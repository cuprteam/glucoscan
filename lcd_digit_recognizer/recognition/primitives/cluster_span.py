class ClusterSpan(object):
    def __init__(self, scored_values, threshold):
        self._scored_values = scored_values
        self._threshold = threshold

        self._start = 0
        self._end = len(self._scored_values) - 1

    @property
    def is_valid(self):
        return self._scored_values[self._start][1] - self._scored_values[self._end][1] < self._threshold

    @property
    def values(self):
        return [sv[0] for sv in self._scored_values[self._start:self._end + 1]]

    def make_hungry_split(self):
        old_start = self._start
        old_end = self._end

        while not self.is_valid:
            hyp1 = self._scored_values[self._start + 1][1] - self._scored_values[self._end][1]
            hyp2 = self._scored_values[self._start][1] - self._scored_values[self._end - 1][1]

            if hyp1 < hyp2:
                self._start += 1
            else:
                self._end -= 1

        if self._start > old_start:
            span = ClusterSpan(self._scored_values, self._threshold)
            span._start = old_start
            span._end = self._start - 1
            yield span

        if self._end < old_end:
            span = ClusterSpan(self._scored_values, self._threshold)
            span._start = self._end + 1
            span._end = old_end
            yield span
