import math


class LineCluster(object):
    def __init__(self, *lines):
        self._lines = list(lines)
        self._tc = None
        self._bc = None
        self._parent = None
        self._children = []

    @property
    def lines(self):
        return list(self._lines)

    @property
    def line_count(self):
        return len(self._lines)

    @property
    def points(self):
        for line in self._lines:
            for point in line.points:
                yield point

    @property
    def top_corner(self):
        if self._tc is None:
            self._tc = min(p[0] for p in self.points), min(p[1] for p in self.points)

        return self._tc

    @property
    def bottom_corner(self):
        if self._bc is None:
            self._bc = max(p[0] for p in self.points), max(p[1] for p in self.points)

        return self._bc

    @property
    def family_top_corner(self):
        tcx, tcy = self.top_corner
        for child in self._children:
            x, y = child.family_top_corner
            tcx = min(tcx, x)
            tcy = min(tcy, y)
        return tcx, tcy

    @property
    def family_bottom_corner(self):
        bcx, bcy = self.bottom_corner
        for child in self._children:
            x, y = child.family_bottom_corner
            bcx = max(bcx, x)
            bcy = max(bcy, y)
        return bcx, bcy

    @property
    def family_width(self):
        return self.family_bottom_corner[0] - self.family_top_corner[0]

    @property
    def family_height(self):
        return self.family_bottom_corner[1] - self.family_top_corner[1]

    @property
    def width(self):
        return self.bottom_corner[0] - self.top_corner[0]

    @property
    def height(self):
        return self.bottom_corner[1] - self.top_corner[1]

    @property
    def center(self):
        tc = self.top_corner
        bc = self.bottom_corner
        return (tc[0] + bc[0]) // 2, (tc[1] + bc[1]) // 2

    @property
    def line_width(self):
        return sum(l.average_width for l in self._lines) / len(self._lines)

    @property
    def line_length(self):
        return sum(l.length for l in self._lines) / len(self._lines)

    @property
    def is_leader(self):
        return self._parent is None

    def add(self, line):
        self._lines.append(line)

    def join_to(self, cluster):
        self._parent = cluster
        cluster._children.append(self)

    def get_width_distance(self, line):
        return max(abs(l.average_width - line.average_width) for l in self._lines)

    def get_line_distance(self, line):
        return min(line.distance_to_line(l) for l in self._lines)

    def get_cluster_distance(self, cluster):
        cx, cy = self.center
        ocx, ocy = cluster.center
        return math.sqrt((cx - ocx) ** 2 + (cy - ocy) ** 2)

    def get_join_error(self, cluster):
        return min(abs(self.width - cluster.width), abs(self.height - cluster.height))
