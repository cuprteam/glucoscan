import os
from time import sleep
from typing import List

import cv2
import imutils
import numpy as np
from matplotlib.pyplot import imshow

from recognize_seven_segment.experiments.detect_digits_freestyle_libre import detect_display_freestyle_libre
from recognize_seven_segment.utils.four_point_transform import four_point_transform

INPUT_PATH = "C:/Users/MiroslavVodolan/VirtualBox VMs/Shared/display_detection_dataset"
OUTPUT_PATH = "C:/Users/MiroslavVodolan/VirtualBox VMs/Shared/display_detection_output"

os.makedirs(OUTPUT_PATH, exist_ok=True)


def white_balance_loops(img):
    result = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    avg_a = np.average(result[:, :, 1])
    avg_b = np.average(result[:, :, 2])
    for x in range(result.shape[0]):
        for y in range(result.shape[1]):
            l, a, b = result[x, y, :]
            # fix for CV correction
            l *= 100 / 255.0
            result[x, y, 1] = a - ((avg_a - 128) * (l / 100.0) * 1.1)
            result[x, y, 2] = b - ((avg_b - 128) * (l / 100.0) * 1.1)
    result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
    return result


scaling_factor = 4
larger_edge = 768

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    image = frame
    w, h, chans = image.shape
    if w > h:
        nw = larger_edge
        nh = h / w * nw
    else:
        nh = larger_edge
        nw = w / h * nh

    resized = cv2.resize(image, (int(nh), int(nw)))
    # resized = white_balance_loops(resized)
    # displays = [resized]
    displays = detect_display_freestyle_libre(resized, factor=scaling_factor)

    if displays:
        output = displays[0]
    else:
        output = image

    cv2.imwrite("test.jpg", output)
    print("Saved")

    # sleep(1.0)