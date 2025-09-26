from sards.data_types import Number
from sards.core.error import AttributeError, IllegalOperationError
from sards.user_functions import Function
from sards.ast_nodes import SymbolTable

class ModelInstance:
    """
    Represents an instance of a model. Follows the same interface as Number, String, etc.
    """
    def __init__(self, model):
        self.model = model
        self.symbol_table = SymbolTable()
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
        copy = ModelInstance(self.model)
        copy.symbol_table = self.symbol_table
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def get_attr(self, name):
        value = self.symbol_table.get(name)
        if value:
            return value, None

        if name in self.model.method_nodes:
            method_node = self.model.method_nodes[name]
            
            method = Function(
                name,method_node.body_node,
                [tok.value for tok in method_node.arg_name_toks],
                False,self
            ).set_context(self.context)
            method.set_pos(method_node.pos_start, method_node.pos_end)

            return method, None

        return None, AttributeError(
            self.pos_start, self.pos_end,
            f"'{self.model.name}' instance has no attribute '{name}'",
            self.context
        )

    def set_attr(self, name, value):
        self.symbol_table.set(name, value)
        return value, None

    def add(self, other):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'+\' to a model')

    def subtract(self, other):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'-\' to a model')

    def multiply(self, other):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'*\' to a model')

    def divide(self, other):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'/\' to a model')
    
    def modulus(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'%\' to a model')

    def floor_divide(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'//\' to a model')

    def exponent(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'**\' to a model')

    def get_comparison_eq(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'==\' to a model')

    def get_comparison_neq(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'!=\' to a model')

    def get_comparison_lte(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'<=\' to a model')

    def get_comparison_lt(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'<\' to a model')

    def get_comparison_gte(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'>=\' to a model')

    def get_comparison_gt(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'>\' to a model')

    def and_by(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'and\' to a model')

    def or_by(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'or\' to a model')

    def not_by(self):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'not\' to a model')

    def is_true(self):
        return Number(1), None

    def __repr__(self):
        return f"<instance of {self.model.name}>"