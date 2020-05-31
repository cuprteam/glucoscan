import cv2
import numpy as np


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
