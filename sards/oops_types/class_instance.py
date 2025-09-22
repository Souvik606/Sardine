from sards.data_types import Number
from sards.core import AttributeError, IllegalOperationError
from sards.core import Context
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
        # Check instance attributes first
        value = self.symbol_table.get(name)
        if value:
            return value, None

        # Check for methods on the model blueprint
        if name in self.model.method_nodes:
            method_node = self.model.method_nodes[name]
            method = Function(
                name,
                method_node.body_node,
                [tok.value for tok in method_node.param_name_toks],
                False
            ).set_context(self.context)

            method_context = Context(f"method {name}", self.context, self.pos_start)
            method_context.symbol_table = SymbolTable(self.context.symbol_table)
            method_context.symbol_table.set("this", self)
            method.set_context(method_context)

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
        return None, IllegalOperationError(self.pos_start, self.pos_end, 'Addition not supported for models',
                                           self.context)

    def subtract(self, other):
        return None, IllegalOperationError(self.pos_start, self.pos_end, 'Subtraction not supported for models',
                                           self.context)

    def multiply(self, other):
        return None, IllegalOperationError(self.pos_start, self.pos_end, 'Multiplication not supported for models',
                                           self.context)


    def is_true(self):
        return Number(1), None

    def __repr__(self):
        return f"<instance of {self.model.name}>"