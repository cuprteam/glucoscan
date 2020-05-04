from operator import itemgetter

from lcd_digit_recognizer.recognition.primitives.digit_center import DigitCenter
import numpy as np

from lcd_digit_recognizer.recognition.utils import angle_between, linear_clustering, ratio_error, span_clustering, \
    stair_clustering, merge_clustering


class DigitNet(object):
    def __init__(self):
        self._digit_centers = []
        self._are_centers_merged = False

    def add_hypothesis(self, x, y, owner):
        if self._are_centers_merged:
            raise AssertionError("Can't add hypothesis now")

        self._digit_centers.append(DigitCenter(x, y, owner))

    def get_aligned_center_buckets(self):
        self._ensure_merged_centers()

        measured_centers = []
        for center in self.centers:
            for cocenter in center.cocenters:
                measured_centers.append((center, cocenter, center.absolute_angle_to(cocenter)))

        clusters = merge_clustering(measured_centers, lambda v: v[2], 10)
        if len(clusters) > 1:
            # because the metric is non-continuous between 0-360 deg
            # join first and last cluster which corresponds to that part
            clusters[0].extend(clusters[-1])
            clusters.pop(-1)

        center_buckets = []
        for cluster in clusters:
            if len(cluster) < 2:
                continue

            projection_angle = cluster[len(cluster) // 2][2] + 90
            projection_rads = np.deg2rad(projection_angle)
            direction = np.array([np.cos(projection_rads), np.sin(projection_rads)])

            # subcluster by alignment

            if direction[1] > direction[0]:
                def projection_metric(v):
                    L = -v[0].y / direction[1]
                    p = v[0].x + L * direction[0]
                    return p, L, (p, 0)
            else:
                def projection_metric(v):
                    L = -v[0].x / direction[0]
                    p = v[0].y + L * direction[1]
                    return p, L, (0, p)

            projected_cluster = []
            for item in cluster:
                p, L, hit = projection_metric(item)
                projected_cluster.append((item[0], item[1], p, L, hit))

            # subclusters = linear_clustering(projected_cluster, itemgetter(2), 20)
            subclusters = merge_clustering(projected_cluster, itemgetter(2), 10)
            subclusters.sort(key=lambda c: len(c), reverse=True)
            # return subclusters[-7:-6] + subclusters[1:3]

            for subcluster in subclusters:

                subcluster = list(set(subcluster))
                subcluster.sort(key=itemgetter(3), reverse=True)

                if len(subcluster) < 2:
                    continue

                center_buckets.append(subcluster)

        center_buckets.sort(key=lambda b: len(b), reverse=True)

        return center_buckets

    @property
    def centers(self):
        self._ensure_merged_centers()
        return self._digit_centers

    def _ensure_merged_centers(self):
        if self._are_centers_merged:
            return  # nothing to do

        self._are_centers_merged = True

        self._collapse_close_centers()
        self._fill_neighbours()
        self._fill_cocenters()
        # self._prune_alone_cocenters()

    def _fill_cocenters(self):
        center_pool = list(self._digit_centers)

        while center_pool:
            current_center = center_pool.pop(0)
            for center in center_pool:
                if center not in current_center.neighbours:
                    continue

                average_segment_length = (current_center.average_segment_length + center.average_segment_length) / 2
                distance_length_diff = abs(current_center.distance_to(center) - average_segment_length)
                if distance_length_diff / average_segment_length < 0.8:
                    current_center.add_cocenter(center)

    def _fill_neighbours(self):
        center_pool = list(self._digit_centers)

        while center_pool:
            current_center = center_pool.pop(0)
            for center in center_pool:
                distance = current_center.distance_to(center)
                if distance > current_center.average_segment_length * 2.5:
                    continue

                if distance < current_center.average_segment_length * 0.7:
                    continue

                aligned_angle_distance = max(
                    current_center.aligned_angle_distance_to(center),
                    center.aligned_angle_distance_to(current_center)
                )
                if aligned_angle_distance > 15:
                    continue

                if ratio_error(current_center.average_segment_length, center.average_segment_length) > 0.3:
                    continue

                current_center.try_add_neighbour(center)

    def _collapse_close_centers(self):
        center_pool = list(self._digit_centers)
        while center_pool:
            current_center = center_pool.pop(0)
            best_center = None
            best_distance = None
            for center in center_pool:
                # if not current_center.can_merge_with(center):
                #    continue

                distance = current_center.distance_to(center)

                if best_distance is None or best_distance > distance:
                    best_distance = distance
                    best_center = center

            if best_distance and best_distance < best_center.average_segment_length / 2:
                best_center.merge_with(current_center)
                self._digit_centers.remove(current_center)
