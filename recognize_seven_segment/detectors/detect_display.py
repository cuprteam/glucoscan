from typing import List

import cv2
import imutils
import numpy as np

from recognize_seven_segment.utils.four_point_transform import four_point_transform
from recognize_seven_segment.utils.input_output import load_image, list_image_paths, get_image_name, \
    create_dir_if_it_doesnt_exist
from recognize_seven_segment.utils.preprocess import preprocess

def detect_display_v2(image: np.ndarray,
                      max_edge_ratio: float = 1.5,
                      min_display_dimension: int = 100,
                      max_orig_to_rotated_ratio: float = 1.3) -> List[np.ndarray]:
    orig = image.copy()
    image = cv2.GaussianBlur(src=image, ksize=(5, 5), sigmaX=0)
    image = cv2.Canny(image, threshold1=0, threshold2=50)
    contours = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)

    lcd_displays = []
    for contour in contours:
        if len(contour) < 3:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        if h < min_display_dimension or w < min_display_dimension or (w / h) > max_edge_ratio or (
                h / w) > max_edge_ratio:
            continue

        ((mx, my), (mw, mh), rot) = cv2.minAreaRect(contour)

        if mw / w < max_orig_to_rotated_ratio and w / mw < max_orig_to_rotated_ratio \
                and h / mh < max_orig_to_rotated_ratio and mh / h < max_orig_to_rotated_ratio:
            box = cv2.boxPoints(((mx, my), (mw, mh), rot))
        else:
            box = cv2.boxPoints(((x, y), (w, h), 0))

        box = np.int0(box)
        lcd_display = four_point_transform(orig, box)
        lcd_displays.append(lcd_display)

    return lcd_displays

if __name__ == "__main__":
    # image_dir = "/home/josef/Downloads/Gluko/"
    # image_dir = "/home/josef/Downloads/cukrovka_trainset_0_1920_and_3840/"
    # image_dir = "./recognize_seven_segment/resources/easy_gluko/"
    image_dir = "/home/josef/Downloads/OneDrive_1_11-19-2019/"

    out_dir = "/tmp/displays/"

    create_dir_if_it_doesnt_exist(out_dir)
    image_paths = list_image_paths(image_dir)

    for image_path in image_paths[:50]:
        image = load_image(image_path)
        image_name = get_image_name(image_path)
        image = preprocess(image)

        lcd_displays = detect_display_v2(image)
        for lcd_display_index, lcd_display in enumerate(lcd_displays):
            output_path = f"{out_dir}{image_name}_{lcd_display_index}.jpg"
            cv2.imwrite(output_path, lcd_display)
