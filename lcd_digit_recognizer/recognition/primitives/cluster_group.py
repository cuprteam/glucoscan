class ClusterGroup(object):
    def __init__(self, *clusters):
        self._clusters = list(clusters)
