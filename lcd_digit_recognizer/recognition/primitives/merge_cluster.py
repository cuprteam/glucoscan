class MergeCluster(object):
    def __init__(self):
        self.start = None
        self.end = None

        self.min = None
        self.max = None

    def add(self, index, score):
        if self.start is None:
            self.start = index
            self.end = index
            self.min = score
            self.max = score
        else:
            self.start = min(self.start, index)
            self.end = max(self.end, index)

            self.min = min(self.min, score)
            self.max = max(self.max, score)

    def accept(self, cluster):
        self.start = min(self.start, cluster.start)
        self.end = max(self.end, cluster.end)

        self.min = min(self.min, cluster.min)
        self.max = max(self.max, cluster.max)
