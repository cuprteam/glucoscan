from typing import List, Tuple


class DigitHypothesis(object):
    """
    (0,0) ----- (1,0)
      |           |
      |           |
    (0,1) ----- (1,1)
      |           |
      |           |
    (0,2) ----- (1,2)
    """

    start_points = [
        (0, 0),
        (1, 0)
    ]

    start_directions = [
        0,
        1,
    ]

    direction_table = [
        (1, 0),
        (0, 1),
        (-1, 0),
        (0, -1)
    ]

    def __init__(self):
        self._vertices = [[None, None, None], [None, None, None]]

    @property
    def vertexes(self):
        for x in range(2):
            for y in range(3):
                vertex = self._vertices[x][y]
                if vertex:
                    yield vertex

    @classmethod
    def from_component(cls, component_root) -> List['DigitHypothesis']:
        result = []
        for start_point in DigitHypothesis.start_points:
            for start_direction in DigitHypothesis.start_directions:
                builder = HypothesisBuilder(component_root, start_point, start_direction)
                for hypothesis_vertices in builder.get_mirrored_hypotheses():
                    hypothesis = DigitHypothesis()
                    hypothesis._vertices = hypothesis_vertices
                    result.append(hypothesis)

        return result

    @classmethod
    def move(cls, point, direction):
        direction_offsets = cls.direction_table[direction % len(cls.direction_table)]
        result = (point[0] + direction_offsets[0], point[1] + direction_offsets[1])

        return result


class HypothesisBuilder(object):
    def __init__(self, component_root, start_point: Tuple[int, int], direction: int):
        self._start_point = start_point
        self._direction = direction

        self._recorded_vertices = {}

        self._processed_lines = []

        self._write_joints(start_point, direction, component_root)

    def get_mirrored_hypotheses(self):
        for h in [
            self._rotated_vertices((1, 0), (0, 1)),
            self._rotated_vertices((0, 1), (1, 0)),
            self._rotated_vertices((-1, 0), (0, -1)),
            self._rotated_vertices((0, -1), (-1, 0))
        ]:
            if h is not None:
                yield h

    def _rotated_vertices(self, rot_x, rot_y):
        result = [[None, None, None], [None, None, None]]
        for (x, y), value in self._recorded_vertices.items():
            rx = rot_x[0] * x + rot_x[1] * y
            ry = rot_y[0] * x + rot_y[1] * y

            if rx < 0 or rx > 1:
                return None

            if ry < 0 or ry > 2:
                return None

            result[rx][ry] = value

        return result

    def _write_joints(self, point, direction, line):
        if line in self._processed_lines:
            return

        self._processed_lines.append(line)
        for joint in line.joints:
            if joint.source_line is not line:
                continue

            if joint.angle_category == 180:
                after_join_direction = direction
            elif joint.angle_category == 90:
                after_join_direction = direction - 1
            elif joint.angle_category == 270:
                after_join_direction = direction + 1
            else:
                raise NotImplementedError(f"Invalid angle category {joint.angle_category}")

            p1_index = point
            p2_index = DigitHypothesis.move(point, direction)
            p3_index = DigitHypothesis.move(p2_index, after_join_direction)

            self._write_vertex(p1_index, joint.p1)
            self._write_vertex(p2_index, joint.p2)
            self._write_vertex(p3_index, joint.p3)

            self._write_joints(p3_index, after_join_direction, joint.target_line)

    def _write_vertex(self, index, vertex):
        # todo some blending maybe could be here
        self._recorded_vertices[index] = vertex
