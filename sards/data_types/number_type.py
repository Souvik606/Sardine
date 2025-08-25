"""
number_operations.py

This module defines a `Number` class that represents numerical values with additional
functionalities such as:
- Basic arithmetic operations (addition, subtraction, multiplication, division).
- Error handling for division by zero.
- Position tracking for error handling and debugging.
- Context management.

Classes:
- Number: Represents a number and supports basic arithmetic operations.
"""
from sards.core.error import RunTimeError, IllegalOperationError

class Number:
    """
    A class representing a numerical value with context and position tracking.

    Attributes:
    - value (float/int): The numerical value.
    - pos_start (optional): The start position of the number (used for error tracking).
    - pos_end (optional): The end position of the number (used for error tracking).
    - context (optional): Context information for debugging.
    """

    def __init__(self, value):
        """
        Initializes a Number instance.

        Parameters:
        - value (float or int): The numerical value of the instance.
        """
        self.value = value
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        """
        Sets the position of the number (used for error tracking).

        Parameters:
        - pos_start (optional): The starting position of the number.
        - pos_end (optional): The ending position of the number.

        Returns:
        - self: The current Number instance.
        """
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        """
        Sets the context of the number (used for debugging and error tracking).

        Parameters:
        - context (optional): The context information.

        Returns:
        - self: The current Number instance.
        """
        self.context = context
        return self

    def add(self, operand):
        """
        Adds another Number instance to the current instance.

        Parameters:
        - operand (Number): The number to add.

        Returns:
        - Number: A new Number instance with the result.
        - IllegalOperationError: An error if operand is not of type Number.
        """
        if isinstance(operand, Number):
            return Number(self.value + operand.value).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def subtract(self, operand):
        """
        Subtracts another Number instance from the current instance.

        Parameters:
        - operand (Number): The number to subtract.

        Returns:
        - Number: A new Number instance with the result.
        - IllegalOperationError: An error if operand is not of type Number.
        """
        if isinstance(operand, Number):
            return Number(self.value - operand.value).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def multiply(self, operand):
        """
        Multiplies another Number instance with the current instance.

        Parameters:
        - operand (Number): The number to multiply.

        Returns:
        - Number: A new Number instance with the result.
        - IllegalOperationError: An error if operand is not of type Number.
        """
        if isinstance(operand, Number):
            return Number(self.value * operand.value).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def _get_runtime_error():
        from sards.core import RunTimeError
        return RunTimeError
    
    def divide(self, operand):
        """
        Divides the current Number instance by another Number instance.

        Parameters:
        - operand (Number): The number to divide by.

        Returns:
        - Number: A new Number instance with the result if division is successful.
        - RunTimeError: An error if division by zero is attempted.
        - IllegalOperationError: An error if operand is not of type Number.
        """
        if isinstance(operand, Number):
            if operand.value == 0:
                return None, RunTimeError(
                    operand.pos_start, operand.pos_end, 'Division by zero', self.context
                )
            return Number(self.value / operand.value).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def modulus(self, operand):
        if isinstance(operand, Number):
            if operand.value == 0:
                return None, RunTimeError(
                    operand.pos_start, operand.pos_end, 'Division by zero', self.context
                )
            return Number(self.value % operand.value).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def floor_divide(self, operand):
        if isinstance(operand, Number):
            if operand.value == 0:
                return None, RunTimeError(
                    operand.pos_start, operand.pos_end, 'Division by zero', self.context
                )
            return Number(self.value // operand.value).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def exponent(self, operand):
        if isinstance(operand, Number):
            return Number(self.value ** operand.value).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def get_comparison_eq(self, operand):
        if isinstance(operand, Number):
            return Number(int(self.value == operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def get_comparison_neq(self, operand):
        if isinstance(operand, Number):
            return Number(int(self.value != operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def get_comparison_lte(self, operand):
        if isinstance(operand, Number):
            return Number(int(self.value <= operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def get_comparison_lt(self, operand):
        if isinstance(operand, Number):
            return Number(int(self.value < operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def get_comparison_gte(self, operand):
        if isinstance(operand, Number):
            return Number(int(self.value >= operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def get_comparison_gt(self, operand):
        if isinstance(operand, Number):
            return Number(int(self.value > operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def and_by(self, operand):
        if isinstance(operand, Number):
            return (Number(int(self.value != 0 and operand.value != 0)).set_context(self.context),
                    None)
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def or_by(self, operand):
        if isinstance(operand, Number):
            return (Number(int(self.value != 0 or operand.value != 0)).set_context(self.context),
                    None)
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a Number type')

    def not_by(self):
        return Number(int(not self.value)).set_context(self.context), None

    def is_true(self):
        return self.value != 0

    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        """
        Returns a string representation of the Number instance.

        Returns:
        - str: The string representation of the numerical value.
        """
        return str(self.value)
