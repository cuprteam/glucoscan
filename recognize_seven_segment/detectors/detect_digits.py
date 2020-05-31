from typing import List, Tuple, Optional, Dict

import cv2
import numpy as np

from recognize_seven_segment.detectors.detect_display import detect_display_v2
from recognize_seven_segment.utils.adaptively_match_digit import adaptively_match_digit_hypotheses
from recognize_seven_segment.utils.generate_digit import generate_digit_easy_gluko
from recognize_seven_segment.utils.get_leading_rectangles import get_leading_rectangles
from recognize_seven_segment.utils.input_output import load_image, list_image_paths, get_image_name, \
    create_dir_if_it_doesnt_exist
from recognize_seven_segment.utils.leading_rectangles_to_str import leading_rectangles_to_str
from recognize_seven_segment.utils.plot_rectangle import plot_rectangle
from recognize_seven_segment.utils.preprocess import preprocess
from recognize_seven_segment.utils.threshold import threshold_colored


def detect_digit_hypotheses(digit: int, image: np.ndarray, scale_iterations: int = 10,
                            scale_min: float = 0.5, scale_max: float = 1.0,
                            match_threshold: float = 0.6) -> List[Tuple[List[int], float]]:
    """
    :return: list of digit occurences ((x0, y0, x1, y1), confidence)
    """
    image_height, image_width = image.shape

    template = generate_digit_easy_gluko(digit, image_width // 7)

    return adaptively_match_digit_hypotheses(template, image, scale_iterations, scale_min, scale_max, match_threshold)


def detect_hypothesis(image: np.ndarray, scale_iterations: int = 10,
                      scale_min: float = 0.5, scale_max: float = 1.0,
                      match_threshold: float = 0.8) -> List[Tuple[List[int], float, int]]:
    # TODO: default match threshold could be 0.7 or even maybe 0.5 and it still wouldn't hurt accuracy
    # but the performance will go down
    """
    :return: list of digit occurences ((x0, y0, x1, y1), confidence)
    """
    rectangles = []
    for digit in range(10):
        digit_rectangles = detect_digit_hypotheses(digit, image, scale_iterations,
                                                   scale_min, scale_max, match_threshold)
        digit_rectangles = [tuple(list(rectangle) + [digit]) for rectangle in digit_rectangles]
        rectangles.extend(digit_rectangles)

    return rectangles


def detect_digits(image: np.ndarray) -> Tuple[Optional[str], Dict]:
    image = preprocess(image)
    lcd_displays = detect_display_v2(image)

    if len(lcd_displays) == 0:
        return None, {"display_detected": False}

    display_annotations = []
    display_rectangles = []

    for lcd_display in lcd_displays:
        lcd_display = threshold_colored(lcd_display)
        rectangles = detect_hypothesis(lcd_display)
        if len(rectangles) < 2:
            annotation = "no_rectangles_found"
        else:
            rectangles = get_leading_rectangles(rectangles)

            if len(rectangles) < 2:
                annotation = "no_leading_rectangles_found"
            else:
                annotation = leading_rectangles_to_str(rectangles)

        display_rectangles.append(rectangles)
        display_annotations.append(annotation)

    number_annotations = [annotation for annotation in display_annotations
                          if annotation != "no_rectangles_found" and
                          annotation != "no_leading_rectangles_found"]

    if len(number_annotations) == 0:
        return None, {"display_detected": True}
    else:
        top_annotation = max(set(number_annotations), key=number_annotations.count)
        # TODO: here is a place for some more clever heuristic over the count
        # of the top annotation and other annotations, perhaps a place to use
        # confidence of the rectangles ...
        top_annotation_index = display_annotations.index(top_annotation)
        top_lcd_display = lcd_displays[top_annotation_index]
        top_rectangles = display_rectangles[top_annotation_index]
        for rectangle in top_rectangles:
            plot_rectangle(top_lcd_display, rectangle)

        return top_annotation, {"display_detected": True, "annotated_image": top_lcd_display}


if __name__ == "__main__":
    image_dir = "/tmp/images/"
    out_dir = "/tmp/annotations/"

    create_dir_if_it_doesnt_exist(out_dir)
    image_paths = list_image_paths(image_dir)

    for image_path in image_paths[:50]:
        image = load_image(image_path)
        image_name = get_image_name(image_path)

        annotation, metadata = detect_digits(image)

        if annotation is not None:
            annotated_display = metadata["annotated_image"]
            output_path = f"{out_dir}{image_name}.jpg"
            cv2.imwrite(output_path, annotated_display)
