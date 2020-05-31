from typing import List, Tuple


def leading_rectangles_to_str(rectangles: List[Tuple[List[int], float, int]]) -> str:
    rectangles.sort(key=lambda x: x[0][0])
    digits = [str(r[-1]) for r in rectangles]
    str_representation = "".join(digits[:-1]) + "." + digits[-1]
    return str_representation
