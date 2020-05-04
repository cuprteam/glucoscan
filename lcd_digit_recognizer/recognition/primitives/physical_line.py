import math
import sys
from typing import List
import numpy as np

from lcd_digit_recognizer.recognition.utils import angle_between, unit_vector, absolute_angle


class PhysicalLine(object):
    def __init__(self, line_start, initial_index, width, is_vertical):
        self._stall_time = 0
        self._line_start = line_start
        self._last_index = initial_index
        self._last_width = width
        self._is_updated = False
        self._width_sum = 0
        self._point_indexes: List[int] = []
        self._absolute_angle = None
        self._direction = None
        self.is_vertical = is_vertical
        self.joints: List['Joint'] = []

        self.add(initial_index, width)

    @property
    def line_start(self):
        return self._line_start

    @property
    def length(self):
        return len(self._point_indexes)

    @property
    def metric_length(self):
        ps = list(self.significant_points)
        s = ps[0]
        e = ps[-1]
        return np.sqrt((s[0] - e[0]) ** 2 + (s[1] - e[1]) ** 2)

    @property
    def average_width(self):
        return self._width_sum / len(self._point_indexes)

    @property
    def current_stall_time(self):
        return self._stall_time

    @property
    def is_updated(self):
        return self._is_updated

    @property
    def points(self):
        x = self._line_start
        for y in self._point_indexes:
            yield self._handle_vertical_flipping(x, y)

            x += 1

    @property
    def absolute_angle(self):
        if self._absolute_angle is None:
            angles = []
            point_list = []
            angle_segment = max(10, self.length // 10)

            for point in self.points:
                point_list.append(point)
                if len(point_list) > angle_segment:
                    angle, _ = self._calculate_absolute_angle(point_list[0], point_list[-1])
                    angles.append(angle)
                    point_list = []

            if len(point_list) > 1:
                angle, _ = self._calculate_absolute_angle(point_list[0], point_list[-1])
                angles.append(angle)

            self._absolute_angle = np.mean(angles)

        return self._absolute_angle

    @property
    def direction(self):
        if self._direction is None:
            directions = []
            point_list = []
            angle_segment = max(10, self.length // 10)

            for point in self.points:
                point_list.append(point)
                if len(point_list) > angle_segment:
                    _, direction = self._calculate_absolute_angle(point_list[0], point_list[-1])
                    directions.append(direction)
                    point_list = []

            if len(point_list) > 1:
                _, direction = self._calculate_absolute_angle(point_list[0], point_list[-1])
                directions.append(direction)

            self._direction = np.mean(directions, axis=0)

        return self._direction

    @property
    def significant_points(self):
        ps = list(self.points)
        yield ps[0]
        yield ps[-1]
        return

        x = self._line_start
        y = self._point_indexes[0]

        yield self._handle_vertical_flipping(x, y)

        # if len(self._point_indexes) > 2:
        #    middle = self.length // 2
        #    yield self._handle_vertical_flipping(x + middle, self._point_indexes[middle])

        yield self._handle_vertical_flipping(x + self.length, self._point_indexes[-1])

    @property
    def center(self):
        middle = self.length // 2
        x = self._line_start + middle
        cy = self._point_indexes[middle]

        return self._handle_vertical_flipping(x, cy)

    @property
    def normal_points(self):
        normal = np.array([self.direction[1], -self.direction[0]])
        normal_length = self.metric_length / 2
        normal_end1 = (self.center + normal * normal_length).astype(np.int)
        normal_end2 = (self.center - normal * normal_length).astype(np.int)

        return normal_end1, normal_end2

    def distance_to_line(self, line: 'PhysicalLine'):
        dmin = sys.maxsize
        for px, py in self.significant_points:
            for opx, opy in line.significant_points:
                d = (px - opx) ** 2 + (py - opy) ** 2
                dmin = min(dmin, d)

        return math.sqrt(dmin)

    def distance_to_point(self, point):
        dmin = sys.maxsize
        for px, py in self.significant_points:
            d = (px - point[0]) ** 2 + (py - point[1]) ** 2
            dmin = min(dmin, d)

        return math.sqrt(dmin)

    def register_next_epoch(self):
        if self._is_updated:
            self._is_updated = False
        else:
            self._stall_time += 1

    def remove_curvature(self, curvature_threshold):
        centered_diff = np.array(self._point_indexes) - self._point_indexes[len(self._point_indexes) // 2]
        slope = self._diff(centered_diff)
        curvature = self._diff(slope)

        offset, point_indexes = self._centered_masked_point_indexes(curvature, curvature_threshold)
        self._line_start += offset
        self._point_indexes = point_indexes

    def _calculate_absolute_angle(self, p1, p2):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]

        direction = unit_vector(np.array((dx, dy)))

        angle = absolute_angle(direction)

        return angle, direction

    def _centered_masked_point_indexes(self, point_mask_values, threshold):
        center = len(point_mask_values) // 2
        mask_offset = point_mask_values[center]

        offset = 0
        points = []

        for value_index, value in enumerate(point_mask_values):
            is_above_threshold = abs(value - mask_offset) > threshold
            is_over_center = value_index >= center

            if is_above_threshold and is_over_center:
                break
            elif is_above_threshold:
                points = []
                offset = value_index
            else:
                points.append(self._point_indexes[value_index])

        return offset, points

    def _diff(self, values):
        result = []
        last_value = None
        for value in values:
            if last_value is None:
                diff = 0
            else:
                diff = last_value - value

            last_value = value

            result.append(diff)

        return result

    def index_distance_to(self, point_index):
        return abs(self._last_index - point_index)

    def add(self, index, width):
        self._is_updated = True

        for _ in range(self._stall_time):
            self._width_sum += width
            self._point_indexes.append(index)

        self._stall_time = 0
        self._width_sum += width
        self._last_index = index
        self._last_width = width
        self._point_indexes.append(index)

    def _handle_vertical_flipping(self, x, y):
        if self.is_vertical:
            return (y, x)
        else:
            return (x, y)

    def __repr__(self):
        return str(list(self.significant_points))
