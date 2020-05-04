from typing import List, Tuple, Optional, Dict

import cv2
import numpy as np
import imutils

from recognize_seven_segment.detectors.detect_display import detect_display_v2
from recognize_seven_segment.utils.generate_digit import generate_digit_easy_gluko
from recognize_seven_segment.utils.preprocess import preprocess
from recognize_seven_segment.utils.threshold import threshold_colored
from recognize_seven_segment.utils.input_output import load_image, list_image_paths, get_image_name, \
    create_dir_if_it_doesnt_exist


def detect_digit_hypotheses(digit: int, image: np.ndarray, scale_iterations: int = 10,
                            scale_min: float = 0.5, scale_max: float = 1.0,
                            match_threshold: float = 0.6) -> List[Tuple[List[int], float]]:
    """
    :return: list of digit occurences ((x0, y0, x1, y1), confidence)
    """
    image_height, image_width = image.shape

    template = generate_digit_easy_gluko(digit, image_width // 7)
    template_height, template_width = template.shape

    rectangles = []

    for scale in np.linspace(scale_min, scale_max, scale_iterations)[::-1]:
        resized = imutils.resize(image, width=int(image_width * scale))
        resized_height, resized_width = resized.shape
        scale_inv = image_width / float(resized_width)

        if resized_width < template_width or resized_height < template_height:
            break

        result = cv2.matchTemplate(resized, template, cv2.TM_CCOEFF_NORMED)
        start_coordinates = np.where(result > match_threshold)
        values = result[start_coordinates]
        for y, x, confidence in zip(*start_coordinates, values):
            rectangle_coordinates = get_rectangle_coordinates(x, y, scale_inv, template_width, template_height)
            rectangle = (rectangle_coordinates, confidence)
            rectangles.append(rectangle)

    return rectangles


def get_rectangle_coordinates(x: int, y: int, scale_inv: int, template_width: int, template_height: int) -> List[int]:
    x0 = (int)(x * scale_inv)
    y0 = (int)(y * scale_inv)
    x1 = (int)((x + template_width) * scale_inv)
    y1 = (int)((y + template_height) * scale_inv)

    return [x0, y0, x1, y1]


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


def plot_rectangle(image: np.ndarray, rectangle, show_match_coeff: bool = True):
    (x0, y0, x1, y1), match_coeff, digit = rectangle
    cv2.rectangle(image, (x0, y0), (x1, y1), (0, 0, 0), 1)
    cv2.rectangle(image, (x0, y0), (x0 + 20, y0 + 24), (50, 50, 50), -1)
    cv2.putText(image, str(digit), (x0 + 3, y0 + 18),
                cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 1)
    if show_match_coeff:
        cv2.rectangle(image, (x0, y1 - 24), (x1, y1), (100, 100, 100), -1)
        cv2.putText(image, f"{match_coeff:.2f}", (x0 + 3, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 1)


def rectangles_could_be_adjacent_digits(rectangle_a: Tuple[List[int], float, int],
                                        rectangle_b: Tuple[List[int], float, int],
                                        max_allowed_size_ratio: float = 1.2,
                                        min_allowed_horizontal_distance_multiple: float = 0.8,
                                        max_allowed_horizontal_distance_multiple: float = 0.3,
                                        max_allowed_vertical_distance_multiple: float = 0.2) -> bool:
    (x0_a, y0_a, x1_a, y1_a), match_coeff_a, digit_a = rectangle_a
    (x0_b, y0_b, x1_b, y1_b), match_coeff_b, digit_b = rectangle_b
    width_a, width_b = x1_a - x0_a, x1_b - x0_b
    height_a, height_b = y1_a - y0_a, y1_b - y0_b

    result = width_a / width_b < max_allowed_size_ratio and \
             width_b / width_a < max_allowed_size_ratio and \
             height_a / height_b < max_allowed_size_ratio and \
             height_b / height_a < max_allowed_size_ratio and \
             abs(x0_a - x0_b) > (width_a + width_b) / 2 * min_allowed_horizontal_distance_multiple and \
             min(abs(x1_a - x0_b), abs(x1_b - x0_a)) < (
                     width_a + width_b) / 2 * max_allowed_horizontal_distance_multiple and \
             abs(y0_a - y0_b) < (height_a + height_b) / 2 * max_allowed_vertical_distance_multiple

    return result


def get_leading_rectangles(rectangles: List[Tuple[List[int], float, int]]) \
        -> List[Tuple[List[int], float, int]]:
    best_pair_coeff = -1
    best_pair = []
    for rectangle_left in rectangles:
        (x0_left, y0_left, x1_left, y1_left), match_coeff_left, digit_left = rectangle_left
        for rectangle_right in rectangles:
            (x0_right, y0_right, x1_right, y1_right), match_coeff_right, digit_right = rectangle_right

            if rectangles_could_be_adjacent_digits(rectangle_left, rectangle_right) \
                    and x0_left < x0_right:
                cumulative_coeff = match_coeff_left + match_coeff_right
                if cumulative_coeff > best_pair_coeff:
                    best_pair_coeff = cumulative_coeff
                    best_pair = [rectangle_left, rectangle_right]

    if len(best_pair) == 0:
        return best_pair

    best_rectangle_left, best_rectangle_right = best_pair
    (x0_left, y0_left, x1_left, y1_left), match_coeff_left, digit_left = best_rectangle_left
    (x0_right, y0_right, x1_right, y1_right), match_coeff_right, digit_right = best_rectangle_right

    best_coeff_leftmost = -1
    best_coeff_rightmost = -1
    best_rectangle_leftmost = []
    best_rectangle_rightmost = []
    for rectangle in rectangles:
        (x0, y0, x1, y1), match_coeff, digit = rectangle
        if x0 < x0_left and rectangles_could_be_adjacent_digits(rectangle, best_rectangle_left):
            if match_coeff > best_coeff_leftmost:
                best_coeff_leftmost = match_coeff
                best_rectangle_leftmost = [rectangle]
        if x1 > x1_right and rectangles_could_be_adjacent_digits(rectangle, best_rectangle_right):
            if match_coeff > best_coeff_rightmost:
                best_coeff_rightmost = match_coeff
                best_rectangle_rightmost = [rectangle]

    # TODO: here is a space for some prior. It is for example far less likely to get 2
    # as the leftmost digit, but if it matches really well, it could happen.

    use_rightmost = best_coeff_leftmost < best_coeff_rightmost
    if use_rightmost:
        return best_pair + best_rectangle_rightmost
    else:
        return best_rectangle_leftmost + best_pair


def leading_rectangles_to_str(rectangles: List[Tuple[List[int], float, int]]) -> str:
    rectangles.sort(key=lambda x: x[0][0])
    digits = [str(r[-1]) for r in rectangles]
    str_representation = "".join(digits[:-1]) + "." + digits[-1]
    return str_representation


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
    # image_dir = "/home/josef/Downloads/Gluko/"
    # image_dir = "/home/josef/Downloads/cukrovka_trainset_0_1920_and_3840/"
    # image_dir = "./recognize_seven_segment/resources/easy_gluko/"
    # image_dir = "/home/josef/Downloads/OneDrive_1_11-19-2019/"
    image_dir = "/home/josef/Downloads/flash/"

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
