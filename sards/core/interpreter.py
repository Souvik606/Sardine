"""
interpreter.py

This module defines the components needed for interpreting an abstract syntax tree (AST).
It includes classes for handling runtime context, execution results, and evaluating expressions.

Classes:
- Context: Maintains execution context (e.g., scope, parent context).
- RunTimeResult: Stores the result of an evaluation, including errors.
- Interpreter: Evaluates AST nodes and executes operations.
"""

import os

from sards.ast_nodes import SymbolTable
from sards.data_types import Number, String, List, Dict, Module

from .constants import (T_PLUS, T_MINUS, T_MUL, T_DIVIDE, T_MODULUS, T_FLOOR, T_BITAND, T_BITXOR, T_BITOR, T_BITNOT, T_EXP, T_EE,
                        T_LSHIFT, T_RSHIFT, T_NEQ, T_GT, T_GTE, T_LT, T_LTE, T_KEYWORD, ERROR_TYPES)
from .error import (
    NameError, NotImplementedError, InvalidErrorTypeError, RunTimeError,
    IllegalOperationError, IndexOutOfBoundsError, ArgumentError,
    DivisionByZeroError, ModuleError, AttributeError, DictKeyError,
    TypeError, ValueError, StackDepthExceededError,
    fuzzy_match
)

# Global module cache: abs_path -> Module instance
_MODULE_CACHE = {}

# Standard library directory (sibling folder 'stdlib' next to sards/)
_STDLIB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stdlib')

ERROR_CLASS_MAP = {
    "RunTimeError": RunTimeError,
    "IllegalOperationError": IllegalOperationError,
    "DivisionByZeroError": DivisionByZeroError,
    "IndexOutOfBoundsError": IndexOutOfBoundsError,
    "NameError": NameError,
    "ArgumentError": ArgumentError,
    "NotImplementedError": NotImplementedError,
    "InvalidErrorTypeError": InvalidErrorTypeError,
    "ModuleError": ModuleError,
    "AttributeError": AttributeError,
    "DictKeyError": DictKeyError,
    "TypeError": TypeError,
    "ValueError": ValueError,
    "StackDepthExceededError": StackDepthExceededError,
}


class Context: # pylint: disable=R0903
    """
    Represents the execution context of a program.

    Attributes:
    - display_name (str): The name of the current execution context.
    - parent (Context, optional): The parent context (e.g., caller function).
    - parent_entry_pos (optional): The position in the parent where this context was entered.
    """

    def __init__(self, display_name, parent=None, parent_entry_pos=None,owner_class=None):
        """
        Initializes a new execution context.

        Parameters:
        - display_name (str): The name of the execution context.
        - parent (Context, optional): The parent execution context.
        - parent_entry_pos (optional): The entry position in the parent context.
        """
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None
        self.owner_class=owner_class
        self.depth = (parent.depth + 1) if parent else 1


