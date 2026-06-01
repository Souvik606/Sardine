from sards.data_types.number_type import Boolean

class Null:
    def __init__(self):
        self.pos_start = None
        self.pos_end = None
        self.context = None

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def copy(self):
        copy = Null()
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def is_true(self):
        return Boolean(False).set_context(self.context), None

    def __repr__(self):
        return "Null"

    def get_comparison_eq(self, operand):
        return Boolean(isinstance(operand, Null)).set_context(self.context), None

    def get_comparison_neq(self, operand):
        return Boolean(not isinstance(operand, Null)).set_context(self.context), None
