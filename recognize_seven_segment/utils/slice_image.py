# TODO: Remove - this is specific for the EasyGluko baseline
from typing import Dict

import numpy as np


def slice_image(image: np.ndarray, width: int = 40, height: int = 70) -> Dict[str, np.ndarray]:
    """
    Specific function for EasyGluko glucometer that given image of display returns
    dictionary of 3 slices where digits should be.
    """
    result = {}

    for (row, col) in [[15, 15], [15, 50], [15, 98]]:
        desc = f"{row}_{col}_{width}_{height}"
        slice = image[row:(row + height), col:(col + width)]
        result[desc] = slice

    return result
