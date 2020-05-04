import math
from operator import itemgetter
from typing import Callable

import numpy as np

from lcd_digit_recognizer.recognition.primitives.cluster_span import ClusterSpan
from lcd_digit_recognizer.recognition.primitives.merge_cluster import MergeCluster


def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)


def angle_between(v1, v2):
    """ Returns the angle in degrees between vectors 'v1' and 'v2':: """

    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    radians = np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))
    return np.rad2deg(radians)


def angle_between_points(a, b, c):
    ang = math.degrees(math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0]))
    return ang + 360 if ang < 0 else ang


def get_segment_aligned_angle(angle):
    if angle < 0:
        raise AssertionError("Negative angle was not expected")
    elif angle < 90 - 45:
        return 0
    elif angle < 180 - 45:
        return 90
    elif angle < 270 - 45:
        return 180
    elif angle < 360 - 45:
        return 270
    else:
        return 0


def absolute_angle(direction):
    return np.degrees(np.arctan2(direction[1], direction[0])) % 360.0


def calculate_angle_distance(x, y):
    while x < 0:
        x += 360
    x %= 360

    while y < 0:
        y += 360
    y %= 360

    if x < y:
        x, y = y, x

    diff1 = x - y
    diff2 = y - x + 360

    return min(diff1, diff2)


def merge_clustering(values, metric: Callable, range_threshold: float):
    if range_threshold < 0:
        raise AssertionError("Threshold has to be positive")

    scored_values = []
    for value in values:
        score = metric(value)
        scored_values.append((value, score))

    scored_values.sort(key=itemgetter(1), reverse=True)

    if not scored_values:
        return []

    diffs = []
    last_score = scored_values[0][1]
    for value, score in scored_values[1:]:
        diff = last_score - score
        diffs.append(diff)
        last_score = score

    merge_order = np.argsort(diffs)
    cluster_cover = [None] * len(scored_values)

    for merge_index in merge_order:
        m1 = merge_index
        m2 = merge_index + 1

        c1 = _get_merge_cluster(m1, cluster_cover, scored_values)
        c2 = _get_merge_cluster(m2, cluster_cover, scored_values)

        if c1.min - c2.max < range_threshold:
            # they can be merged

            c1.accept(c2)
            cluster_cover[c1.start] = c1
            cluster_cover[c1.end] = c1

    result = []

    i = 0
    while i < len(scored_values):
        cluster = cluster_cover[i]
        cluster_values = []

        for j in range(cluster.start, cluster.end + 1):
            cluster_values.append(scored_values[j][0])

        result.append(cluster_values)
        i = cluster.end + 1

    return result


def stair_clustering(values, metric: Callable, range_threshold: float):
    if range_threshold < 0:
        raise AssertionError("Threshold has to be positive")

    scored_values = []
    for value in values:
        score = metric(value)
        scored_values.append((value, score))

    scored_values.sort(key=itemgetter(1), reverse=True)

    stairs = []
    last_score = None
    for value, score in scored_values:
        if last_score is None:
            last_score = score

        diff = last_score - score
        stairs.append(diff)
        last_score = score

    stair_sorting = np.argsort(stairs)[::-1]
    stair_coverage = np.zeros_like(stair_sorting)
    end = len(stair_coverage)

    result = []
    for stair_index in stair_sorting:
        if stair_coverage[stair_index]:
            continue

        start = stair_index
        current_cluster = []
        diff = None

        current_index = start + 1
        while (diff is None or diff <= range_threshold) and current_index < end and not stair_coverage[current_index]:
            stair_coverage[current_index] = 1
            current_cluster.append(scored_values[current_index])
            diff = current_cluster[0][1] - current_cluster[-1][1]
            current_index += 1

        current_index = start
        while (diff is None or diff <= range_threshold) and current_index >= 0 and not stair_coverage[current_index]:
            stair_coverage[current_index] = 1
            current_cluster.insert(0, scored_values[current_index])
            diff = current_cluster[0][1] - current_cluster[-1][1]
            current_index -= 1

        result.append([c[0] for c in current_cluster])

        result.sort(key=lambda c: metric(c[0]), reverse=True)

        # rebalancing phase
        last_c = None
        for c in result:
            if last_c is not None:
                lm = metric(last_c[-1])
                cm0 = metric(c[0])

                if len(c) > 1:
                    cm1 = metric(c[1])

                    if lm - cm0 < cm0 - cm1:
                        # rebalance
                        if lm - cm0 < range_threshold:
                            last_c.append(c.pop(0))
                    elif len(last_c) > 1:
                        prelm = metric(last_c[-2])
                        if prelm - lm > lm - cm0:
                            if prelm - lm < range_threshold:
                                c.insert(0, last_c.pop(-1))

            last_c = c

    return result


def span_clustering(values, metric: Callable, range_threshold: float):
    if range_threshold < 0:
        raise AssertionError("Threshold has to be positive")

    scored_values = []
    for value in values:
        score = metric(value)
        scored_values.append((value, score))

    scored_values.sort(key=itemgetter(1), reverse=True)

    spans_to_split = [ClusterSpan(scored_values, range_threshold)]

    completed_spans = []

    while spans_to_split:
        span = spans_to_split.pop(0)
        if span.is_valid:
            completed_spans.append(span)
            continue

        new_spans = span.make_hungry_split()
        spans_to_split.extend(new_spans)
        completed_spans.append(span)

    completed_spans.sort(key=lambda s: s._start)

    result = []
    for span in completed_spans:
        result.append(span.values)

    return result


def linear_clustering(values, metric: Callable, diff_threshold: float = None):
    if diff_threshold < 0:
        raise AssertionError("Threshold has to be positive")

    if not values:
        return []

    sorted_values = list(values)
    sorted_values.sort(key=metric, reverse=True)

    clusters = []
    current_cluster = [sorted_values[0]]
    last_value_metric = metric(sorted_values[0])

    for value in sorted_values[1:]:
        diff = abs(last_value_metric - metric(value))
        if diff < 0.0:
            raise AssertionError(f"Invalid ordering detected -> descending order was expected but got {diff}")

        if diff < diff_threshold:
            current_cluster.append(value)
        else:
            clusters.append(current_cluster)
            current_cluster = [value]
            last_value_metric = metric(value)

    if current_cluster:
        clusters.append(current_cluster)

    return clusters


def ratio_error(a, b):
    return abs(a - b) / (abs(a) + abs(b))


def _get_merge_cluster(index, cluster_cover, scored_values):
    cluster = cluster_cover[index]
    if cluster is None:
        cluster_cover[index] = cluster = MergeCluster()
        cluster.add(index, scored_values[index][1])

    return cluster


if __name__ == "__main__":
    test = [1, 2, 3, 34, 56, 2, 223]
    print(merge_clustering(test, lambda v: v, 25))

    test2 = [1, 2, 3, 4, 5, 15, 16, 17, 18, 19, 40, 42, 43]
    print(merge_clustering(test2, lambda v: v, 10))
