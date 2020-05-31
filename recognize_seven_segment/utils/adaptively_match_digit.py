from typing import List, Tuple

import cv2
import imutils
import numpy as np


def adaptively_match_digit_hypotheses(template: np.ndarray, image: np.ndarray, scale_iterations: int = 10,
                                      scale_min: float = 0.5, scale_max: float = 1.0,
                                      match_threshold: float = 0.6) -> List[Tuple[List[int], float]]:
    """
    :return: list of digit occurences ((x0, y0, x1, y1), confidence)
    """
    image_height, image_width = image.shape

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
