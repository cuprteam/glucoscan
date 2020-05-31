# TODO: Remove or make more general.
import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# This is how we code segments by numbers 0 to 6
#
#      00000
#     1     2
#     1     2
#      33333
#     4     5
#     4     5
#      66666
#

segment_to_digit = {
    "0010010": 1,
    "1011101": 2,
    "1011011": 3,
    "0111010": 4,
    "1101011": 5,
    "1101111": 6,
    "1110010": 7,
    "1010010": 7,
    "1111111": 8,
    "1111011": 9,
    "1110111": 0
}


def generate_mask(row, col, orientation, shape=None):
    if shape is None:
        shape = (70, 40)
    mask = np.zeros(shape)

    if orientation == "horizontal":
        ellipse_shape = (6, 4)

    if orientation == "vertical":
        ellipse_shape = (4, 6)

    mask = cv2.ellipse(mask, (col, row), ellipse_shape, 0, 0, 360, (255, 255, 255), 10)
    mask = cv2.blur(mask, (10, 10))
    return mask / 255


mask_0 = generate_mask(5, 20, "horizontal")
mask_1 = generate_mask(20, 5, "vertical")
mask_2 = generate_mask(20, 35, "vertical")
mask_3 = generate_mask(34, 20, "horizontal")
mask_4 = generate_mask(52, 5, "vertical")
mask_5 = generate_mask(52, 35, "vertical")
mask_6 = generate_mask(65, 20, "horizontal")

masks = [mask_0, mask_1, mask_2, mask_3, mask_4, mask_5, mask_6]


def recognize_single_digit(image: np.ndarray, threshold: float = 100) -> int:
    try:
        gray = image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    except:
        pass
    resized = cv2.resize(gray, (40, 70))
    resized = resized < np.mean(resized)
    scores = [np.sum(mask * resized) for mask in masks]
    scores = [score > threshold for score in scores]
    scores = ["1" if score else "0" for score in scores]
    return segment_to_digit.get("".join(scores))


if __name__ == "__main__":
    image_path = "/tmp/images/"
    image = Image.open(image_path)
    image = np.array(image)
    digit = recognize_single_digit(image, 100)
    print(f"Recognized digit {digit}")

    for i in [0, 1, 2, 3, 4, 5, 6]:
        plt.imshow(masks[i])
        plt.title(f"Mask {i}")
        plt.show()
