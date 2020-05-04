import colorsys
from typing import List

import cv2
import numpy as np

from lcd_digit_recognizer.recognition.digit_net2 import DigitNet2
from lcd_digit_recognizer.recognition.primitives.digit_hypothesis import DigitHypothesis
from lcd_digit_recognizer.recognition.primitives.physical_line import PhysicalLine
from lcd_digit_recognizer.visualization.utils import highlight_point, write_text, recoordinate


def draw_recognized_digits(output_img, digit_hyps):
    if not digit_hyps:
        return

    segment_size = 1.0 / (len(digit_hyps) + 1)
    segment_inc = segment_size + 0.5
    h = 0
    for hyp in digit_hyps:
        c = colorsys.hls_to_rgb(h % 1.0, 0.5, 1.0)
        color = (c[0] * 255, c[1] * 255, c[2] * 255)

        current_digit = hyp
        while current_digit is not None:
            center = current_digit._center
            cocenter = current_digit._cocenter

            highlight_point(output_img, center, color=color, size=10)
            highlight_point(output_img, cocenter, color=color, size=5)
            # cv2.line(output_img, recoordinate(center.as_point()), recoordinate(cocenter.as_point()), thickness=3,
            #         color=color)

            write_text(output_img, [center.x, center.y + 10], str(current_digit.value), 0.8, color)

            current_digit = current_digit._next_digit

        for b in hyp.bucket:
            center, cocenter = b[0:2]
            highlight_point(output_img, center, color, size=3)
            cv2.line(output_img, recoordinate(center.as_point()), recoordinate(cocenter.as_point()), thickness=1,
                     color=color)

        h += segment_inc


def draw_aligned_center_buckets(output_img, net):
    buckets = net.get_aligned_center_buckets()

    segment_size = 1.0 / (len(buckets) + 1)
    segment_inc = segment_size + 0.5
    h = 0
    for bucket in buckets:
        c = colorsys.hls_to_rgb(h % 1.0, 0.5, 1.0)
        color = (c[0] * 255, c[1] * 255, c[2] * 255)
        for b in bucket:
            center, cocenter = b[0:2]
            # print(b[2])

            if len(b) > 4:
                cv2.line(output_img, recoordinate(center.as_point()), recoordinate(b[4]), thickness=1, color=color)
                highlight_point(output_img, center.as_point(), color)

            cv2.line(output_img, recoordinate(center.as_point()), recoordinate(cocenter.as_point()), thickness=1,
                     color=color)

        h += segment_inc


def draw_aligned_center_buckets_simple(output_img, net):
    buckets = net.get_aligned_center_buckets()

    segment_size = 1.0 / (len(buckets) + 1)
    segment_inc = segment_size + 0.5
    h = 0
    for bucket in buckets:
        c = colorsys.hls_to_rgb(h % 1.0, 0.5, 1.0)
        color = (c[0] * 255, c[1] * 255, c[2] * 255)
        for b in bucket:
            center, cocenter = b[0:2]

            cv2.line(output_img, recoordinate(center.as_point()), recoordinate(cocenter.as_point()), thickness=1,
                     color=color)

        h += segment_inc


def draw_lines(img, lines):
    color = (255, 64, 64)
    for line in lines:
        # print(f"angle: {line.absolute_angle}")
        # print(f"dir: {line.direction}")
        normal_end1, normal_end2 = line.normal_points
        # print(f"center: {line.center}")
        # print(f"end: {normal_end1}")
        thickness = 2
        cv2.line(img, recoordinate(line.center), recoordinate(normal_end1), color=color, thickness=thickness)
        cv2.line(img, recoordinate(line.center), recoordinate(normal_end2), color=color, thickness=thickness)
        for x, y in line.points:
            img[x, y] = color


def draw_cocenter_net(img, net):
    for center in net.centers:
        if not center.cocenters:
            continue

        cv2.line(img, recoordinate([center.x, center.y]), recoordinate([center.x, center.y]), thickness=4,
                 color=(0, 0, 255))

        angle = center.average_segment_aligned_angle
        rad = np.deg2rad(angle)
        dir = np.array([np.cos(rad), np.sin(rad)])
        p = np.array(center.as_point()) + dir * 10
        # cv2.line(img, recoordinate(center.as_point()), recoordinate(p), thickness=2, color=(0, 255, 0))

        for cocenter in center.cocenters:
            cv2.line(img, recoordinate([center.x, center.y]), recoordinate([cocenter.x, cocenter.y]), thickness=1,
                     color=(0, 0, 255))

            angle = center.absolute_angle_to(cocenter)
            rad = np.deg2rad(angle)
            dir2 = np.array([np.cos(rad), np.sin(rad)])
            p2 = np.array(center.as_point()) + dir2 * 10
            # cv2.line(img, recoordinate(center.as_point()), recoordinate(p2), thickness=2, color=(255, 0, 0))


def draw_physical_line_clusters(output_img, lines: List[List[PhysicalLine]]):
    lines = list(filter(lambda c: len(c) > 1, lines))
    segment_size = 1.0 / (len(lines) + 1)
    segment_inc = segment_size + 0.5
    h = 0
    for line_cluster in lines:
        c = colorsys.hls_to_rgb(h % 1.0, 0.5, 1.0)
        color = (c[0] * 255, c[1] * 255, c[2] * 255)
        for line in line_cluster:
            for point in line.points:
                output_img[point[0], point[1]] = color

            # points = list(line.points)
            # cv2.line(output_img, recoordinate(points[0]), recoordinate(points[-1]), thickness=1,
            #         color=color)

        h += segment_inc


def draw_join_points(output_img, lines: List[List[PhysicalLine]], net: DigitNet2):
    segment_size = 1.0 / (len(lines) + 1)
    segment_inc = segment_size + 0.5
    h = 0
    for line_cluster in lines:
        c = colorsys.hls_to_rgb(h % 1.0, 0.5, 1.0)
        color = (c[0] * 255, c[1] * 255, c[2] * 255)

        seed = line_cluster[0]
        processed = set()
        worklist = [seed]
        while worklist:
            line = worklist.pop(0)
            if line in processed:
                continue

            processed.add(line)
            print("--------------")
            print(line)
            for joint in line.joints:
                print(joint)
                neighbour = joint.target_line
                p1, join_point, p2 = net.get_joint_points(line, neighbour)
                cv2.line(output_img, recoordinate(p1), recoordinate(join_point), thickness=1,
                         color=(0, 0, 255))
                cv2.line(output_img, recoordinate(join_point), recoordinate(p2), thickness=1,
                         color=(0, 0, 255))

                highlight_point(output_img, join_point, color)


                worklist.append(neighbour)
        h += segment_inc


def draw_digit_hypotheses(output_img, digits: List[DigitHypothesis], net: DigitNet2):
    segment_size = 1.0 / (len(digits) + 1)
    segment_inc = segment_size + 0.5
    h = 0
    for digit in digits:
        c = colorsys.hls_to_rgb(h % 1.0, 0.5, 1.0)
        color = (c[0] * 255, c[1] * 255, c[2] * 255)

        for vertex in digit.vertexes:
            highlight_point(output_img, vertex, color)

        h += segment_inc

