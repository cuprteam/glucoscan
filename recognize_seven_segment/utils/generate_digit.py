import os

import cv2
import imutils
import numpy as np
from PIL import Image, ImageDraw, ImageFont

this_file_path = os.path.realpath(__file__)


def generate_digit(digit: int, width: int = 40, threshold=100) -> np.ndarray:
    """
    Returns image of a 7-segment digit as np.array of shape (height, width).
    Color range 0 - 255
    """
    font_path = "/".join(this_file_path.split("/")[:-2]) + "/resources/fonts/Segment7Standard.otf"

    img = Image.new("RGB", (width, (int)(width * 1.35)))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, (int)(width * 1.5))
    draw.text((width // 10, width // 10), str(digit), "white", font)
    img = np.array(img)
    img = img[:, :, 0]
    img = 255 * (1 - 1 * (img > threshold))
    img = img.astype(np.uint8)
    return img


def load_digit_easy_gluko(digit: int) -> np.ndarray:
    relative_path = os.path.join("..", "resources", "fonts", "EasyGlukoFont", str(digit) + ".png")
    image_path = os.path.join(os.path.dirname(this_file_path), relative_path)

    image = cv2.imread(image_path)
    image = image[:, :, 0]
    return image


easy_gluko_digits = [load_digit_easy_gluko(digit) for digit in range(10)]


def generate_digit_easy_gluko(digit: int, width: int = 40) -> np.ndarray:
    return imutils.resize(easy_gluko_digits[digit], width=width)


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    digit = generate_digit_easy_gluko(6)
    print(f"Color range: {np.min(digit)} - {np.max(digit)}")
    print(f"Shape: {digit.shape}")
    plt.imshow(digit, cmap="gray")
    plt.show()
