"""
interpreter.py

This module defines the components needed for interpreting an abstract syntax tree (AST).
It includes classes for handling runtime context, execution results, and evaluating expressions.

Classes:
- Context: Maintains execution context (e.g., scope, parent context).
- RunTimeResult: Stores the result of an evaluation, including errors.
- Interpreter: Evaluates AST nodes and executes operations.
"""

from sards.data_types import Number, String, List, Dict
from .constants import (T_PLUS, T_MINUS, T_MUL, T_DIVIDE, T_MODULUS, T_FLOOR, T_EXP, T_EE,
                        T_NEQ, T_GT, T_GTE, T_LT, T_LTE, T_KEYWORD)
from .error import RunTimeError

class Context: # pylint: disable=R0903
    """
    Represents the execution context of a program.

    Attributes:
    - display_name (str): The name of the current execution context.
    - parent (Context, optional): The parent context (e.g., caller function).
    - parent_entry_pos (optional): The position in the parent where this context was entered.
    """

    def __init__(self, display_name, parent=None, parent_entry_pos=None):
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
        self.error = res.should_return()
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
        raise NotImplementedError(f'No visit_{type(node).__name__} method defined')

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
                    RunTimeError(
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

    def visit_FunctionDefinitionNode(self, node, context):
        from sards.user_functions import Function
        res = RunTimeResult()

        func_name = node.var_name_tok.value if node.var_name_tok else None
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_toks]
        func_value = (Function(func_name, body_node, arg_names, node.auto_return)
                      .set_context(context)
                      .set_pos(node.pos_start, node.pos_end))

        if node.var_name_tok:
            context.symbol_table.set(func_name, func_value)

        return res.success(func_value)

    def visit_FunctionCallNode(self, node, context):
        res = RunTimeResult()
        args = []

        call_value = res.register(self.visit(node.call_node, context))
        if res.should_return():
            return res
        call_value = call_value.copy().set_pos(node.pos_start, node.pos_end)

        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.should_return():
                return res

        return_value = res.register(call_value.execute(args))
        if res.should_return():
            return res
        return_value = (return_value.copy()
                        .set_pos(node.pos_start, node.pos_end)
                        .set_context(context))

        return res.success(return_value)

    def visit_WhileNode(self, node, context):
        res = RunTimeResult()
        elements = []

        while True:
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

            elements.append(value)

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

        i = start_value.value

        if step_value.value >= 0:
            condition = lambda: i <= end_value.value
        else:
            condition = lambda: i >= end_value.value

        while condition():
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

            elements.append(value)

        return res.success(
            Number(0) if node.return_null else (List(elements)
                                                .set_context(context)
                                                .set_pos(node.pos_start,
                                                                                           node.pos_end)))

    def visit_SwitchNode(self, node, context):
        res = RunTimeResult()
        elements = []
        match_index = start_index = 0
        default_index = len(node.cases)
        match_found = False
        selection_val = res.register(self.visit(node.select, context))
        if res.should_return():
            return res

        for choice, _, _ in node.cases:
            if choice is None:
                default_index = match_index
                match_index = match_index + 1
                continue
            choice_val = res.register(self.visit(choice, context))
            if res.should_return():
                return res
            if selection_val.value == choice_val.value:
                match_found = True
                break
            match_index = match_index + 1
        start_index = match_index if match_found else default_index

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
        res = RunTimeResult()
        var_name = node.var_name_tok.value
        value = context.symbol_table.get(var_name)

        if value is None:
            return (res.failure(
                RunTimeError(node.pos_start,
                             node.pos_end,
                             f"'{var_name}' is not defined",
                             context)))
        
        indexes=[]

        for index in node.index_node:
            index_val=res.register(self.visit(index,context))
            indexes.append(index_val)

        if not indexes:
            value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
            return res.success(value)
        else:
            value,error=value.getByIndex(indexes)
            if error:return res.failure(error)
            value=value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
            return res.success(value)

    def visit_VariableAssignNode(self, node, context):
        res = RunTimeResult()
        var_name = node.var_name_tok.value
        indexes=[]

        for index in node.index_node:
            index_val=res.register(self.visit(index,context))
            indexes.append(index_val)

        value = res.register(self.visit(node.value_node, context))
        if res.should_return():
            return res
        
        if indexes:
            list_value = context.symbol_table.get(var_name)
            
            if list_value is None:
                return (res.failure(
                    RunTimeError(node.pos_start,
                                node.pos_end,
                                f"'{var_name}' is not defined",
                                context)))
            
            list_value,error=list_value.assignIndex(indexes,value)
            if error:return res.failure(error)

        if not indexes:
            context.symbol_table.set(var_name, value)
            return res.success(value)
        else:
            context.symbol_table.set(var_name, list_value)
            return res.success(list_value)

    def visit_NumberNode(self, node, context):
        return RunTimeResult().success(
            Number(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_ReturnNode(self, node, context):
        res = RunTimeResult()

        if node.node_to_return:
            value = res.register(self.visit(node.node_to_return, context))
            if res.should_return():
                return res
        else:
            value = Number(0)

        return res.success_return(value)

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

        error = None
        if node.operator.type == T_PLUS:
            result, error = left_node.add(right_node)
        elif node.operator.type == T_MINUS:
            result, error = left_node.subtract(right_node)
        elif node.operator.type == T_MUL:
            result, error = left_node.multiply(right_node)
        elif node.operator.type == T_DIVIDE:
            result, error = left_node.divide(right_node)
        elif node.operator.type == T_MODULUS:
            result, error = left_node.modulus(right_node)
        elif node.operator.type == T_FLOOR:
            result, error = left_node.floor_divide(right_node)
        elif node.operator.type == T_EXP:
            result, error = left_node.exponent(right_node)
        elif node.operator.type == T_EE:
            result, error = left_node.get_comparison_eq(right_node)
        elif node.operator.type == T_NEQ:
            result, error = left_node.get_comparison_neq(right_node)
        elif node.operator.type == T_GT:
            result, error = left_node.get_comparison_gt(right_node)
        elif node.operator.type == T_GTE:
            result, error = left_node.get_comparison_gte(right_node)
        elif node.operator.type == T_LT:
            result, error = left_node.get_comparison_lt(right_node)
        elif node.operator.type == T_LTE:
            result, error = left_node.get_comparison_lte(right_node)
        elif node.operator.type == T_KEYWORD and node.operator.value == 'and':
            result, error = left_node.and_by(right_node)
        elif node.operator.type == T_KEYWORD and node.operator.value == 'or':
            result, error = left_node.or_by(right_node)

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

        error = None
        if node.operator.type == T_MINUS:
            number, error = number.multiply(Number(-1))

        elif node.operator.type == T_KEYWORD and node.operator.value == 'not':
            number, error = number.not_by()

        if error:
            return res.failure(error)
        else:
            return res.success(number.set_pos(node.pos_start, node.pos_end))
