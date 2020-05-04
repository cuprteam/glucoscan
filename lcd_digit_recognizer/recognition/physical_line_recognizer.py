from typing import List

from lcd_digit_recognizer.recognition.primitives.open_line_wave import OpenLineWave
from lcd_digit_recognizer.recognition.primitives.physical_line import PhysicalLine
from lcd_digit_recognizer.recognition.primitives.scan_line import ScanLine


class PhysicalLineRecognizer(object):
    def __init__(self, is_vertical):
        self._stall_limit = 1
        self._physical_line_skip_threshold = 2
        self._lines = []
        self._is_vertical = is_vertical
        self._current_line_index = 0

    def accept(self, line):
        line = ScanLine(self._current_line_index, line)
        self._current_line_index += 1

        self._lines.append(line)

    def get_physical_lines(self) -> List[PhysicalLine]:
        wave = OpenLineWave(self._physical_line_skip_threshold, self._stall_limit, self._is_vertical)

        for line in self._lines:
            for center_point_index, width in line.physical_line_center_indexes():
                wave.accept(center_point_index, width)

            wave.move()

        return wave._collected_lines
