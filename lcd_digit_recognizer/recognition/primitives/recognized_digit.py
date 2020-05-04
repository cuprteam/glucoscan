from lcd_digit_recognizer.recognition.utils import unit_vector, absolute_angle
import numpy as np


class RecognizedDigit(object):
    def __init__(self, value, center, cocenter):
        self._value = value
        self._center = center
        self._cocenter = cocenter
        self._next_digit = None
        self._previous_digit = None

    @property
    def absolute_angle(self):
        return self._center.absolute_angle_to(self._cocenter)

    @property
    def value(self):
        return self._value

    @property
    def first(self):
        current_number = self
        while current_number._previous_digit is not None:
            current_number = current_number._previous_digit

        return current_number

    @property
    def digit_count(self):
        if self._previous_digit is not None:
            raise AssertionError("Can't count digits from middle of a number")

        counter = 0
        current = self
        while current is not None:
            current = current._next_digit
            counter += 1

        return counter

    @property
    def axis_length(self):
        return self._center.distance_to(self._cocenter)

    def join_to(self, other_digit):
        if other_digit is None:
            raise AssertionError("Invalid argument passed for digit joining")

        if self._next_digit is not None:
            raise AssertionError("Can't join to multiple digits")

        if other_digit._previous_digit is not None:
            raise AssertionError("Can't join to already joined digit")

        self._next_digit = other_digit
        other_digit._previous_digit = self

    def __repr__(self):
        return f"Digit: {self._value}, {self._next_digit}"
