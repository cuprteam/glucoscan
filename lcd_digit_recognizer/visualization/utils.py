import cv2
import numpy as np

from lcd_digit_recognizer.recognition.primitives.digit_center import DigitCenter


def join_images(imgs):
    return np.concatenate(imgs, axis=1)


def write_text(img, position, text, size, font_color):
    font = cv2.FONT_HERSHEY_SIMPLEX
    line_type = 2

    cv2.putText(img, text,
                recoordinate(position),
                font,
                size,
                font_color,
                line_type)


def get_color(img, point):
    x, y = point

    if x < 0 or y < 0:
        return None

    if x >= img.shape[0]:
        return None

    if y >= img.shape[1]:
        return None

    return img[x, y]


def highlight_point(output_img, point, color, size=4):
    p = point
    if isinstance(point, DigitCenter):
        p = [point.x, point.y]

    cv2.line(output_img, recoordinate(p), recoordinate(p), thickness=size,
             color=color)


def rotate90(img):
    return np.swapaxes(img, 0, 1)


def brg2rgb(brg):
    return (brg[1], brg[2], brg[0])


def recoordinate(p):
    return (int(max(0, min(p[1], 10000))), int(max(0, min(p[0], 10000))))
