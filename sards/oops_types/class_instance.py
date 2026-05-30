from sards.ast_nodes import SymbolTable
from sards.core.error import AttributeError, IllegalOperationError, fuzzy_match
from sards.data_types import Number
from sards.user_functions import Function


# --------------------------------------------------------------------------
# Operator-method name mapping
# --------------------------------------------------------------------------
BINARY_OP_METHODS = {
    'add':               '__add__',
    'subtract':          '__sub__',
    'multiply':          '__mul__',
    'divide':            '__div__',
    'modulus':           '__mod__',
    'floor_divide':      '__floordiv__',
    'exponent':          '__pow__',
    'bitwise_and':       '__and__',
    'bitwise_or':        '__or__',
    'bitwise_xor':       '__xor__',
    'lshift':            '__lshift__',
    'rshift':            '__rshift__',
    'get_comparison_eq': '__eq__',
    'get_comparison_neq':'__neq__',
    'get_comparison_lt': '__lt__',
    'get_comparison_lte':'__lte__',
    'get_comparison_gt': '__gt__',
    'get_comparison_gte':'__gte__',
    'and_by':            '__land__',
    'or_by':             '__lor__',
}

UNARY_OP_METHODS = {
    'not_by':      '__not__',
    'bitwise_not': '__bitnot__',
}

OP_SYMBOLS = {
    'add': '+', 'subtract': '-', 'multiply': '*', 'divide': '/',
    'modulus': '%', 'floor_divide': '//', 'exponent': '**',
    'bitwise_and': '&', 'bitwise_or': '|', 'bitwise_xor': '^',
    'lshift': '<<', 'rshift': '>>',
    'get_comparison_eq': '==', 'get_comparison_neq': '!=',
    'get_comparison_lt': '<',  'get_comparison_lte': '<=',
    'get_comparison_gt': '>',  'get_comparison_gte': '>=',
    'and_by': 'and', 'or_by': 'or',
    'not_by': 'not', 'bitwise_not': '~',
}


