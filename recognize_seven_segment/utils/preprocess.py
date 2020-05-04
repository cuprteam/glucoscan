import cv2
import numpy as np


def preprocess(image: np.ndarray, verbose: bool = False) -> np.ndarray:
    """
    Basic preprocessing of the input image.
    """
    rows, cols, channels = image.shape
    if verbose:
        print(f"Original rows: {rows}; Original columns: {cols}")

    if cols > rows:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

    image = cv2.resize(image, (432, 768))
    return image
