import math

from lcd_digit_recognizer.recognition.utils import unit_vector, absolute_angle, calculate_angle_distance


class DigitCenter(object):
    def __init__(self, x, y, voter):
        self._x = x
        self._y = y
        self._voters = set([voter])
        self._neighbours = []
        self._cocenters = []

    @property
    def x(self):
        return int(self._x)

    @property
    def y(self):
        return int(self._y)

    def as_point(self):
        return (self.x, self.y)

    @property
    def average_segment_length(self):
        length_sum = sum(v.metric_length for v in self._voters)

        return length_sum / len(self._voters)

    @property
    def average_segment_angle(self):
        angle_sum = sum(v.absolute_angle for v in self._voters)
        return angle_sum / len(self._voters)

    @property
    def average_segment_aligned_angle(self):
        for voter in self._voters:
            # TODO add aligning averaging algorithm
            return voter.absolute_angle

    @property
    def neighbours(self):
        return self._neighbours

    @property
    def cocenters(self):
        return self._cocenters

    def absolute_angle_to(self, cocenter):
        dx = cocenter.x - self.x
        dy = cocenter.y - self.y

        direction = unit_vector([dx, dy])
        return absolute_angle(direction)

    def aligned_angle_distance_to(self, center):
        a1 = self.absolute_angle_to(center)
        a2 = self.average_segment_aligned_angle

        return min(
            calculate_angle_distance(a1, a2),
            calculate_angle_distance(a1, a2 + 90),
            calculate_angle_distance(a1, a2 + 180),
            calculate_angle_distance(a1, a2 + 270),
        )

    def try_add_neighbour(self, neighbour):
        if neighbour is self:
            return

        if neighbour in self._neighbours:
            return

        """
        for voter in self._voters:
            if voter in neighbour._voters:
                return

        for voter in neighbour._voters:
            if voter in self._voters:
                return
        """

        self._neighbours.append(neighbour)
        neighbour._neighbours.append(self)

    def add_cocenter(self, cocenter):
        self._cocenters.append(cocenter)
        cocenter._cocenters.append(self)

    def remove_cocenter(self, cocenter):
        self._cocenters.remove(cocenter)
        cocenter._cocenters.remove(self)

    def merge_with(self, digit_center):

        svc = len(self._voters)
        ovc = len(digit_center._voters)
        tc = svc + ovc
        self._x = (self._x * svc + digit_center._x * ovc) / tc
        self._y = (self._y * svc + digit_center._y * ovc) / tc

        self._voters.union(digit_center._voters)

    def can_merge_with(self, digit_center):

        return True

    def distance_to(self, digit_center):
        return math.sqrt((self._x - digit_center._x) ** 2 + (self._y - digit_center._y) ** 2)

    def __repr__(self):
        return f"({self._x},{self._y})"
