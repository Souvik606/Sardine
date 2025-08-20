from .number_type import *


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

    def multiply(self, operand):
        if isinstance(operand, Number):
            return String(self.value * operand.value).set_context(self.context), None

    def is_true(self):
        return len(self.value) > 0
    
    def getByIndex(self, indexes):
        temp = self.value
        try:
            for idx in indexes:
                if isinstance(idx, Number):
                    if not isinstance(temp, str):
                        return None, RuntimeError(
                            idx.pos_start, idx.pos_end,
                            "Can't index a non-string value",
                            self.context
                        )
                    temp = temp[idx.value]
                else:
                    return None, RuntimeError(
                        idx.pos_start, idx.pos_end,
                        "Invalid Index Type",
                        self.context
                    )
            return String(temp).set_context(self.context), None
        except IndexError:
            bad_idx = indexes[-1]
            return None, RuntimeError(
                bad_idx.pos_start, bad_idx.pos_end,
                "Index out of bounds",
                self.context
            )

    def assignIndex(self, indexes, val):
        if not isinstance(val, String) or len(val.value) != 1:
            return None, RuntimeError(
                getattr(val, "pos_start", None),
                getattr(val, "pos_end", None),
                "Assigned value must be a single character string",
                self.context
            )

        try:
            s = list(self.value)
            for idx in indexes[:-1]:
                if not isinstance(idx, Number):
                    return None, RuntimeError(
                        idx.pos_start, idx.pos_end,
                        "Invalid Index Type",
                        self.context
                    )
                
                return None, RuntimeError(
                    idx.pos_start, idx.pos_end,
                    "Can't index beyond one dimension in string",
                    self.context
                )

            last_idx = indexes[-1]
            if not isinstance(last_idx, Number):
                return None, RuntimeError(
                    last_idx.pos_start, last_idx.pos_end,
                    "Invalid Index Type",
                    self.context
                )

            try:
                s[last_idx.value] = val.value
                return String("".join(s)).set_context(self.context), None
            except IndexError:
                return None, RuntimeError(
                    last_idx.pos_start, last_idx.pos_end,
                    "Index out of bounds",
                    self.context
                )

        except Exception:
            bad_idx = indexes[-1]
            return None, RuntimeError(
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
