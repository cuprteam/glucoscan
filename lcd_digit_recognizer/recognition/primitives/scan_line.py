from typing import List, Tuple
import numpy as np


class ScanLine(object):
    def __init__(self, line_index, pixel_line):
        self.line_index = line_index

        self._centers = []

        active_indexes = np.nonzero(pixel_line)[0]
        if not len(active_indexes):
            return

        last_active_pixel_index = active_indexes[0]

        for i in range(1, len(active_indexes)):
            index = active_indexes[i]

            width = abs(last_active_pixel_index - index)
            if width < 5:
                continue

            center = (last_active_pixel_index + index) // 2
            self._centers.append((center, width))

            last_active_pixel_index = index

    def physical_line_center_indexes(self) -> List[Tuple[int, int]]:
        return list(self._centers)

    @property
    def is_empty(self):
        return len(self._centers) == 0
