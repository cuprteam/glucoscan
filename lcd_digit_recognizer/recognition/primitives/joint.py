from typing import Tuple, List

from lcd_digit_recognizer.recognition.primitives.physical_line import PhysicalLine
from lcd_digit_recognizer.recognition.utils import get_segment_aligned_angle


class Joint(object):
    def __init__(self, source_line: PhysicalLine, angle: float, target_line: PhysicalLine, points: List[Tuple]):
        self.source_line = source_line
        self.angle = angle
        self.angle_category = get_segment_aligned_angle(angle)
        self.target_line = target_line
        self.p1, self.p2, self.p3 = points

    def __repr__(self):
        return f"{self.source_line} {self.angle} {self.target_line}"
