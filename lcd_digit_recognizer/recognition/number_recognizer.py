import time
from typing import List

import cv2
import imutils
import numpy as np

from lcd_digit_recognizer.recognition.digit_net import DigitNet
from lcd_digit_recognizer.recognition.digit_net2 import DigitNet2
from lcd_digit_recognizer.recognition.physical_line_recognizer import PhysicalLineRecognizer
from lcd_digit_recognizer.recognition.primitives.physical_line import PhysicalLine
from lcd_digit_recognizer.recognition.primitives.recognized_digit import RecognizedDigit
from lcd_digit_recognizer.recognition.utils import unit_vector, merge_clustering
from lcd_digit_recognizer.visualization.drawing import draw_recognized_digits, draw_lines, draw_cocenter_net, \
    draw_aligned_center_buckets, draw_aligned_center_buckets_simple, draw_physical_line_clusters, draw_join_points, \
    draw_digit_hypotheses
from lcd_digit_recognizer.visualization.utils import rotate90, get_color

WORKING_IMAGE_SIZE = 500  # size of largest edge of the processed image (original is resized to this)
MINIMAL_NUMBER_LENGTH = 2  # numbers with lesser digits will be thrown away

LINE_MIN_PIXEL_COUNT = 5
LINE_MAX_PIXEL_COUNT = 50

SHARP_EDGE_DIFF_THRESHOLD = 5  # when larger change is found, sharp edge is present
SHARP_EDGE_COLOR_FACTOR = 0.2  # factor used for color rescaling
MIN_CENTER_ARM_LENGTH = 5  # how many pixels, between center and segment is required at minimum
CENTER_ARM_LENGH_FACTOR = 1.1 / 2  # how long center arm length is based on center cocenter length

"""
# s2 #
s1 # s3
# s7 #
s6 # s4
# s5 #
"""
digit_table = {

    "1111110": 0,
    "1000010": 1,
    "0011000": 1,
    "0110111": 2,
    "0111101": 3,
    "1011001": 4,
    "1101101": 5,
    "1101111": 6,
    "1111000": 7,
    "0111000": 7,
    "1111111": 8,
    "1111101": 9,

}


def recognize_digits(input_img, with_visualization=False):
    start = time.time()

    edged, img = preprocess_image(input_img)
    print(f"Image preprocessing {time.time() - start}")
    output_imgs = []

    if with_visualization:
        output_imgs.append(cv2.cvtColor(edged, cv2.COLOR_GRAY2BGR))


    recognizer = PhysicalLineRecognizer(is_vertical=False)
    for edge_line in edged:
        recognizer.accept(edge_line)

    recognizer2 = PhysicalLineRecognizer(is_vertical=True)
    for edge_line2 in rotate90(edged):
        recognizer2.accept(edge_line2)

    print(f"Line recognition {time.time() - start}")

    all_lines = recognizer.get_physical_lines() + recognizer2.get_physical_lines()
    print(f"Physical line collection {time.time() - start} ")
    filtered_lines = digit_line_filter(all_lines)

    print(f"Line filtering {time.time() - start}")

    if with_visualization:
        net2 = DigitNet2(img, filtered_lines)

        output_img = np.array(img)
        output_imgs.append(output_img)
        draw_physical_line_clusters(output_img, net2.vote_components)

        output_img = np.array(img)
        output_imgs.append(output_img)
        draw_join_points(output_img, net2.vote_components, net2)

        output_img = np.array(img)
        output_imgs.append(output_img)
        draw_digit_hypotheses(output_img, net2.digit_hypotheses, net2)

        output_img = np.array(img)
        output_imgs.append(output_img)
        draw_lines(output_img, filtered_lines)

    net = get_digit_net(filtered_lines)
    # net.get_aligned_center_buckets()
    # print(f"Digit net creation {time.time() - start}")

    if with_visualization:
        output_img = np.array(img)
        output_imgs.append(output_img)
        draw_cocenter_net(output_img, net)

        output_img = np.array(img)
        output_imgs.append(output_img)
        draw_aligned_center_buckets(output_img, net)

        output_img = np.array(img)
        output_imgs.append(output_img)
        draw_aligned_center_buckets_simple(output_img, net)

    digit_hyps = get_number_hypotheses(img, net)
    print(f"Number hypothesis {time.time() - start}")

    if with_visualization:
        output_img = np.array(img)
        output_imgs.append(output_img)
        draw_recognized_digits(output_img, digit_hyps)

    return digit_hyps, output_imgs


def segment_clustering(lines: List[PhysicalLine]):
    return merge_clustering(lines, metric=lambda l: l.absolute_angle, range_threshold=20)


