from typing import List, Tuple


def rectangles_could_be_adjacent_digits(rectangle_a: Tuple[List[int], float, int],
                                        rectangle_b: Tuple[List[int], float, int],
                                        max_allowed_size_ratio: float = 1.4,
                                        min_allowed_horizontal_distance_multiple: float = 1.0,
                                        max_allowed_horizontal_distance_multiple: float = 0.4,
                                        max_allowed_vertical_distance_multiple: float = 0.3) -> bool:
    (x0_a, y0_a, x1_a, y1_a), match_coeff_a, digit_a = rectangle_a
    (x0_b, y0_b, x1_b, y1_b), match_coeff_b, digit_b = rectangle_b
    width_a, width_b = x1_a - x0_a, x1_b - x0_b
    height_a, height_b = y1_a - y0_a, y1_b - y0_b

    result = width_a / width_b < max_allowed_size_ratio and \
             width_b / width_a < max_allowed_size_ratio and \
             height_a / height_b < max_allowed_size_ratio and \
             height_b / height_a < max_allowed_size_ratio and \
             abs(x0_a - x0_b) > (width_a + width_b) / 2 * min_allowed_horizontal_distance_multiple and \
             min(abs(x1_a - x0_b), abs(x1_b - x0_a)) < (
                     width_a + width_b) / 2 * max_allowed_horizontal_distance_multiple and \
             abs(y0_a - y0_b) < (height_a + height_b) / 2 * max_allowed_vertical_distance_multiple

    return result


def get_leading_rectangles(rectangles: List[Tuple[List[int], float, int]]) \
        -> List[Tuple[List[int], float, int]]:
    best_pair_coeff = -1
    best_pair = []
    for rectangle_left in rectangles:
        (x0_left, y0_left, x1_left, y1_left), match_coeff_left, digit_left = rectangle_left
        for rectangle_right in rectangles:
            (x0_right, y0_right, x1_right, y1_right), match_coeff_right, digit_right = rectangle_right

            if rectangles_could_be_adjacent_digits(rectangle_left, rectangle_right) \
                    and x0_left < x0_right:
                cumulative_coeff = match_coeff_left + match_coeff_right
                if cumulative_coeff > best_pair_coeff:
                    best_pair_coeff = cumulative_coeff
                    best_pair = [rectangle_left, rectangle_right]

    if len(best_pair) == 0:
        return best_pair

    best_rectangle_left, best_rectangle_right = best_pair
    (x0_left, y0_left, x1_left, y1_left), match_coeff_left, digit_left = best_rectangle_left
    (x0_right, y0_right, x1_right, y1_right), match_coeff_right, digit_right = best_rectangle_right

    best_coeff_leftmost = -1
    best_coeff_rightmost = -1
    best_rectangle_leftmost = []
    best_rectangle_rightmost = []
    for rectangle in rectangles:
        (x0, y0, x1, y1), match_coeff, digit = rectangle
        if x0 < x0_left and rectangles_could_be_adjacent_digits(rectangle, best_rectangle_left):
            if match_coeff > best_coeff_leftmost:
                best_coeff_leftmost = match_coeff
                best_rectangle_leftmost = [rectangle]
        if x1 > x1_right and rectangles_could_be_adjacent_digits(rectangle, best_rectangle_right):
            if match_coeff > best_coeff_rightmost:
                best_coeff_rightmost = match_coeff
                best_rectangle_rightmost = [rectangle]

    # TODO: here is a space for some prior. It is for example far less likely to get 2
    # as the leftmost digit, but if it matches really well, it could happen.

    use_rightmost = best_coeff_leftmost < best_coeff_rightmost
    if use_rightmost:
        return best_pair + best_rectangle_rightmost
    else:
        return best_rectangle_leftmost + best_pair
