from typing import List, Tuple, Dict, Optional

import cv2
import imutils
import numpy as np

from recognize_seven_segment.utils.adaptively_match_digit import adaptively_match_digit_hypotheses
from recognize_seven_segment.utils.describe_arrow_type import describe_arrow
from recognize_seven_segment.utils.perspective_transformation import perspective_transformation
from recognize_seven_segment.utils.generate_digit import generate_digit_freestyle_libre
from recognize_seven_segment.utils.get_leading_rectangles import get_leading_rectangles
from recognize_seven_segment.utils.input_output import load_image, list_image_paths, get_image_name, \
    create_dir_if_it_doesnt_exist
from recognize_seven_segment.utils.leading_rectangles_to_str import leading_rectangles_to_str
from recognize_seven_segment.utils.plot_rectangle import plot_rectangle


def threshold_image(image: np.ndarray):
    image = cv2.pyrMeanShiftFiltering(image, 21, 51)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return threshold


def detect_digit_hypotheses(digit: int, image: np.ndarray, scale_iterations: int = 5,
                            scale_min: float = 0.5, scale_max: float = 1.0,
                            match_threshold: float = 0.6) -> List[Tuple[List[int], float]]:
    """
    :return: list of digit occurences ((x0, y0, x1, y1), confidence)
    """
    image_height, image_width = image.shape

    template = generate_digit_freestyle_libre(digit, image_width // 7)

    return adaptively_match_digit_hypotheses(template, image, scale_iterations, scale_min, scale_max, match_threshold)


def detect_arrow(image: np.array) -> str:
    arrow_types = ["up", "down", "up_right", "down_right", "right"]
    top_arrow_type = ""
    top_arrow_type_match_coeff = -1

    for arrow_type in arrow_types:
        hypothesis = adaptively_match_digit_hypotheses(generate_digit_freestyle_libre(arrow_type),
                                                       image,
                                                       scale_min=0.3,
                                                       scale_max=2.0,
                                                       scale_iterations=15,
                                                       match_threshold=0.5)
        hypothesis.sort(key=lambda rectangle: rectangle[1], reverse=True)
        if len(hypothesis) == 0:
            continue
        top_hypothesis = hypothesis[0]
        coordinates, match_coeff = top_hypothesis
        if match_coeff > top_arrow_type_match_coeff:
            top_arrow_type = arrow_type
            top_arrow_type_match_coeff = match_coeff

    return top_arrow_type


def detect_hypothesis(image: np.ndarray, scale_iterations: int = 10,
                      scale_min: float = 0.5, scale_max: float = 1.0,
                      match_threshold: float = 0.7) -> List[Tuple[List[int], float, int]]:
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


def detect_display_freestyle_libre(image: np.ndarray, factor=2) -> List[np.ndarray]:
    orig = image.copy()
    w, h, _ = image.shape
    image = cv2.resize(image, (int(h // factor), int(w // factor)))
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv_image = hsv_image[:, :, 2]

    e = image
    e = cv2.cvtColor(e, cv2.COLOR_BGR2GRAY)
    # e = cv2.cvtColor(e, cv2.COLOR_BGR2HSV)
    # e = e[:,:,2]
    # return [e]
    kernel = np.ones((5, 5), np.uint8)
    e = cv2.morphologyEx(e, cv2.MORPH_OPEN, kernel)
    e = cv2.bilateralFilter(e, 90, 32, 32)
    e = cv2.GaussianBlur(src=e, ksize=(5, 5), sigmaX=0)
    # e = threshold_image(e)
    e = cv2.Canny(e, 200, 50, 128)

    # return [e]
    contours = cv2.findContours(e,
                                cv2.RETR_TREE,
                                cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)

    boxes = []

    for contour in contours:
        if len(contour) < 3:
            continue

        min_area_rectangle = cv2.minAreaRect(contour)
        (x, y), (w, h), _ = min_area_rectangle

        if w < 100 / factor or h < 100 / factor:
            continue

        if max(w / h, h / w) > 2.:
            continue

        box = cv2.boxPoints(min_area_rectangle)
        box = np.int0(box)

        mask = np.zeros(image.shape[:2], np.uint8)
        cv2.drawContours(mask, [box], -1, 255, -1)

        mean_color = cv2.mean(hsv_image, mask=mask)[0]
        boxes.append((box, mean_color))

    if len(boxes) == 0:
        return []

    boxes.sort(key=lambda box: -box[1])
    lcd_display = perspective_transformation(orig, boxes[0][0] * factor)
    lcd_display = threshold_image(lcd_display)
    e = lcd_display
    return [e]


def detect_digits_freestyle_libre(image: np.ndarray) -> Tuple[Optional[str], Dict]:
    lcd_displays = detect_display_freestyle_libre(image)

    if len(lcd_displays) == 0:
        return None, {"display_detected": False}

    lcd_display = lcd_displays[0]
    rectangles = detect_hypothesis(lcd_display)
    if len(rectangles) == 0:
        return None, {"display_detected": True, "annotated_image": lcd_display}

    rectangles = get_leading_rectangles(rectangles)
    if len(rectangles) == 0:
        return None, {"display_detected": True, "annotated_image": lcd_display}

    annotation = leading_rectangles_to_str(rectangles)

    for rectangle in rectangles:
        plot_rectangle(lcd_display, rectangle)

    # Find arrow window
    rectangles.sort(key=lambda rectangle: rectangle[0][0], reverse=True)
    rightmost_rectangle = rectangles[0]
    coordinates, _, _ = rightmost_rectangle
    x0, y0, x1, y1 = coordinates
    x_right = lcd_display.shape[1]
    arrow_window = lcd_display[y0:y1, x1:x_right]

    arrow_type = detect_arrow(arrow_window)
    arrow_description = describe_arrow[arrow_type]

    annotation = annotation + " " + arrow_description

    return annotation, {"display_detected": True, "annotated_image": lcd_display}


if __name__ == "__main__":
    image_dir = "/tmp/images/"
    output_dir = "/tmp/freestyle_libre/"

    image_paths = list_image_paths(image_dir)

    create_dir_if_it_doesnt_exist(output_dir)

    for image_path in image_paths:
        image_name = get_image_name(image_path)
        image = load_image(image_path)
        image = imutils.resize(image, width=432)
        cols, rows, channels = image.shape
        if cols < rows:
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

        lcd_displays = detect_display_freestyle_libre(image)

        for lcd_display in lcd_displays:
            rectangles = detect_hypothesis(lcd_display)
            rectangles = get_leading_rectangles(rectangles)

            if len(rectangles) == 0:
                continue

            rectangles.sort(key=lambda rectangle: rectangle[0][0], reverse=True)
            rightmost_rectangle = rectangles[0]
            coord, conf, nr = rightmost_rectangle
            x0, y0, x1, y1 = coord

            x_right = lcd_display.shape[1]

            arrow_window = lcd_display[y0:y1, x1:x_right]

            arrow_type = detect_arrow(arrow_window)

            for rectangle in rectangles:
                plot_rectangle(lcd_display, rectangle, show_match_coeff=False)

            annotation = leading_rectangles_to_str(rectangles)

            cv2.imwrite(f"{output_dir}{image_name}_{annotation}_{arrow_type}.jpg", lcd_display)