class ModelInstance:
    """
    Represents an instance of a model. Follows the same interface as Number, String, etc.

    Operator Overloading
    --------------------
    Define special methods inside a `model` to overload operators, exactly like C++:

        model Vec2 {
            open attr <x, y>

            init(x, y) { x: x, y: y }

            method __add__(other) {
                yield Vec2(x + other.x, y + other.y)
            }
            method __sub__(other) {
                yield Vec2(x - other.x, y - other.y)
            }
            method __mul__(other) {
                yield Vec2(x * other.x, y * other.y)
            }
            method __eq__(other) {
                yield (x == other.x) and (y == other.y)
            }
            method __lt__(other) {
                yield (x < other.x) and (y < other.y)
            }
            method __neg__() {
                yield Vec2(-x, -y)
            }
            method __not__() {
                yield (x == 0) and (y == 0)
            }
        }

    Full list of overloadable special method names:
      Binary  : __add__  __sub__  __mul__  __div__  __mod__  __floordiv__  __pow__
                __and__  __or__   __xor__  __lshift__ __rshift__
                __eq__   __neq__  __lt__   __lte__   __gt__   __gte__
                __land__ __lor__
      Unary   : __neg__  __not__  __bitnot__
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

    def get_attr(self, name, calling_context):
        value = self.symbol_table.get(name)

        if value:
            attr_info = self.model.find_attribute(name)
            if attr_info:
                _, _, access_level = attr_info
                attr_owner = self.model.find_attribute_owner(name)

                if access_level == "secret":
                    current_instance = calling_context.symbol_table.get("this") if (calling_context and getattr(calling_context, 'symbol_table', None)) else None
                    if not current_instance or current_instance.model != attr_owner:
                        return None, AttributeError(self.pos_start, self.pos_end,
                                                    f"Cannot access secret attribute '{name}'", calling_context,
                                                    hint="'secret' attributes can only be accessed within the model that defines them.")

                if access_level == "guarded":
                    current_instance = calling_context.symbol_table.get("this") if (calling_context and getattr(calling_context, 'symbol_table', None)) else None
                    if not current_instance or not current_instance.model.is_descendant_of(attr_owner):
                        return None, AttributeError(self.pos_start, self.pos_end,
                                                    f"Cannot access guarded attribute '{name}'", calling_context,
                                                    hint="'guarded' attributes can only be accessed within the model or its subclasses.")

            return value, None

        method_info = self.model.find_method(name)

        if method_info:
            method_node, access_modifier_tok = method_info

            access_level = "open"
            if access_modifier_tok:
                access_level = access_modifier_tok

            method_owner = self.model.find_method_owner(name)
            caller_class = calling_context.owner_class if calling_context else None

            if access_level == "secret":
                if not caller_class or caller_class != method_owner:
                    return None, AttributeError(self.pos_start, self.pos_end, f"Cannot access secret method '{name}'",
                                                calling_context,
                                                hint="'secret' methods can only be called from within the model that defines them.")

            if access_level == "guarded":
                if not caller_class or not caller_class.is_descendant_of(method_owner):
                    return None, AttributeError(self.pos_start, self.pos_end, f"Cannot access guarded method '{name}'",
                                                calling_context,
                                                hint="'guarded' methods can only be called from within the model or its subclasses.")

            method = Function(
                name,
                method_node.body_node,
                method_node.param_nodes,
                False,
                self,
                owner_class=method_owner
            ).set_context(self.context)
            method.set_pos(method_node.pos_start, method_node.pos_end)
            return method, None

        # Build a hint using fuzzy match on all known attributes + methods
        _all_names = list(self.symbol_table.symbols.keys()) + list(self.model.method_nodes.keys())
        _suggestion = fuzzy_match(name, _all_names)
        _hint = f"Did you mean '{_suggestion}'?" if _suggestion else f"Check the definition of model '{self.model.name}' for available attributes and methods."
        return None, AttributeError(
            self.pos_start, self.pos_end,
            f"'{self.model.name}' instance has no attribute '{name}'",
            self.context,
            hint=_hint
        )

    def set_attr(self, name, value):
        self.symbol_table.set(name, value)
        return value, None

    # ------------------------------------------------------------------
    # Internal helper: call a user-defined operator method
    # Returns (result, error) where result is None if method not defined.
    # ------------------------------------------------------------------

    def _call_op_method(self, method_name, args):
        """Look up method_name on this model and invoke it with args."""
        method_info = self.model.find_method(method_name)
        if method_info is None:
            return None, None   # not found — caller decides what to do

        from sards.core import RunTimeResult

        method_node, _ = method_info
        func = Function(
            method_name,
            method_node.body_node,
            method_node.param_nodes,
            False,
            self
        ).set_context(self.context)
        func.set_pos(method_node.pos_start, method_node.pos_end)

        res = RunTimeResult()
        result = res.register(func.execute(args, {}, call_context=self.context))
        if res.error:
            return None, res.error
        return result, None

    def _binary_op(self, op_name, other):
        """Dispatch a binary operator, first to the user-defined special method."""
        method_name = BINARY_OP_METHODS.get(op_name)
        if method_name:
            result, error = self._call_op_method(method_name, [other])
            if error:
                return None, error
            if result is not None:
                return result, None

        symbol = OP_SYMBOLS.get(op_name, op_name)
        user_method = BINARY_OP_METHODS.get(op_name, '?')
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            f"Operator '{symbol}' is not defined for '{self.model.name}'. "
            f"Define 'method {user_method}(other) {{...}}' inside the model to enable it.",
            self.context
        )

    def _unary_op(self, op_name):
        """Dispatch a unary operator to the user-defined special method."""
        method_name = UNARY_OP_METHODS.get(op_name)
        if method_name:
            result, error = self._call_op_method(method_name, [])
            if error:
                return None, error
            if result is not None:
                return result, None

        symbol = OP_SYMBOLS.get(op_name, op_name)
        user_method = UNARY_OP_METHODS.get(op_name, '?')
        return None, IllegalOperationError(
            self.pos_start, self.pos_end,
            f"Operator '{symbol}' is not defined for '{self.model.name}'. "
            f"Define 'method {user_method}() {{...}}' inside the model to enable it.",
            self.context
        )

    # ------------------------------------------------------------------
    # Binary operators — each delegates to _binary_op
    # ------------------------------------------------------------------

    def add(self, other):
        return self._binary_op('add', other)

    def subtract(self, other):
        return self._binary_op('subtract', other)

    def divide(self, other):
        return self._binary_op('divide', other)

    def modulus(self, other):
        return self._binary_op('modulus', other)

    def floor_divide(self, other):
        return self._binary_op('floor_divide', other)

    def exponent(self, other):
        return self._binary_op('exponent', other)

    def bitwise_and(self, other):
        return self._binary_op('bitwise_and', other)

    def bitwise_or(self, other):
        return self._binary_op('bitwise_or', other)

    def bitwise_xor(self, other):
        return self._binary_op('bitwise_xor', other)

    def lshift(self, other):
        return self._binary_op('lshift', other)

    def rshift(self, other):
        return self._binary_op('rshift', other)

    def get_comparison_eq(self, other):
        return self._binary_op('get_comparison_eq', other)

    def get_comparison_neq(self, other):
        return self._binary_op('get_comparison_neq', other)

    def get_comparison_lt(self, other):
        return self._binary_op('get_comparison_lt', other)

    def get_comparison_lte(self, other):
        return self._binary_op('get_comparison_lte', other)

    def get_comparison_gt(self, other):
        return self._binary_op('get_comparison_gt', other)

    def get_comparison_gte(self, other):
        return self._binary_op('get_comparison_gte', other)

    def and_by(self, other):
        return self._binary_op('and_by', other)

    def or_by(self, other):
        return self._binary_op('or_by', other)

    def multiply(self, other):
        """
        Handles both  obj * other  AND unary  -obj.
        The interpreter converts unary minus to  obj.multiply(Number(-1)).
        Priority: if other is Number(-1), try __neg__ FIRST to avoid
        passing a raw Number into a user-defined __mul__ that expects
        an instance (e.g. accessing other.x would crash).
        """
        # Unary-minus case: detect Number(-1) and try __neg__ first
        if isinstance(other, Number) and other.value == -1:
            neg_result, neg_error = self._call_op_method('__neg__', [])
            if neg_result is not None:
                return neg_result, neg_error
            if neg_error:
                return None, neg_error
            # __neg__ not defined — fall through to try __mul__

        # Normal multiplication (also fallback for unary minus when __neg__ absent)
        result, error = self._call_op_method('__mul__', [other])
        if result is not None:
            return result, None
        if error:
            return None, error

        # Neither found — produce standard error
        return self._binary_op('multiply', other)

    # ------------------------------------------------------------------
    # Unary operators
    # ------------------------------------------------------------------

    def not_by(self):
        return self._unary_op('not_by')

    def bitwise_not(self):
        return self._unary_op('bitwise_not')

    # ------------------------------------------------------------------
    # Truthiness
    # ------------------------------------------------------------------

    def is_true(self):
        return Number(1), None

    def __repr__(self):
        return f"<instance of {self.model.name}>"