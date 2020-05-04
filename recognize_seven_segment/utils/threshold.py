import numpy as np
import cv2


def threshold_gray(image):
    thresh = cv2.adaptiveThreshold(image, 200, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 41, 4)
    return thresh


def threshold_colored(image: np.ndarray) -> np.ndarray:
    """
    :param image: Image of shape (height, width, 3)
    :return: Image of shape (height, width)
    """
    image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    image = image[:, :, 1]
    image = 255 - image
    image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 101, 10)
    return image
