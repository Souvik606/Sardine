"""
This module defines the BaseFunction, Function, and BuiltInFunction classes,
which represent different types of functions in the abstract syntax tree (AST).

Classes:
    BaseFunction: A base class for functions in the AST.
    Function: A class to represent user-defined functions in the AST.
    BuiltInFunction: A class to represent built-in functions in the AST.
"""

from sards.ast_nodes import SymbolTable
from sards.core import RunTimeResult, Interpreter
from sards.core.error import ArgumentError
from sards.data_types import Number, String, List


class BaseFunction:
    """
    A base class for functions in the abstract syntax tree (AST).

    Attributes:
        name: The name of the function.
        pos_start: The starting position of the function in the source code.
        pos_end: The ending position of the function in the source code.
        context: The context in which the function is executed.
    """
    def __init__(self, name):
        """
        Initializes a BaseFunction instance.

        Args:
            name: The name of the function.
        """
        self.name = name or "<anonymous>"
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        """
        Sets the position of the function in the source code.

        Args:
            pos_start: The starting position of the function.
            pos_end: The ending position of the function.

        Returns:
            self: The current instance.
        """
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        """
        Sets the context of the function.

        Args:
            context: The context to set.

        Returns:
            self: The current instance.
        """
        self.context = context
        return self

    def generate_new_context(self):
        from sards.core import Context

        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        return new_context

    def check_args(self, arg_names, args):
        """
        Checks the arguments passed to the function.

        Args:
            arg_names: A list of argument names.
            args: A list of arguments.

        Returns:
            res: The result of the argument check.
        """
        res = RunTimeResult()

        if len(args) > len(arg_names):
            return res.failure(
                ArgumentError(self.pos_start, self.pos_end,
                    f"{len(args) - len(arg_names)} too many args passed into '{self.name}'",
                    self.context))

        if len(args) < len(arg_names):
            return res.failure(
                ArgumentError(self.pos_start, self.pos_end,
                    f"{len(arg_names) - len(args)} too few args passed into '{self.name}'",
                    self.context))
        return res.success(None)

    def populate_args(self, arg_names, args, context):
        """
        Populates the arguments in the function's context.

        Args:
            arg_names: A list of argument names.
            args: A list of arguments.
            context: The context to populate.
        """
        for i, arg_value in enumerate(args):
            arg_name = arg_names[i]
            arg_value.set_context(context)
            context.symbol_table.set(arg_name, arg_value)

    def check_and_populate_args(self, arg_names, args, context):
        """
        Checks and populates the arguments in the function's context.

        Args:
            arg_names: A list of argument names.
            args: A list of arguments.
            context: The context to populate.

        Returns:
            res: The result of the argument check and population.
        """
        res = RunTimeResult()
        res.register(self.check_args(arg_names, args))
        if res.should_return():
            return res
        self.populate_args(arg_names, args, context)
        return res.success(None)


class Function(BaseFunction):
    """
    Represents a user-defined function in the abstract syntax tree (AST).

    Attributes:
        body_node: The node representing the body of the function.
        arg_names: A list of argument names.
        auto_return: A flag indicating whether the function automatically returns the last
        evaluated expression.
    """
    def __init__(self, name, body_node, arg_names, auto_return):
        """
        Initializes a Function instance.

        Args:
            name: The name of the function.
            body_node: The node representing the body of the function.
            arg_names: A list of argument names.
            auto_return: A flag indicating whether the function automatically returns the last
            evaluated expression.
        """
        super().__init__(name)
        self.body_node = body_node
        self.arg_names = arg_names
        self.auto_return = auto_return

    def execute(self, args):
        """
        Executes the function with the given arguments.

        Args:
            args: A list of arguments.

        Returns:
            res: The result of the function execution.
        """
        res = RunTimeResult()
        interpreter = Interpreter()
        exec_context = self.generate_new_context()

        res.register(self.check_and_populate_args(self.arg_names, args, exec_context))
        if res.should_return():
            return res

        value = res.register(interpreter.visit(self.body_node, exec_context))
        if res.should_return() and res.func_return_value is None:
            return res

        return_value = ((value if self.auto_return else None) or
                        res.func_return_value or Number(0))
        return res.success(return_value)

    def copy(self):
        """
        Creates a copy of the function.

        Returns:
            copy: The copy of the function.
        """
        copy = Function(self.name, self.body_node, self.arg_names, self.auto_return)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        """
        Returns a string representation of the function.

        Returns:
            str: The string representation of the function.
        """
        return f"<function {self.name}>"


