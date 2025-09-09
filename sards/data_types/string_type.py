from .number_type import *
from sards.core.error import RunTimeError, IllegalOperationError, IndexOutOfBoundsError


class StringNode:
    def __init__(self, token):
        self.token = token
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end

    def __repr__(self):
        return f'{self.token}'


class String:
    def __init__(self, value):
        self.value = value
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def add(self, operand):
        if isinstance(operand, String):
            return String(self.value + operand.value).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def subtract(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'-\' to a String type', self.context)

    def multiply(self, operand):
        if isinstance(operand, Number) and not isinstance(operand.value, float):
            return String(self.value * operand.value).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected an integer Number type', self.context)

    def divide(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'/\' to a String type', self.context)

    def modulus(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'%\' to a String type', self.context)

    def floor_divide(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'//\' to a String type', self.context)

    def exponent(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'**\' to a String type', self.context)

    def get_comparison_eq(self, operand):
        if isinstance(operand, String):
            return Number(int(self.value == operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def get_comparison_neq(self, operand):
        if isinstance(operand, String):
            return Number(int(self.value != operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def get_comparison_lte(self, operand):
        if isinstance(operand, String):
            return Number(int(self.value <= operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def get_comparison_lt(self, operand):
        if isinstance(operand, String):
            return Number(int(self.value < operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def get_comparison_gte(self, operand):
        if isinstance(operand, String):
            return Number(int(self.value >= operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def get_comparison_gt(self, operand):
        if isinstance(operand, String):
            return Number(int(self.value > operand.value)).set_context(self.context), None
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def and_by(self, operand):
        if isinstance(operand, String):
            return (Number(int(self.value and operand.value)).set_context(self.context),
                    None)
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def or_by(self, operand):
        if isinstance(operand, String):
            return (Number(int(self.value or operand.value)).set_context(self.context),
                    None)
        else: return None, IllegalOperationError(
                    operand.pos_start, operand.pos_end, 'Expected a String type', self.context)

    def not_by(self):
        return Number(int(not self.value)).set_context(self.context), None

    def is_true(self):
        return Number(len(self.value)).set_context(self.context), None
    
    def getByIndex(self, indexes):
        temp = self.value
        try:
            for idx in indexes:
                if isinstance(idx, Number) and not isinstance(idx.value, float):
                    if not isinstance(temp, str):
                        return None, IllegalOperationError(
                            idx.pos_start, idx.pos_end,
                            "Can't index a non-string value",
                            self.context
                        )
                    temp = temp[idx.value]
                else:
                    return None, IllegalOperationError(
                        idx.pos_start, idx.pos_end,
                        "Invalid Index Type",
                        self.context
                    )
            return String(temp).set_context(self.context), None
        except IndexError:
            bad_idx = indexes[-1]
            return None, IndexOutOfBoundsError(
                bad_idx.pos_start, bad_idx.pos_end,
                "Index out of bounds",
                self.context
            )

    def assignIndex(self, indexes, val):
        if not isinstance(val, String) or len(val.value) != 1:
            return None, IllegalOperationError(
                getattr(val, "pos_start", None),
                getattr(val, "pos_end", None),
                "Assigned value must be a single character string",
                self.context
            )

        try:
            s = list(self.value)
            for idx in indexes[:-1]:
                if not isinstance(idx, Number) or isinstance(idx.value, float):
                    return None, IllegalOperationError(
                        idx.pos_start, idx.pos_end,
                        "Invalid Index Type",
                        self.context
                    )
                
                return None, IllegalOperationError(
                    idx.pos_start, idx.pos_end,
                    "Can't index beyond one dimension in string",
                    self.context
                )

            last_idx = indexes[-1]
            if not isinstance(last_idx, Number) or isinstance(last_idx.value, float):
                return None, RunTimeError(
                    last_idx.pos_start, last_idx.pos_end,
                    "Invalid Index Type",
                    self.context
                )

            try:
                s[last_idx.value] = val.value
                return String("".join(s)).set_context(self.context), None
            except IndexError:
                return None, IndexOutOfBoundsError(
                    last_idx.pos_start, last_idx.pos_end,
                    "Index out of bounds",
                    self.context
                )

        except Exception:
            bad_idx = indexes[-1]
            return None, RunTimeError(
                bad_idx.pos_start, bad_idx.pos_end,
                "Unexpected error in assignIndex",
                self.context
            )

    def copy(self):
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __str__(self):
        return f'{self.value}'

    def __repr__(self):
        return f'"{self.value}"'