class RunTimeResult:
    """
    Represents the result of evaluating an AST node.

    Attributes:
    - value (any): The computed value.
    - error (Exception, optional): The error encountered, if any.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.value = None
        self.error = None
        self.func_return_value = None
        self.loop_continue = False
        self.loop_or_switch_break = False

    def register(self, res):
        self.error = res.error if res.error else None
        self.func_return_value = res.func_return_value
        self.loop_continue = res.loop_continue
        self.loop_or_switch_break = res.loop_or_switch_break
        return res.value

    def success(self, value):
        self.reset()
        self.value = value
        return self

    def success_return(self, value):
        self.reset()
        self.func_return_value = value
        return self

    def success_continue(self):
        self.reset()
        self.loop_continue = True
        return self

    def success_break(self):
        self.reset()
        self.loop_or_switch_break = True
        return self

    def failure(self, error):
        self.reset()
        self.error = error
        return self

    def should_return(self):
        return (self.error or
                self.func_return_value or
                self.loop_continue or
                self.loop_or_switch_break)


class Interpreter:
    """
    Interprets an abstract syntax tree (AST) by visiting its nodes and evaluating expressions.

    Methods:
    - visit(node, context): Determines the appropriate visit method for a node.
    - visit_NumberNode(node, context): Evaluates a number node.
    - visit_BinaryOperationNode(node, context): Evaluates binary operations (+, -, *, /).
    - visit_UnaryOperationNode(node, context): Evaluates unary operations (-).
    """

    def visit(self, node, context):
        """
        Visits an AST node and executes the corresponding evaluation method.

        Parameters:
        - node (AST Node): The node to visit.
        - context (Context): The execution context.

        Returns:
        - RunTimeResult: The evaluation result.
        """
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)

    def no_visit_method(self, node, context):
        """
        Handles cases where no visit method is defined for a node type.

        Parameters:
        - node (AST Node): The unrecognized node.
        - context (Context): The execution context.

        Raises:
        - Exception: Indicates that the node type is unsupported.
        """
        return RunTimeResult().failure(NotImplementedError(node.pos_end,node.pos_end,f'No visit_{type(node).__name__} method defined',context))

    def visit_ModelNode(self, node, context):
        from sards.ast_nodes import FunctionDefinitionNode, InitNode, AttrNode
        from sards.oops_types import Model

        res = RunTimeResult()
        model_name = node.name_tok.value

        parent_models = []
        if node.parent_name_toks:
            for parent_tok in node.parent_name_toks:
                parent_name = parent_tok.value
                parent = context.symbol_table.get(parent_name)
                if not parent:
                    _candidates = list(context.symbol_table.symbols.keys())
                    _suggestion = fuzzy_match(parent_name, _candidates)
                    _hint = f"Did you mean '{_suggestion}'?" if _suggestion else "Make sure the parent model is defined before this model."
                    return res.failure(NameError(
                        parent_tok.pos_start, parent_tok.pos_end,
                        f"Parent class '{parent_name}' is not defined", context,
                        hint=_hint
                    ))
                if not isinstance(parent, Model):
                    return res.failure(TypeError(
                        parent_tok.pos_start, parent_tok.pos_end,
                        f"'{parent_name}' is not a class and cannot be inherited from", context,
                        hint=f"Only values defined with 'model' can be inherited from."
                    ))

                parent_models.append(parent)

        method_nodes = {}
        init_node = None
        attr_nodes = []

        for member in node.body_nodes:
            if isinstance(member, FunctionDefinitionNode):
                access_level = "open"
                if member.access_modifier_tok:
                    access_level = member.access_modifier_tok.value

                method_nodes[member.var_name_tok.value] = (member, access_level)
            elif isinstance(member, InitNode):
                init_node = member
            elif isinstance(member, AttrNode):
                access_level = "open"
                if member.access_modifier_tok:
                    access_level = member.access_modifier_tok.value

                for name_tok, default_node in member.declarations:
                    attr_nodes.append((name_tok.value, default_node, access_level))

        model = Model(model_name, attr_nodes, init_node, method_nodes, parent_models)

        model.set_context(context)
        model.set_pos(node.pos_start, node.pos_end)

        context.symbol_table.set(model_name, model)
        return res.success(model)

    def visit_AttrAccessNode(self, node, context):
        from sards.user_functions import Function
        from sards.oops_types import Model

        res = RunTimeResult()

        object_val = res.register(self.visit(node.object_node, context))
        if res.should_return():
            return res

        attr_name = node.attr_name_tok.value

        if not hasattr(object_val, 'get_attr'):
            return res.failure(AttributeError(
                node.object_node.pos_start, node.object_node.pos_end,
                f"'{type(object_val).__name__}' object has no attribute '{attr_name}'",
                context,
                hint=f"Only model instances and modules support attribute access with '.'"
            ))

        value, error = object_val.get_attr(attr_name, context)

        if error:
            return res.failure(error)

        value = value.copy()
        value.set_pos(node.pos_start, node.pos_end)

        if not isinstance(value, Function) and not isinstance(value, Model):
            value.set_context(context)

        return res.success(value)

    def visit_TryNode(self, node, context):
        res = RunTimeResult()

        try_result = res.register(self.visit(node.body_node, context))

        if not res.error:
            if node.clean_node:
                res.register(self.visit(node.clean_node.body_node, context))
                if res.should_return(): return res
            return res.success(try_result)

        error = res.error
        handled = False

        for trap_node in node.trap_nodes:
            if trap_node.error_type and trap_node.error_type.value not in ERROR_CLASS_MAP:
                return res.failure(
                    InvalidErrorTypeError(
                        trap_node.pos_start, trap_node.pos_end,
                        f"'{trap_node.error_type}' is not a valid error type",
                        context
                    )
                )

            matches = False
            if trap_node.error_type is None:
                matches = True
            else:
                caught_cls = ERROR_CLASS_MAP[trap_node.error_type.value]
                actual_cls = type(error)
                if issubclass(actual_cls, caught_cls):
                    matches = True

            # Match error (type check or wildcard)
            if matches:
                # Create a fresh context for the trap block
                trap_context = Context("<trap block>", context, trap_node.pos_start)
                trap_context.symbol_table = SymbolTable(parent=context.symbol_table)

                # Bind error variable if provided
                if trap_node.error_name:
                    from sards.oops_types.class_type import Model
                    from sards.oops_types.class_instance import ModelInstance
                    from sards.data_types import String

                    exception_model = Model(error.error_name, [], None, {})
                    e_instance = ModelInstance(exception_model)
                    e_instance.set_attr("type", String(error.error_name))
                    e_instance.set_attr("message", String(error.details))
                    e_instance.set_attr("traceback", String(error.to_string()))

                    trap_context.symbol_table.set(
                        trap_node.error_name.value,
                        e_instance
                        .set_pos(trap_node.pos_start, trap_node.pos_end)
                        .set_context(trap_context)
                    )

                # Run the trap body
                trap_result = res.register(self.visit(trap_node.body_node, trap_context))
                if res.error:
                    return res
                handled = True
                break

        # Always run clean if exists
        if node.clean_node:
            res.register(self.visit(node.clean_node.body_node, context))
            if res.should_return(): return res

        if handled:
            return res.success(None)

        # If not handled -> propagate error
        return res.failure(error)

    def visit_ListNode(self, node, context):
        res = RunTimeResult()
        elements = []

        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))
            if res.should_return():
                return res

        return (res.success(List(elements)
                            .set_context(context)
                            .set_pos(node.pos_start, node.pos_end)))

    def visit_DictNode(self, node, context):
        res = RunTimeResult()
        elements = []

        for key_node, value_node in node.keyval_nodes:
            key = res.register(self.visit(key_node, context))
            if res.should_return():
                return res
                
            if not isinstance(key, (Number, String)):
                return res.failure(
                    IllegalOperationError(
                        key_node.pos_start,
                        key_node.pos_end,
                        "Dictionary keys must be numbers or strings",
                        context
                    )
                )

            value = res.register(self.visit(value_node, context))
            if res.should_return():
                return res

            elements.append((key, value))

        return res.success(
            Dict(elements)
                .set_context(context)
                .set_pos(node.pos_start, node.pos_end)
        )

    def visit_StringNode(self, node, context):
        return RunTimeResult().success(
            String(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_FStringNode(self, node, context):
        """
        Evaluate a $"..." interpolated string.

        Each ('literal', text) part is kept as-is.
        Each ('expr', ast_node) part is evaluated and converted to str.
        All parts are concatenated into a single String value.
        """
        res = RunTimeResult()
        result_str = ''

        for kind, part in node.parts:
            if kind == 'literal':
                result_str += part
            else:
                # 'expr' — evaluate the sub-expression
                value = res.register(self.visit(part, context))
                if res.should_return():
                    return res
                try:
                    str_val = str(value)
                except (ValueError, OverflowError, MemoryError):
                    try:
                        str_val = f"{float(value.value):.4e}" if hasattr(value, 'value') else "INF"
                    except:
                        str_val = "INF"
                result_str += str_val

        return res.success(
            String(result_str).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_ListComprehensionNode(self, node, context):
        """
        Evaluate a list comprehension.

        Supports two loop forms:
          - 'Cycle' : numeric range  [expr Cycle i = start : end (: step)? (when cond)?]
          - 'trace' : collection     [expr trace x <- coll (when cond)?]

        An isolated child context is used so the loop variable does not
        leak into the surrounding scope.
        """
        from sards.ast_nodes import SymbolTable
        res = RunTimeResult()
        elements = []

        # Create a child scope for the comprehension variable(s)
        comp_context = Context('<comprehension>', context, node.pos_start)
        comp_context.symbol_table = SymbolTable(parent=context.symbol_table)

        if node.loop_type == 'Cycle':
            start_val = res.register(self.visit(node.start_node, context))
            if res.should_return(): return res
            end_val = res.register(self.visit(node.end_node, context))
            if res.should_return(): return res

            if node.step_node:
                step_val = res.register(self.visit(node.step_node, context))
                if res.should_return(): return res
            else:
                step_val = Number(1)

            if not isinstance(start_val, Number):
                return res.failure(TypeError(
                    node.start_node.pos_start, node.start_node.pos_end,
                    f"Comprehension loop start value must be a Number, not '{type(start_val).__name__}'",
                    context
                ))

            if not isinstance(end_val, Number):
                return res.failure(TypeError(
                    node.end_node.pos_start, node.end_node.pos_end,
                    f"Comprehension loop end value must be a Number, not '{type(end_val).__name__}'",
                    context
                ))

            if not isinstance(step_val, Number):
                return res.failure(TypeError(
                    node.step_node.pos_start if node.step_node else node.pos_start,
                    node.step_node.pos_end if node.step_node else node.pos_end,
                    f"Comprehension loop step value must be a Number, not '{type(step_val).__name__}'",
                    context
                ))

            if step_val.value == 0:
                return res.failure(IllegalOperationError(
                    node.step_node.pos_start if node.step_node else node.pos_start,
                    node.step_node.pos_end if node.step_node else node.pos_end,
                    "Comprehension loop step cannot be 0",
                    context
                ))

            i = start_val.value
            var_name = node.var_name_tok.value

            if step_val.value >= 0:
                condition = lambda: i <= end_val.value
            else:
                condition = lambda: i >= end_val.value

            iterations = 0
            while condition():
                iterations += 1
                from sards.core import constants
                if not constants.UNBOUNDED_MODE and iterations >= 200000:
                    from sards.core.error import ValueError as SardineValueError
                    return res.failure(SardineValueError(node.pos_start, node.pos_end, "Comprehension execution limit exceeded (max 100,000 iterations)", context))
                if len(elements) >= 100000:
                    from sards.core.error import ValueError as SardineValueError
                    return res.failure(SardineValueError(node.pos_start, node.pos_end, "Comprehension execution limit exceeded (max 100,000 items)", context))
                comp_context.symbol_table.set(var_name, Number(i))
                i += step_val.value

                # Optional filter
                if node.condition_node:
                    cond_val = res.register(self.visit(node.condition_node, comp_context))
                    if res.should_return(): return res
                    truthy, _ = cond_val.is_true()
                    if not truthy.value:
                        continue

                elem = res.register(self.visit(node.expr_node, comp_context))
                if res.should_return(): return res
                elements.append(elem)

        elif node.loop_type == 'trace':
            collection = res.register(self.visit(node.collection_node, context))
            if res.should_return(): return res

            # Build iterable items (same logic as visit_ForEachLoopNode)
            num_vars = len(node.var_name_tokens)

            if isinstance(collection, List):
                items = collection.elements
            elif isinstance(collection, String):
                items = [String(ch).set_context(context).set_pos(
                    node.pos_start, node.pos_end) for ch in collection.value]
            else:
                return res.failure(IllegalOperationError(
                    node.pos_start, node.pos_end,
                    f"'{type(collection).__name__}' object is not iterable in comprehension",
                    context))

            iterations = 0
            for item in items:
                iterations += 1
                from sards.core import constants
                if not constants.UNBOUNDED_MODE and iterations >= 200000:
                    from sards.core.error import ValueError as SardineValueError
                    return res.failure(SardineValueError(node.pos_start, node.pos_end, "Comprehension execution limit exceeded (max 100,000 iterations)", context))
                if len(elements) >= 100000:
                    from sards.core.error import ValueError as SardineValueError
                    return res.failure(SardineValueError(node.pos_start, node.pos_end, "Comprehension execution limit exceeded (max 100,000 items)", context))
                if num_vars == 1:
                    comp_context.symbol_table.set(node.var_name_tokens[0].value, item)
                else:
                    if not isinstance(item, List) or len(item.elements) != num_vars:
                        return res.failure(IllegalOperationError(
                            node.pos_start, node.pos_end,
                            f"Cannot unpack item into {num_vars} variables in comprehension",
                            context))
                    for idx, var_tok in enumerate(node.var_name_tokens):
                        comp_context.symbol_table.set(var_tok.value, item.elements[idx])

                # Optional filter
                if node.condition_node:
                    cond_val = res.register(self.visit(node.condition_node, comp_context))
                    if res.should_return(): return res
                    truthy, _ = cond_val.is_true()
                    if not truthy.value:
                        continue

                elem = res.register(self.visit(node.expr_node, comp_context))
                if res.should_return(): return res
                elements.append(elem)

        return res.success(
            List(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_DictComprehensionNode(self, node, context):
        """
        Evaluate a dict comprehension.

        Supports two loop forms:
          - 'Cycle' : numeric range  {key:val Cycle i = start : end (: step)? (when cond)?}
          - 'trace' : collection     {key:val trace x <- coll (when cond)?}
        """
        from sards.ast_nodes import SymbolTable
        res = RunTimeResult()
        pairs = []   # list of (key, value) tuples

        # Child scope for loop variable(s)
        comp_context = Context('<dict-comprehension>', context, node.pos_start)
        comp_context.symbol_table = SymbolTable(parent=context.symbol_table)

        if node.loop_type == 'Cycle':
            start_val = res.register(self.visit(node.start_node, context))
            if res.should_return(): return res
            end_val = res.register(self.visit(node.end_node, context))
            if res.should_return(): return res

            if node.step_node:
                step_val = res.register(self.visit(node.step_node, context))
                if res.should_return(): return res
            else:
                step_val = Number(1)

            if not isinstance(start_val, Number):
                return res.failure(TypeError(
                    node.start_node.pos_start, node.start_node.pos_end,
                    f"Comprehension loop start value must be a Number, not '{type(start_val).__name__}'",
                    context
                ))

            if not isinstance(end_val, Number):
                return res.failure(TypeError(
                    node.end_node.pos_start, node.end_node.pos_end,
                    f"Comprehension loop end value must be a Number, not '{type(end_val).__name__}'",
                    context
                ))

            if not isinstance(step_val, Number):
                return res.failure(TypeError(
                    node.step_node.pos_start if node.step_node else node.pos_start,
                    node.step_node.pos_end if node.step_node else node.pos_end,
                    f"Comprehension loop step value must be a Number, not '{type(step_val).__name__}'",
                    context
                ))

            if step_val.value == 0:
                return res.failure(IllegalOperationError(
                    node.step_node.pos_start if node.step_node else node.pos_start,
                    node.step_node.pos_end if node.step_node else node.pos_end,
                    "Comprehension loop step cannot be 0",
                    context
                ))

            i = start_val.value
            var_name = node.var_name_tok.value

            if step_val.value >= 0:
                condition = lambda: i <= end_val.value
            else:
                condition = lambda: i >= end_val.value

            iterations = 0
            while condition():
                iterations += 1
                from sards.core import constants
                if not constants.UNBOUNDED_MODE and iterations >= 200000:
                    from sards.core.error import ValueError as SardineValueError
                    return res.failure(SardineValueError(node.pos_start, node.pos_end, "Comprehension execution limit exceeded (max 100,000 iterations)", context))
                if len(pairs) >= 100000:
                    from sards.core.error import ValueError as SardineValueError
                    return res.failure(SardineValueError(node.pos_start, node.pos_end, "Comprehension execution limit exceeded (max 100,000 items)", context))
                comp_context.symbol_table.set(var_name, Number(i))
                i += step_val.value

                if node.condition_node:
                    cond_val = res.register(self.visit(node.condition_node, comp_context))
                    if res.should_return(): return res
                    truthy, _ = cond_val.is_true()
                    if not truthy.value:
                        continue

                key = res.register(self.visit(node.key_node, comp_context))
                if res.should_return(): return res
                val = res.register(self.visit(node.val_node, comp_context))
                if res.should_return(): return res
                pairs.append((key, val))

        elif node.loop_type == 'trace':
            collection = res.register(self.visit(node.collection_node, context))
            if res.should_return(): return res

            num_vars = len(node.var_name_tokens)

            if isinstance(collection, List):
                items = collection.elements
            elif isinstance(collection, String):
                items = [String(ch).set_context(context).set_pos(
                    node.pos_start, node.pos_end) for ch in collection.value]
            else:
                return res.failure(IllegalOperationError(
                    node.pos_start, node.pos_end,
                    f"'{type(collection).__name__}' object is not iterable in dict comprehension",
                    context))

            iterations = 0
            for item in items:
                iterations += 1
                from sards.core import constants
                if not constants.UNBOUNDED_MODE and iterations >= 200000:
                    from sards.core.error import ValueError as SardineValueError
                    return res.failure(SardineValueError(node.pos_start, node.pos_end, "Comprehension execution limit exceeded (max 100,000 iterations)", context))
                if len(pairs) >= 100000:
                    from sards.core.error import ValueError as SardineValueError
                    return res.failure(SardineValueError(node.pos_start, node.pos_end, "Comprehension execution limit exceeded (max 100,000 items)", context))
                if num_vars == 1:
                    comp_context.symbol_table.set(node.var_name_tokens[0].value, item)
                else:
                    if not isinstance(item, List) or len(item.elements) != num_vars:
                        return res.failure(IllegalOperationError(
                            node.pos_start, node.pos_end,
                            f"Cannot unpack into {num_vars} variables in dict comprehension",
                            context))
                    for idx, var_tok in enumerate(node.var_name_tokens):
                        comp_context.symbol_table.set(var_tok.value, item.elements[idx])

                if node.condition_node:
                    cond_val = res.register(self.visit(node.condition_node, comp_context))
                    if res.should_return(): return res
                    truthy, _ = cond_val.is_true()
                    if not truthy.value:
                        continue

                key = res.register(self.visit(node.key_node, comp_context))
                if res.should_return(): return res
                val = res.register(self.visit(node.val_node, comp_context))
                if res.should_return(): return res
                pairs.append((key, val))

        return res.success(
            Dict(pairs).set_context(context).set_pos(node.pos_start, node.pos_end)
        )


    def visit_FunctionDefinitionNode(self, node, context):
        from sards.user_functions import Function
        res = RunTimeResult()

        func_name = node.var_name_tok.value if node.var_name_tok else None
        body_node = node.body_node
        param_nodes = node.param_nodes
        func_value = (Function(func_name, body_node, param_nodes, node.auto_return)
                      .set_context(context)
                      .set_pos(node.pos_start, node.pos_end))

        if node.var_name_tok:
            context.symbol_table.set(func_name, func_value)

        return res.success(func_value)

    def visit_FunctionCallNode(self, node, context):
        from sards.user_functions import Function
        from sards.oops_types import Model

        res = RunTimeResult()
        pos_args = []
        kw_args = {}

        call_value = res.register(self.visit(node.call_node, context))
        if res.should_return():
            return res
        call_value = call_value.copy().set_pos(node.pos_start, node.pos_end)

        if not hasattr(call_value, 'execute'):
            return res.failure(IllegalOperationError(
                node.pos_start, node.pos_end,
                f"'{type(call_value).__name__}' object is not callable",
                context,
                hint="Only functions and models (constructors) can be called with '()'."
            ))

        for arg_node in node.positional_param_nodes:
            pos_args.append(res.register(self.visit(arg_node, context)))
            if res.should_return():
                return res

        for name_tok, value_node in node.keyword_param_nodes:
            arg_name = name_tok.value
            arg_value = res.register(self.visit(value_node, context))
            if res.should_return():
                return res
            kw_args[arg_name] = arg_value

        return_value = res.register(call_value.execute(pos_args, kw_args, call_context=context))
        if res.should_return():
            return res

        return_value = return_value.copy().set_pos(node.pos_start, node.pos_end)
        if not isinstance(return_value, Function) and not isinstance(return_value, Model):
            return_value.set_context(context)

        return res.success(return_value)

    def visit_WhileNode(self, node, context):
        res = RunTimeResult()
        elements = []
        iterations = 0

        while True:
            iterations += 1
            from sards.core import constants
            if not constants.UNBOUNDED_MODE and iterations >= 200000:
                from sards.core.error import ValueError as SardineValueError
                return res.failure(SardineValueError(node.pos_start, node.pos_end, "Loop execution limit exceeded (max 100,000 iterations)", context))
            condition = res.register(self.visit(node.condition_node, context))
            if res.should_return():
                return res
            cond, error = condition.is_true()
            if not cond.value:
                break

            value = res.register(self.visit(node.body_node, context))
            if (res.should_return() and
                not res.loop_or_switch_break and
                not res.loop_continue):
                return res

            if res.loop_continue:
                continue
            if res.loop_or_switch_break:
                break

            if not node.return_null:
                if len(elements) < 100000:
                    elements.append(value)
                elif not constants.UNBOUNDED_MODE:
                    from sards.core.error import ValueError as SardineValueError
                    return res.failure(SardineValueError(node.pos_start, node.pos_end, "Loop execution result accumulation limit exceeded (max 100,000 items)", context))

        return res.success(
            Number(0) if node.return_null else (List(elements).set_context(context)
                                                .set_pos(node.pos_start, node.pos_end)))

    def visit_ForNode(self, node, context):
        res = RunTimeResult()
        elements = []

        start_value = res.register(self.visit(node.start_value_node, context))
        if res.should_return():
            return res

        end_value = res.register(self.visit(node.end_value_node, context))
        if res.should_return():
            return res

        if node.step_value_node:
            step_value = res.register(self.visit(node.step_value_node, context))
            if res.should_return():
                return res
        else:
            step_value = Number(1)

        if not isinstance(start_value, Number):
            return res.failure(TypeError(
                node.start_value_node.pos_start, node.start_value_node.pos_end,
                f"Loop start value must be a Number, not '{type(start_value).__name__}'",
                context
            ))

        if not isinstance(end_value, Number):
            return res.failure(TypeError(
                node.end_value_node.pos_start, node.end_value_node.pos_end,
                f"Loop end value must be a Number, not '{type(end_value).__name__}'",
                context
            ))

        if not isinstance(step_value, Number):
            return res.failure(TypeError(
                node.step_value_node.pos_start if node.step_value_node else node.pos_start,
                node.step_value_node.pos_end if node.step_value_node else node.pos_end,
                f"Loop step value must be a Number, not '{type(step_value).__name__}'",
                context
            ))

        if step_value.value == 0:
            return res.failure(IllegalOperationError(
                node.step_value_node.pos_start if node.step_value_node else node.pos_start,
                node.step_value_node.pos_end if node.step_value_node else node.pos_end,
                "Loop step cannot be 0",
                context
            ))

        i = start_value.value

        if step_value.value >= 0:
            condition = lambda: i <= end_value.value
        else:
            condition = lambda: i >= end_value.value

        iterations = 0
        while condition():
            iterations += 1
            from sards.core import constants
            if not constants.UNBOUNDED_MODE and iterations >= 200000:
                from sards.core.error import ValueError as SardineValueError
                return res.failure(SardineValueError(node.pos_start, node.pos_end, "Loop execution limit exceeded (max 100,000 iterations)", context))
            context.symbol_table.set(node.var_name_tok.value, Number(i))
            i += step_value.value

            value = res.register(self.visit(node.body_node, context))
            if (res.should_return() and
                not res.loop_continue and
                not res.loop_or_switch_break):
                return res

            if res.loop_continue:
                continue
            if res.loop_or_switch_break:
                break

            if not node.return_null:
                if len(elements) < 100000:
                    elements.append(value)
                elif not constants.UNBOUNDED_MODE:
                    from sards.core.error import ValueError as SardineValueError
                    return res.failure(SardineValueError(node.pos_start, node.pos_end, "Loop execution result accumulation limit exceeded (max 100,000 items)", context))

        return res.success(
            Number(0) if node.return_null else (List(elements)
                                                .set_context(context)
                                                .set_pos(node.pos_start,node.pos_end)))

    def visit_ForEachLoopNode(self, node, context):
        res = RunTimeResult()
        var_name_tokens = node.var_name_tokens
        num_vars = len(var_name_tokens)

        collection = res.register(self.visit(node.collection_node, context))
        if res.should_return():
            return res

        if isinstance(collection, Dict):
            if num_vars == 1:
                var_name = var_name_tokens[0].value
                for key, value in list(collection.elements.items()):
                    pair = List([key.copy(), value.copy()])
                    pair.set_context(context).set_pos(node.pos_start, node.pos_end)
                    context.symbol_table.set(var_name, pair)

                    value = res.register(self.visit(node.body_node, context))
                    if (res.should_return() and
                            not res.loop_continue and
                            not res.loop_or_switch_break):
                        return res
                    if res.loop_continue:
                        continue
                    if res.loop_or_switch_break:
                        break

            elif num_vars == 2:
                key_var_name = var_name_tokens[0].value
                val_var_name = var_name_tokens[1].value
                for key, value in list(collection.elements.items()):
                    context.symbol_table.set(key_var_name, key.copy())
                    context.symbol_table.set(val_var_name, value.copy())

                    value = res.register(self.visit(node.body_node, context))
                    if (res.should_return() and
                            not res.loop_continue and
                            not res.loop_or_switch_break):
                        return res
                    if res.loop_continue:
                        continue
                    if res.loop_or_switch_break:
                        break
            else:
                return res.failure(
                    ArgumentError(
                        node.pos_start, node.pos_end,
                        f"Dictionary trace expects 1 or 2 variables, but got {num_vars}",
                        context
                    )
                )

        elif isinstance(collection, List):
            if num_vars == 1:
                var_name = var_name_tokens[0].value
                for element in list(collection.elements):
                    context.symbol_table.set(var_name, element.copy())

                    value = res.register(self.visit(node.body_node, context))
                    if (res.should_return() and
                            not res.loop_continue and
                            not res.loop_or_switch_break):
                        return res
                    if res.loop_continue:
                        continue
                    if res.loop_or_switch_break:
                        break
            else:
                for element in list(collection.elements):
                    if not isinstance(element, List):
                        return res.failure(
                            IllegalOperationError(
                                getattr(element, 'pos_start', node.pos_start),
                                getattr(element, 'pos_end', node.pos_end),
                                f"Cannot unpack non-list item into {num_vars} variables",
                                context
                            )
                        )

                    if len(element.elements) != num_vars:
                        return res.failure(
                            ValueError(
                                getattr(element, 'pos_start', node.pos_start),
                                getattr(element, 'pos_end', node.pos_end),
                                f"Expected {num_vars} values to unpack, but got {len(element.elements)}",
                                context
                            )
                        )

                    for i in range(num_vars):
                        var_name = var_name_tokens[i].value
                        sub_element = element.elements[i]
                        context.symbol_table.set(var_name, sub_element.copy())

                    value = res.register(self.visit(node.body_node, context))
                    if (res.should_return() and
                            not res.loop_continue and
                            not res.loop_or_switch_break):
                        return res
                    if res.loop_continue:
                        continue
                    if res.loop_or_switch_break:
                        break

        elif isinstance(collection, String):
            if num_vars == 1:
                var_name = var_name_tokens[0].value
                for char in collection.value:
                    char_str = String(char).set_context(context).set_pos(node.pos_start, node.pos_end)
                    context.symbol_table.set(var_name, char_str)

                    value = res.register(self.visit(node.body_node, context))
                    if (res.should_return() and
                            not res.loop_continue and
                            not res.loop_or_switch_break):
                        return res
                    if res.loop_continue:
                        continue
                    if res.loop_or_switch_break:
                        break
            else:
                return res.failure(
                    ArgumentError(
                        node.pos_start, node.pos_end,
                        f"Cannot unpack a string into {num_vars} variables",
                        context
                    )
                )

        else:
            return res.failure(
                IllegalOperationError(
                    getattr(collection, 'pos_start', node.pos_start),
                    getattr(collection, 'pos_end', node.pos_end),
                    f"'{type(collection).__name__}' object is not iterable",
                    context,
                    hint="Only List, String, and Dict values can be iterated with 'trace'."
                )
            )

        return res.success(Number(0))

    def visit_SwitchNode(self, node, context):
        res = RunTimeResult()
        elements = []
        match_index = start_index = 0
        default_index = len(node.cases)
        match_found = False
        selection_val = res.register(self.visit(node.select, context))
        if res.should_return():
            return res

        if not hasattr(selection_val, 'value'):
            return res.failure(IllegalOperationError(
                node.select.pos_start, node.select.pos_end,
                f"Menu selection value must be a primitive value, not '{type(selection_val).__name__}'",
                context
            ))

        seen_choices = []
        for choice, _, _ in node.cases:
            if choice is None:
                default_index = match_index
                match_index = match_index + 1
                continue
            choice_val = res.register(self.visit(choice, context))
            if res.should_return():
                return res

            if not hasattr(choice_val, 'value'):
                return res.failure(IllegalOperationError(
                    choice.pos_start, choice.pos_end,
                    f"Menu choices must be primitive values, not '{type(choice_val).__name__}'",
                    context
                ))
            
            try:
                for seen in seen_choices:
                    if choice_val.value == seen:
                        return res.failure(RunTimeError(
                            choice.pos_start, choice.pos_end,
                            f"Duplicate choice '{choice_val.value}' in menu",
                            context
                        ))
                seen_choices.append(choice_val.value)
            except Exception:
                pass

            if not match_found and selection_val.value == choice_val.value:
                match_found = True
                start_index = match_index
            match_index = match_index + 1
        
        if not match_found:
            start_index = default_index

        for choice, body, return_null in node.cases[start_index:]:
            body_val = res.register(self.visit(body, context))
            if (res.should_return() and
                not res.loop_or_switch_break):
                return res
            elements.append(Number(0) if return_null else body_val)
            if res.loop_or_switch_break:
                break

        return res.success(
            Number(0) if node.return_null else (List(elements)
                                                .set_context(context)
                                                .set_pos(node.pos_start,
                                                                                           node.pos_end)))
    def visit_IfNode(self, node, context):
        res = RunTimeResult()

        for condition, expression, return_null in node.cases:
            condition_value = res.register(self.visit(condition, context))
            if res.should_return():
                return res

            cond, error = condition_value.is_true()
            if cond.value:
                expression_value = res.register(self.visit(expression, context))
                if res.should_return():
                    return res
                return res.success(Number(0) if return_null else expression_value)

        if node.else_case:
            expression, return_null = node.else_case
            else_value = res.register(self.visit(expression, context))
            if res.should_return():
                return res
            return res.success(Number(0) if return_null else else_value)

        return res.success(Number(0))

    def visit_VariableUseNode(self, node, context):
        from sards.user_functions import Function
        from sards.oops_types import Model

        res = RunTimeResult()
        var_name = node.var_name_tok.value
        value = None

        value = context.symbol_table.get(var_name)

        if value is None:
            instance = context.symbol_table.get("this")
            if instance:
                value, error = instance.get_attr(var_name, context)
                if error:
                    return res.failure(error)

        if value is None:
            _STDLIB_MODULES = {"math", "random", "stat", "linalg", "test_utils"}
            _all_names = list(context.symbol_table.symbols.keys())
            # walk up the scope chain for more candidates
            _scope = context.symbol_table.parent
            while _scope:
                _all_names.extend(_scope.symbols.keys())
                _scope = _scope.parent
            if var_name in _STDLIB_MODULES:
                _hint = f"'{var_name}' is a standard library module. Did you forget to 'summon {var_name}'?"
            else:
                _suggestion = fuzzy_match(var_name, _all_names)
                _hint = f"Did you mean '{_suggestion}'?" if _suggestion else "Check for typos or make sure the variable is assigned before use."
            return res.failure(
                NameError(
                    node.pos_start,
                    node.pos_end,
                    f"'{var_name}' is not defined",
                    context,
                    hint=_hint
                )
            )

        indexes = []
        for index_node in node.index_node:
            index_val = res.register(self.visit(index_node, context))
            if res.should_return():
                return res
            indexes.append(index_val)

        if not indexes:
            value = value.copy().set_pos(node.pos_start, node.pos_end)
    
            if not isinstance(value, Function) and not isinstance(value, Model):
                value.set_context(context)
            return res.success(value)
        else:
            if not hasattr(value, 'getByIndex'):
                return res.failure(RunTimeError(node.pos_start, node.pos_end, f"Type '{type(value).__name__}' is not scriptable/indexable", context))
            value, error = value.getByIndex(indexes)
            if error:
                return res.failure(error)
            value = value.copy().set_pos(node.pos_start, node.pos_end)
            if not isinstance(value, Function) and not isinstance(value, Model):
                value.set_context(context)
            return res.success(value)

    def visit_AssignNode(self, node, context):
        res = RunTimeResult()
        last_result = None

        num_vars = len(node.left_nodes)
        num_vals = len(node.value_nodes)

        if num_vars > 1 and num_vals == 1:
            for left_node in node.left_nodes:
                node_type = left_node.__class__.__name__
                if node_type == "IndexAccessNode" or (node_type == "VariableUseNode" and left_node.index_node):
                    return res.failure(RunTimeError(
                        node.pos_start, node.pos_end,
                        "Cannot unpack into indexed variables",
                        context
                    ))

            collection = res.register(self.visit(node.value_nodes[0], context))
            if res.should_return():
                return res

            elements = []
            if isinstance(collection, List):
                elements = collection.elements
            elif isinstance(collection, String):
                elements = [String(char).set_context(context).set_pos(collection.pos_start, collection.pos_end)
                            for char in collection.value]
            else:
                return res.failure(IllegalOperationError(
                    node.value_nodes[0].pos_start, node.value_nodes[0].pos_end,
                    f"Cannot unpack non-iterable type '{type(collection).__name__}'",
                    context
                ))

            if len(elements) != num_vars:
                return res.failure(RunTimeError(
                    node.value_nodes[0].pos_start, node.value_nodes[0].pos_end,
                    f"ValueError: Expected {num_vars} values, but got {len(elements)}",
                    context
                ))

            for i in range(num_vars):
                left_node = node.left_nodes[i]
                value = elements[i]
                node_type = left_node.__class__.__name__

                if node_type == "VariableUseNode":
                    var_name = left_node.var_name_tok.value
                    
                    instance = context.symbol_table.get("this")
                    is_attr = False
                    if instance and hasattr(instance, 'model'):
                        if instance.model.find_attribute(var_name) is not None:
                            is_attr = True

                    if is_attr:
                        instance.symbol_table.set(var_name, value)
                    else:
                        context.symbol_table.set(var_name, value)
                    last_result = value
                elif node_type == "AttrAccessNode":
                    object_val = res.register(self.visit(left_node.object_node, context))
                    if res.should_return(): return res
                    attr_name = left_node.attr_name_tok.value
                    
                    if not hasattr(object_val, 'set_attr'):
                        return res.failure(RunTimeError(left_node.pos_start, left_node.pos_end, f"Cannot set attribute on '{type(object_val).__name__}'", context))
                        
                    _, err = object_val.set_attr(attr_name, value)
                    if err:
                        return res.failure(RunTimeError(left_node.pos_start, left_node.pos_end, err, context))
                    last_result = value

            return res.success(last_result)

        else:
            if num_vars != num_vals:
                return res.failure(RunTimeError(
                    node.pos_start, node.pos_end,
                    f"Interpreter Error: Mismatched assignment count ({num_vars} vars, {num_vals} vals)",
                    context
                ))

            for left_node, value_node in zip(node.left_nodes, node.value_nodes):
                value = res.register(self.visit(value_node, context))
                if res.should_return():
                    return res

                node_type = left_node.__class__.__name__

                if node_type == "IndexAccessNode":
                    object_val = res.register(self.visit(left_node.object_node, context))
                    if res.should_return(): return res
                    
                    index_val = res.register(self.visit(left_node.index_node, context))
                    if res.should_return(): return res
                    
                    if not hasattr(object_val, 'assignIndex'):
                        return res.failure(RunTimeError(left_node.pos_start, left_node.pos_end, f"Type '{type(object_val).__name__}' does not support index assignment", context))
                        
                    _, error = object_val.assignIndex([index_val], value)
                    if error:
                        return res.failure(error)
                    last_result = value
                    
                elif node_type == "VariableUseNode":
                    var_name = left_node.var_name_tok.value
                    indexes = left_node.index_node

                    if indexes:
                        indexes_vals = []
                        for index in indexes:
                            index_val = res.register(self.visit(index, context))
                            if res.should_return():
                                return res
                            indexes_vals.append(index_val)

                        list_value = context.symbol_table.get(var_name)
                        if list_value is None:
                            _all_names2 = list(context.symbol_table.symbols.keys())
                            _sug2 = fuzzy_match(var_name, _all_names2)
                            _hint2 = f"Did you mean '{_sug2}'?" if _sug2 else "Check for typos or make sure the variable is assigned before use."
                            return res.failure(
                                NameError(left_node.pos_start, value_node.pos_end, f"'{var_name}' is not defined", context, hint=_hint2)
                            )
                        list_value, error = list_value.assignIndex(indexes_vals, value)
                        if error:
                            return res.failure(error)
                        context.symbol_table.set(var_name, list_value)
                        last_result = list_value
                    else:
                        instance = context.symbol_table.get("this")
                        is_attr = False
                        if instance and hasattr(instance, 'model'):
                            if instance.model.find_attribute(var_name) is not None:
                                is_attr = True

                        if is_attr:
                            instance.symbol_table.set(var_name, value)
                        else:
                            context.symbol_table.set(var_name, value)
                        last_result = value
                
                elif node_type == "AttrAccessNode":
                    object_val = res.register(self.visit(left_node.object_node, context))
                    if res.should_return(): return res
                    attr_name = left_node.attr_name_tok.value
                    
                    if not hasattr(object_val, 'set_attr'):
                        return res.failure(RunTimeError(left_node.pos_start, left_node.pos_end, f"Cannot set attribute on '{type(object_val).__name__}'", context))
                        
                    _, err = object_val.set_attr(attr_name, value)
                    if err:
                        return res.failure(RunTimeError(left_node.pos_start, left_node.pos_end, err, context))
                    last_result = value

            return res.success(last_result)

    def visit_IndexAccessNode(self, node, context):
        res = RunTimeResult()
        
        object_val = res.register(self.visit(node.object_node, context))
        if res.should_return(): return res
        
        index_val = res.register(self.visit(node.index_node, context))
        if res.should_return(): return res
        
        if not hasattr(object_val, 'getByIndex'):
            return res.failure(RunTimeError(node.pos_start, node.pos_end, f"Type '{type(object_val).__name__}' is not scriptable/indexable", context))
            
        value, error = object_val.getByIndex([index_val])
        if error:
            return res.failure(error)
            
        value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return res.success(value)

    def visit_NumberNode(self, node, context):
        return RunTimeResult().success(
            Number(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_ReturnNode(self, node, context):
        res = RunTimeResult()
        return_values = []

        if not node.nodes_to_return:
            return res.success_return(Number(0))

        for node_to_return in node.nodes_to_return:
            value = res.register(self.visit(node_to_return, context))
            if res.should_return():
                return res
            return_values.append(value)

        if len(return_values) == 1:
            return res.success_return(return_values[0])

        return res.success_return(
            List(return_values)
            .set_context(context)
            .set_pos(node.pos_start, node.pos_end)
        )

    def visit_ContinueNode(self, node, context):
        return RunTimeResult().success_continue()

    def visit_BreakNode(self, node, context):
        return RunTimeResult().success_break()

    def visit_BinaryOperationNode(self, node, context):
        res = RunTimeResult()
        left_node = res.register(self.visit(node.left_node, context))
        if res.should_return():
            return res
        right_node = res.register(self.visit(node.right_node, context))
        if res.should_return():
            return res

        method_name = None
        op_symbol = node.operator.value or str(node.operator.type)
        if node.operator.type == T_PLUS: method_name = 'add'
        elif node.operator.type == T_MINUS: method_name = 'subtract'
        elif node.operator.type == T_MUL: method_name = 'multiply'
        elif node.operator.type == T_DIVIDE: method_name = 'divide'
        elif node.operator.type == T_MODULUS: method_name = 'modulus'
        elif node.operator.type == T_FLOOR: method_name = 'floor_divide'
        elif node.operator.type == T_BITAND: method_name = 'bitwise_and'
        elif node.operator.type == T_BITXOR: method_name = 'bitwise_xor'
        elif node.operator.type == T_BITOR: method_name = 'bitwise_or'
        elif node.operator.type == T_LSHIFT: method_name = 'lshift'
        elif node.operator.type == T_RSHIFT: method_name = 'rshift'
        elif node.operator.type == T_EXP: method_name = 'exponent'
        elif node.operator.type == T_EE: method_name = 'get_comparison_eq'
        elif node.operator.type == T_NEQ: method_name = 'get_comparison_neq'
        elif node.operator.type == T_GT: method_name = 'get_comparison_gt'
        elif node.operator.type == T_GTE: method_name = 'get_comparison_gte'
        elif node.operator.type == T_LT: method_name = 'get_comparison_lt'
        elif node.operator.type == T_LTE: method_name = 'get_comparison_lte'
        elif node.operator.type == T_KEYWORD and node.operator.value == 'and': method_name = 'and_by'
        elif node.operator.type == T_KEYWORD and node.operator.value == 'or': method_name = 'or_by'

        if method_name:
            if not hasattr(left_node, method_name):
                return res.failure(IllegalOperationError(
                    node.pos_start, node.pos_end,
                    f"Operator '{op_symbol}' is not supported by type '{type(left_node).__name__}'",
                    context
                ))
            method = getattr(left_node, method_name)
            try:
                result, error = method(right_node)
            except (ValueError, TypeError, OverflowError, MemoryError, AttributeError) as e:
                return res.failure(IllegalOperationError(
                    node.pos_start, node.pos_end,
                    f"Error during binary operation '{op_symbol}': {str(e)}",
                    context
                ))
        else:
            return res.failure(IllegalOperationError(
                node.pos_start, node.pos_end,
                f"Unsupported operator '{op_symbol}'",
                context
            ))

        if error:
            return res.failure(error)
        return res.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_TernaryOperationNode(self, node, context):
        res = RunTimeResult()
        comp_node = res.register(self.visit(node.comp_node, context))
        if res.should_return():
            return res

        cond, error = comp_node.is_true()
        if cond.value:
            true_node = res.register(self.visit(node.true_node, context))
            if res.should_return():
                return res
            result, error = true_node, None
        else:
            false_node = res.register(self.visit(node.false_node, context))
            if res.should_return():
                return res
            result, error = false_node, None

        if error:
            return res.failure(error)
        else:
            return res.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_UnaryOperationNode(self, node, context):
        res = RunTimeResult()
        number = res.register(self.visit(node.node, context))
        if res.should_return():
            return res

        method_name = None
        op_symbol = node.operator.value or str(node.operator.type)
        if node.operator.type == T_MINUS:
            method_name = 'multiply'
        elif node.operator.type == T_KEYWORD and node.operator.value == 'not':
            method_name = 'not_by'
        elif node.operator.type == T_BITNOT:
            method_name = 'bitwise_not'

        if method_name:
            if not hasattr(number, method_name):
                return res.failure(IllegalOperationError(
                    node.pos_start, node.pos_end,
                    f"Operator '{op_symbol}' is not supported by type '{type(number).__name__}'",
                    context
                ))
            try:
                if method_name == 'multiply':
                    number, error = number.multiply(Number(-1))
                else:
                    method = getattr(number, method_name)
                    number, error = method()
            except (ValueError, TypeError, OverflowError, MemoryError, AttributeError) as e:
                return res.failure(IllegalOperationError(
                    node.pos_start, node.pos_end,
                    f"Error during unary operation '{op_symbol}': {str(e)}",
                    context
                ))
        else:
            return res.failure(IllegalOperationError(
                node.pos_start, node.pos_end,
                f"Unsupported unary operator '{op_symbol}'",
                context
            ))

        if error:
            return res.failure(error)
        else:
            return res.success(number.set_pos(node.pos_start, node.pos_end))

    # ------------------------------------------------------------------
    # summon / import
    # ------------------------------------------------------------------

    def visit_SummonNode(self, node, context):
        """
        Resolves, loads (or retrieves from cache), and executes a Sardine module,
        then binds the requested names into the current context's symbol table.
        """
        res = RunTimeResult()
        module_name = node.module_tok.value

        # ── 1. Resolve the file path ────────────────────────────────────
        # Derive the directory of the currently-executing file from context.
        source_dir = getattr(context, 'source_dir', None) or os.getcwd()
        candidates = [
            os.path.join(source_dir, module_name + '.sad'),
            os.path.join(source_dir, module_name + '.sard'),
            os.path.join(_STDLIB_DIR, module_name + '.sad'),
            os.path.join(_STDLIB_DIR, module_name + '.sard'),
        ]

        resolved_path = None
        for path in candidates:
            if os.path.isfile(path):
                resolved_path = os.path.abspath(path)
                break

        if resolved_path is None:
            display_candidates = [
                os.path.relpath(path, start=os.curdir).replace('\\', '/')
                for path in candidates
            ]
            return res.failure(ModuleError(
                node.pos_start, node.pos_end,
                f"Module '{module_name}' not found. Searched:\n" +
                "\n".join(f"  {p}" for p in display_candidates),
                context
            ))

        # ── 2. Check cache ───────────────────────────────────────────────
        if resolved_path in _MODULE_CACHE:
            module_obj = _MODULE_CACHE[resolved_path]
            if module_obj == "loading":
                return res.failure(ModuleError(
                    node.pos_start, node.pos_end,
                    f"Circular dependency detected: module '{module_name}' is already being loaded",
                    context
                ))
        else:
            # ── 3. Read & execute the module ─────────────────────────────
            _MODULE_CACHE[resolved_path] = "loading"
            try:
                try:
                    with open(resolved_path, 'r', encoding='utf-8') as f:
                        source = f.read()
                except Exception as file_err:
                    if _MODULE_CACHE.get(resolved_path) == "loading":
                        del _MODULE_CACHE[resolved_path]
                    return res.failure(ModuleError(
                        node.pos_start, node.pos_end,
                        f"Failed to read module '{module_name}': {str(file_err)}",
                        context
                    ))

                from .lexer import Lexer
                from .parser import Parser

                lexer = Lexer(resolved_path, source)
                tokens, lex_error = lexer.enumerate_tokens()
                if lex_error:
                    if _MODULE_CACHE.get(resolved_path) == "loading":
                        del _MODULE_CACHE[resolved_path]
                    return res.failure(ModuleError(
                        node.pos_start, node.pos_end,
                        f"Lexer error in module '{module_name}': {lex_error.details}",
                        context
                    ))

                parser = Parser(tokens)
                parse_result = parser.parse()
                if parse_result.error:
                    if _MODULE_CACHE.get(resolved_path) == "loading":
                        del _MODULE_CACHE[resolved_path]
                    return res.failure(ModuleError(
                        node.pos_start, node.pos_end,
                        f"Syntax error in module '{module_name}': {parse_result.error.details}",
                        context
                    ))

                # Build a fresh context for the module, inheriting global builtins
                mod_symbol_table = SymbolTable(parent=context.symbol_table)
                mod_context = Context(f"<module '{module_name}'>",
                                      parent=context,
                                      parent_entry_pos=node.pos_start)
                mod_context.symbol_table = mod_symbol_table
                mod_context.source_dir = os.path.dirname(resolved_path)

                mod_interpreter = Interpreter()
                mod_res = mod_interpreter.visit(parse_result.node, mod_context)
                if mod_res.error:
                    if _MODULE_CACHE.get(resolved_path) == "loading":
                        del _MODULE_CACHE[resolved_path]
                    return res.failure(ModuleError(
                        node.pos_start, node.pos_end,
                        f"Runtime error in module '{module_name}': {mod_res.error.details}",
                        context
                    ))

                module_obj = Module(module_name, mod_symbol_table)
                module_obj.set_pos(node.pos_start, node.pos_end)
                module_obj.set_context(context)
                _MODULE_CACHE[resolved_path] = module_obj
            except Exception as e:
                if _MODULE_CACHE.get(resolved_path) == "loading":
                    del _MODULE_CACHE[resolved_path]
                return res.failure(ModuleError(
                    node.pos_start, node.pos_end,
                    f"Unexpected error loading module '{module_name}': {str(e)}",
                    context
                ))

        # ── 4. Bind names into current scope ────────────────────────────

        # Case A: bare  summon math  OR  summon math as m
        if not node.names and not node.wildcard:
            bind_name = node.module_alias.value if node.module_alias else module_name
            context.symbol_table.set(bind_name, module_obj)
            return res.success(module_obj)

        # Case B: wildcard  summon * from math
        if node.wildcard:
            for name, value in module_obj.symbol_table.symbols.items():
                context.symbol_table.set(name, value)
            return res.success(module_obj)

        # Case C: specific names  summon sin, cos from math
        #         or with alias   summon factorial as fact from math
        for orig_tok, alias_tok in node.names:
            orig_name = orig_tok.value
            value = module_obj.symbol_table.get(orig_name)
            if value is None:
                _mod_members = list(module_obj.symbol_table.symbols.keys())
                _mod_suggestion = fuzzy_match(orig_name, _mod_members)
                _mod_hint = f"Did you mean '{_mod_suggestion}'?" if _mod_suggestion else f"Available members: {', '.join(_mod_members[:8])}"
                return res.failure(ModuleError(
                    orig_tok.pos_start, orig_tok.pos_end,
                    f"Module '{module_name}' has no member '{orig_name}'",
                    context,
                    hint=_mod_hint
                ))
            bind_name = alias_tok.value if alias_tok else orig_name
            context.symbol_table.set(bind_name, value)

        return res.success(module_obj)
