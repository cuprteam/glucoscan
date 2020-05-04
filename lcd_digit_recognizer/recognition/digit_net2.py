import numpy as np
from typing import List

from lcd_digit_recognizer.recognition.primitives.digit_hypothesis import DigitHypothesis
from lcd_digit_recognizer.recognition.primitives.joint import Joint
from lcd_digit_recognizer.recognition.primitives.physical_line import PhysicalLine
from lcd_digit_recognizer.recognition.utils import angle_between, angle_between_points, ratio_error, \
    get_segment_aligned_angle


class DigitNet2(object):
    def __init__(self, img, lines: List[PhysicalLine]):
        # first, join lines that are close together
        self._img = img
        self._vote_components = self._join_vote_components(lines)
        self._vote_components = self._vote_components[:1] # todo this is for debug only
        self._digit_hypotheses = self._create_hypotheses(self._vote_components)

    @property
    def vote_components(self):
        return list(self._vote_components)

    @property
    def digit_hypotheses(self):
        return self._digit_hypotheses

    def _create_hypotheses(self, vote_components: List[PhysicalLine]):
        result = []

        for component in vote_components:
            for hyp in DigitHypothesis.from_component(component[0]):
                result.append(hyp)

        return result

    def _join_vote_components(self, lines: List[PhysicalLine]):
        for i in range(len(lines)):
            line1 = lines[i]

            for j in range(i + 1, len(lines)):
                line2 = lines[j]
                self._try_join(line1, line2)

        for line in lines:
            current_joints = {}
            for joint in list(line.joints):
                category = get_segment_aligned_angle(joint.angle)
                if category in current_joints:
                    joint2 = current_joints[category]
                    if self._is_joint_better(joint, joint2):
                        to_remove = joint2
                    else:
                        to_remove = joint
                        joint = joint2

                    self._remove_joint(to_remove)

                current_joints[category] = joint

        result = []
        covered_lines = set()

        for line in lines:
            # lines are traversed in the same order
            # as children are added - thus, no cyclic traversing is needed
            if line in covered_lines:
                continue

            component = []
            worklist = [line]
            while worklist:
                current_line = worklist.pop(0)
                if current_line in covered_lines:
                    continue

                covered_lines.add(current_line)
                component.append(current_line)
                for joint in current_line.joints:
                    worklist.append(joint.target_line)

            if len(component) > 1:
                result.append(component)

        return result

    def _is_single_component(self, line1: PhysicalLine, line2: PhysicalLine):
        c1 = line1.center
        c2 = line2.center

        c1_color = self._img[c1]
        c2_color = self._img[c2]

        # if ratio_error(sum(c1_color), sum(c2_color)) > 0.1:
        #    return False

        distance = line1.distance_to_line(line2)

        avg_length = (line1.metric_length + line2.metric_length) / 2
        if distance > avg_length / 2.5:
            return False

        ld = line1.distance_to_line(line2)
        cd1 = line1.distance_to_point(line2.center)
        cd2 = line2.distance_to_point(line1.center)
        if min(cd1, cd2) < ld:
            return False  # filter out splitting lines

        s1, e1, s2, e2 = self.get_oriented_endpoints(line1, line2)

        diff1 = self.get_alignment_diff(s1, e1, e2)
        diff2 = self.get_alignment_diff(s1, s2, e2)

        skip_point_threshold = 30
        if diff1 > skip_point_threshold or diff2 > skip_point_threshold:
            return False

        p1, p2, p3 = self.get_joint_points(line1, line2)

        alignment_diff = self.get_alignment_diff(p1, p2, p3)
        return alignment_diff < 15

    def _is_joint_better(self, j1, j2):
        d1 = j1.source_line.distance_to_line(j1.target_line)
        d2 = j2.source_line.distance_to_line(j2.target_line)
        return d1 < d2

        aligned_angle = get_segment_aligned_angle(j1.angle)

        diff1 = abs(j1.angle - aligned_angle)
        diff2 = abs(j2.angle - aligned_angle)

        return diff1 < diff2

    def _try_join(self, line1, line2):
        if not self._is_single_component(line1, line2):
            return

        p1, p2, p3 = self.get_joint_points(line1, line2)
        a1 = angle_between_points(p1, p2, p3)
        a2 = angle_between_points(p3, p2, p1)
        j1 = Joint(line1, a1, line2, [p1, p2, p3])
        j2 = Joint(line2, a2, line1, [p3, p2, p1])

        if j1.angle_category == 0:
            return  # returning joints are not allowed

        line1.joints.append(j1)
        line2.joints.append(j2)

    def _remove_joint(self, joint):
        joint.source_line.joints.remove(joint)
        for j2 in joint.target_line.joints:
            if j2.target_line is joint.source_line and j2.source_line is joint.target_line:
                joint.target_line.joints.remove(j2)
                return

        raise AssertionError("Joint was not found")

    def get_alignment_diff(self, p1, p2, p3):
        # check angles
        angle = angle_between_points(p1, p2, p3)
        if angle < 0:
            raise AssertionError("Negative angle was not expected")

        # alignment allows only 90deg, 180deg or 270deg
        aligned_angle = get_segment_aligned_angle(angle)
        return abs(aligned_angle - angle)

    def get_oriented_endpoints(self, line1, line2):
        s1, e1 = line1.significant_points
        s2, e2 = line2.significant_points

        hypotheses = [
            (s1, e1, e2, s2),
            (s1, e1, s2, e2),
            (e1, s1, e2, s2),
            (e1, s1, s2, e2),
        ]

        j0, j1a, j1b, j2 = min(hypotheses, key=lambda h: (h[1][0] - h[2][0]) ** 2 + (h[1][1] - h[2][1]) ** 2)
        return j0, j1a, j1b, j2

    def get_joint_points(self, line1, line2):
        j0, j1a, j1b, j2 = self.get_oriented_endpoints(line1, line2)
        j1 = ((j1a[0] + j1b[0]) // 2, (j1a[1] + j1b[1]) // 2)

        return j0, j1, j2
