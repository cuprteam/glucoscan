from typing import Dict

from lcd_digit_recognizer.recognition.primitives.physical_line import PhysicalLine


class OpenLineWave(object):
    def __init__(self, skip_limit, stall_limit, is_vertical):
        self._stall_limit = stall_limit

        self._current_line_index = 0
        self._is_vertical = is_vertical
        self._open_lines = []
        self._lookup: Dict[int, PhysicalLine] = {}
        self._lookup_pattern = [0]

        self._collected_lines = []

        for i in range(1, skip_limit):
            self._lookup_pattern.append(-i)
            self._lookup_pattern.append(i)

    def accept(self, center_index, width):
        for i in self._lookup_pattern:
            index = center_index + i

            if index in self._lookup:
                line = self._lookup[index]

                line.add(center_index, width)
                if i != 0:
                    del self._lookup[index]
                    self._lookup[center_index] = line

                return  # line was found

        # new line has to be added
        line = PhysicalLine(
            self._current_line_index, center_index, width,
            self._is_vertical
        )

        self._open_lines.append(line)
        self._lookup[center_index] = line

    def move(self):
        self._current_line_index += 1
        for open_line in list(self._open_lines):
            open_line.register_next_epoch()
            if open_line.current_stall_time > self._stall_limit:
                self._open_lines.remove(open_line)
                self._collected_lines.append(open_line)
                del self._lookup[open_line._last_index]