def preprocess_image(img):
    if img.shape[0] < img.shape[1]:
        img = rotate90(img)

    img = imutils.resize(img, width=500)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred2 = cv2.bilateralFilter(gray, 40, 16, 16)
    edged = cv2.Canny(blurred2, 50, 100, 128)
    return edged, img,


def get_number_hypotheses(original_img, net):
    img = np.array(original_img)
    img = np.sum(img, axis=2) * SHARP_EDGE_COLOR_FACTOR
    result = []
    for center_bucket in net.get_aligned_center_buckets():
        current_number = None

        filtered_bucket = filter_surrounding_artifacts(center_bucket)

        for b in filtered_bucket:
            center, cocenter = b[0:2]
            digit_state = get_digit_state(img, center, cocenter)
            digit_value = recognize_digit(digit_state)
            # print(f"{center}->{cocenter}")
            # print(digit_state)
            if digit_value is None:
                continue

            digit = RecognizedDigit(digit_value, center, cocenter)
            digit.bucket = center_bucket

            if current_number is None:
                current_number = digit
            else:
                current_number.join_to(digit)
                current_number = digit

        if current_number:
            current_number = current_number.first
            if current_number.digit_count >= MINIMAL_NUMBER_LENGTH:
                result.append(current_number)

            # print(center_bucket)

    return result


def filter_surrounding_artifacts(center_bucket):
    if (len(center_bucket) < 3):
        return center_bucket

    d_inside = center_bucket[1][0].distance_to(center_bucket[2][0])
    d_start = center_bucket[0][0].distance_to(center_bucket[1][0])
    d_end = center_bucket[-1][0].distance_to(center_bucket[-2][0])

    if d_start * 1.2 < d_inside:
        center_bucket = center_bucket[1:]

    # if ratio_error(d_inside, d_end) > 0.1:
    #    center_bucket = center_bucket[:-1]

    return center_bucket


def get_digit_net(lines):
    net = DigitNet()
    for line in lines:
        n_end1, n_end2 = line.normal_points
        net.add_hypothesis(n_end1[0], n_end1[1], line)
        net.add_hypothesis(n_end2[0], n_end2[1], line)

    return net


def recognize_digit(state):
    if not state:
        return None

    state_repr = "".join('1' if s else '0' for s in state)

    return digit_table.get(state_repr, None)


def get_digit_state(img, center, cocenter):
    state1 = get_center_state(img, center, cocenter)
    state2 = get_center_state(img, cocenter, center)

    if state1 is None or state2 is None:
        return None

    """
    # s2 #
    s1 # s3
    # s7 #
    s6 # s4
    # s5 #
    """

    s7a, s1, s2, s3 = state1
    s7b, s4, s5, s6 = state2

    if s7a != s7b:
        return None

    return [s1, s2, s3, s4, s5, s6, s7a]


def digit_line_filter(lines):
    result = []
    for line in lines:
        if line.length < LINE_MIN_PIXEL_COUNT or line.length > LINE_MAX_PIXEL_COUNT:
            continue

        if line.average_width * 1.5 > line.length:
            continue

        if line.average_width * 5 < line.length:
            continue

        result.append(line)

    return result


def get_direction(p1, p2):
    direction = np.array([p2.x - p1.x, p2.y - p1.y])
    return unit_vector(direction)


def get_directions(center, cocenter):
    direction = get_direction(center, cocenter)
    for i in range(4):
        yield direction
        direction = rotate_vector90(direction)


def rotate_vector90(vector):
    return np.array([vector[1], -vector[0]])


def has_sharp_edge(img, start, direction, length):
    last_color = None
    start = np.array([start.x, start.y])
    # readings = []

    try:
        for i in range(0, int(length), 1):
            point = start + direction * i
            p = [int(point[0]), int(point[1])]
            color = get_color(img, p)
            # readings.append((p, color))
            if color is None:
                return None

            if last_color is not None:
                diff = abs(color - last_color)
                if diff > SHARP_EDGE_DIFF_THRESHOLD:
                    if i < MIN_CENTER_ARM_LENGTH:
                        return None

                    return True

            last_color = color

        return False
    finally:
        # print(f"dir: {direction} {readings}")
        pass


def get_center_state(img, center, cocenter):
    arm_length = center.distance_to(cocenter) * CENTER_ARM_LENGH_FACTOR

    states = []
    for direction in get_directions(center, cocenter):
        has_active_segment = has_sharp_edge(img, center, direction, arm_length)
        state = True if has_active_segment else False
        states.append(state)

    return states
