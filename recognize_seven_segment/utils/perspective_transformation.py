import cv2
import numpy as np

from recognize_seven_segment.utils.input_output import load_image


def _rearrange_corners(rectangle_corners: np.ndarray) -> np.ndarray:
    xy_sum = rectangle_corners.sum(axis=1)
    xy_difference = np.diff(rectangle_corners, axis=1)

    top_left = rectangle_corners[np.argmin(xy_sum)]
    top_right = rectangle_corners[np.argmin(xy_difference)]
    bottom_left = rectangle_corners[np.argmax(xy_difference)]
    bottom_right = rectangle_corners[np.argmax(xy_sum)]

    return np.array([top_left, top_right, bottom_right, bottom_left], dtype="float32")


def perspective_transformation(image: np.ndarray, rectangle_corners: np.ndarray) -> np.ndarray:
    """
    :param image: np.array ( rows, cols, channels ), integer values 0 - 255
    :param rectangle_corners: np.array of 4 pts, inteter, e.g.
        [[ 36 335]
         [ 29 541]
         [251 546]
         [258 341]]
    :return:
    """
    rearranged_corners = _rearrange_corners(rectangle_corners)
    top_left, top_right, bottom_right, bottom_left = rearranged_corners

    width_top = np.linalg.norm(bottom_right - bottom_left)
    width_bottom = np.linalg.norm(top_right - top_left)

    height_right = np.linalg.norm(top_right - bottom_right)
    height_left = np.linalg.norm(top_left - bottom_left)

    width = int(max(width_top, width_bottom))
    height = int(max(height_right, height_left))

    dst = np.array([[0, 0],
                    [width, 0],
                    [width, height],
                    [0, height]], dtype="float32")

    M = cv2.getPerspectiveTransform(src=rearranged_corners, dst=dst)
    transformed = cv2.warpPerspective(src=image, M=M, dsize=(width, height))

    return transformed


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    image_path = "/home/josef/Downloads/test_image.jpeg"
    image = load_image(image_path)
    points = np.array([[300, 30], [200, 280], [470, 80], [350, 350]])
    transformed_image = perspective_transformation(image, points)
    plt.imshow(transformed_image)
    plt.show()