class BuiltInFunction(BaseFunction):
    """
    Represents a built-in function in the abstract syntax tree (AST).
    """
    def __init__(self, name):
        """
        Initializes a BuiltInFunction instance.

        Args:
            name: The name of the function.
        """
        super().__init__(name)

    def execute(self, args):
        """
        Executes the built-in function with the given arguments.

        Args:
            args: A list of arguments.

        Returns:
            res: The result of the function execution.
        """
        res = RunTimeResult()
        exec_context = self.generate_new_context()

        method_name = f'execute_{self.name}'
        method = getattr(self, method_name, self.no_visit_method)

        res.register(self.check_and_populate_args(method.arg_names, args, exec_context))
        if res.should_return():
            return res

        return_value = res.register(method(exec_context))
        if res.should_return():
            return res
        return res.success(return_value)

    def no_visit_method(self):
        """
        Raises an exception if the execute method is not defined.

        Args:
            node: The node to visit.
            context: The context of the function.

        Raises:
            Exception: If the execute method is not defined.
        """
        raise NotImplementedError(f'No execute_{self.name} method defined')

    def copy(self):
        """
        Creates a copy of the built-in function.

        Returns:
            copy: The copy of the built-in function.
        """
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        """
        Returns a string representation of the built-in function.

        Returns:
            str: The string representation of the built-in function.
        """
        return f"<built-in function {self.name}>"

    def execute_show(self, exec_context):
        """
        Executes the 'show' built-in function.

        Args:
            exec_context: The execution context.

        Returns:
            res: The result of the function execution.
        """
        print(str(exec_context.symbol_table.get('value')))
        return RunTimeResult().success(Number(0))

    execute_show.arg_names = ['value']

    def execute_listen(self,exec_context):
        """
        Executes the 'listen' built-in function.

        Args:
            exec_context: The execution context.

        Returns:
            res: The result of the function execution.
        """
        text = input()
        return RunTimeResult().success(String(text))

    execute_listen.arg_names = []

    def execute_Integer(self, exec_context): #pylint: disable=C0103
        """
        Executes the 'Integer' built-in function.

        Args:
            exec_context: The execution context.

        Returns:
            res: The result of the function execution.
        """
        try:
            number = int(exec_context.symbol_table.get('value').value)
        except ValueError as exc:
            raise ValueError("Value Error: Cant convert to integer") from exc

        return RunTimeResult().success(Number(number))

    execute_Integer.arg_names = ['value']

    def execute_String(self, exec_context): #pylint: disable=C0103
        """
        Executes the 'String' built-in function.

        Args:
            exec_context: The execution context.

        Returns:
            res: The result of the function execution.
        """
        try:
            string = str(exec_context.symbol_table.get('value').value)
        except ValueError as exc:
            raise ValueError("Value Error: Cant convert to string") from exc

        return RunTimeResult().success(String(string))

    execute_String.arg_names = ['value']

    def execute_type(self, exec_context):
        """
        Executes the 'type' built-in function.

        Args:
            exec_context: The execution context.

        Returns:
            res: The result of the function execution.
        """
        data = exec_context.symbol_table.get('value')
        if isinstance(data, Number):
            print("type <Number>")
        elif isinstance(data, String):
            print("type <String>")
        elif isinstance(data, List):
            print("type <List>")
        return RunTimeResult().success(Number(0))

    execute_type.arg_names = ['value']


BuiltInFunction.show = BuiltInFunction('show')
BuiltInFunction.listen = BuiltInFunction('listen')
BuiltInFunction.Integer = BuiltInFunction('Integer')
BuiltInFunction.String = BuiltInFunction('String')
BuiltInFunction.type = BuiltInFunction('type')
