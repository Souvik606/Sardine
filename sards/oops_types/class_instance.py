from sards.ast_nodes import SymbolTable
from sards.core.error import AttributeError, IllegalOperationError
from sards.data_types import Number
from sards.user_functions import Function

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
        method_info = self.model.find_method(name)
        if method_info:
            method_node, access_modifier_tok = method_info

            access_level = "open"
            if access_modifier_tok:
                access_level = access_modifier_tok

            method_owner = self.model.find_method_owner(name)

            if access_level == "secret":
                if not self.context or not hasattr(self.context,
                                                   'display_name') or self.context.display_name != method_owner.name:
                    return None, AttributeError(self.pos_start, self.pos_end, f"Cannot access secret method '{name}'",
                                                self.context)

            if access_level == "guarded":
                current_instance = self.context.symbol_table.get("this")
                if not current_instance or not current_instance.model.is_descendant_of(method_owner):
                    return None, AttributeError(self.pos_start, self.pos_end,
                                                f"Cannot access guarded method '{name}' from context '{self.context.display_name}'",
                                                self.context)

            method = Function(
                name, method_node.body_node, [tok.value for tok in method_node.arg_name_toks], False, self
            ).set_context(self.context)
            method.set_pos(method_node.pos_start, method_node.pos_end)
            return method, None

        attr_info = self.model.find_attribute(name)
        if attr_info:
            attr_name, default_node, access_level = attr_info

            attr_owner = self.model.find_attribute_owner(name)

            if access_level == "secret":
                if not self.context or not hasattr(self.context,
                                                   'display_name') or self.context.display_name != attr_owner.name:
                    return None, AttributeError(self.pos_start, self.pos_end,
                                                f"Cannot access secret attribute '{name}'", self.context)

            if access_level == "guarded":
                current_instance = self.context.symbol_table.get("this")
                if not current_instance or not current_instance.model.is_descendant_of(attr_owner):
                    return None, AttributeError(self.pos_start, self.pos_end,
                                                f"Cannot access guarded attribute '{name}' from context '{self.context.display_name}'",
                                                self.context)

            return None, NameError(self.pos_start, self.pos_end, f"Attribute '{name}' was not initialized.",
                                   self.context)

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
                self.pos_start, self.pos_end, 'Cannot apply \'+\' to a model', self.context)

    def subtract(self, other):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'-\' to a model', self.context)

    def multiply(self, other):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'*\' to a model', self.context)

    def divide(self, other):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'/\' to a model', self.context)
    
    def modulus(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'%\' to a model', self.context)

    def floor_divide(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'//\' to a model', self.context)

    def exponent(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'**\' to a model', self.context)

    def get_comparison_eq(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'==\' to a model', self.context)

    def get_comparison_neq(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'!=\' to a model', self.context)

    def get_comparison_lte(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'<=\' to a model', self.context)

    def get_comparison_lt(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'<\' to a model', self.context)

    def get_comparison_gte(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'>=\' to a model', self.context)

    def get_comparison_gt(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'>\' to a model', self.context)

    def and_by(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'and\' to a model', self.context)

    def or_by(self, operand):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'or\' to a model', self.context)

    def not_by(self):
        return None, IllegalOperationError(
                self.pos_start, self.pos_end, 'Cannot apply \'not\' to a model', self.context)

    def is_true(self):
        return Number(1), None

    def __repr__(self):
        return f"<instance of {self.model.name}>"