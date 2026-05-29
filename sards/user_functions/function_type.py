"""
This module defines the BaseFunction, Function, and BuiltInFunction classes,
which represent different types of functions in the abstract syntax tree (AST).

Classes:
    BaseFunction: A base class for functions in the AST.
    Function: A class to represent user-defined functions in the AST.
    BuiltInFunction: A class to represent built-in functions in the AST.
"""
from sards.ast_nodes import SymbolTable
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

    def __init__(self, name, instance=None):
        """
        Initializes a BaseFunction instance.

        Args:
            name: The name of the function.
        """
        self.name = name or "<anonymous>"
        self.instance = instance
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

    def check_and_populate_args(self, param_nodes, pos_args, kw_args, exec_context):
        """
        Checks and populates arguments, now handling positional, keyword, and default arguments.

        Args:
            param_nodes: The list of (name_tok, default_value_node) tuples from the function definition.
            pos_args: The list of positional arguments from the call.
            kw_args: A dictionary of {name: value_node} for keyword arguments from the call.
            exec_context: The context to populate with the final arguments.
        """
        from sards.core import RunTimeResult, Interpreter

        res = RunTimeResult()
        interpreter = Interpreter()
        param_names = [p_name.value for p_name, _ in param_nodes]
        final_args = {}

        if self.instance:
            exec_context.symbol_table.set("this", self.instance)

        if len(pos_args) > len(param_names):
            return res.failure(ArgumentError(
                self.pos_start, self.pos_end,
                f"{len(pos_args) - len(param_names)} too many arguments passed into '{self.name}'",
                exec_context
            ))

        for i, arg_value in enumerate(pos_args):
            final_args[param_names[i]] = arg_value

        for name, value_node in kw_args.items():
            if name not in param_names:
                return res.failure(ArgumentError(
                    self.pos_start, self.pos_end,
                    f"Unexpected keyword argument '{name}' passed to '{self.name}'",
                    exec_context
                ))
            if name in final_args:
                return res.failure(ArgumentError(
                    self.pos_start, self.pos_end,
                    f"Multiple values for argument '{name}' passed to '{self.name}'",
                    exec_context
                ))
            final_args[name] = value_node

        for p_name, p_default_value_node in param_nodes:
            param_name = p_name.value
            if param_name not in final_args:
                if p_default_value_node:
                    default_value = res.register(interpreter.visit(p_default_value_node, exec_context))
                    if res.should_return(): return res
                    final_args[param_name] = default_value
                else:
                    return res.failure(ArgumentError(
                        self.pos_start, self.pos_end,
                        f"Missing required argument '{param_name}' for function '{self.name}'",
                        exec_context
                    ))

        for name, value in final_args.items():
            value.set_context(exec_context)
            exec_context.symbol_table.set(name, value)

        return res.success(None)


class Function(BaseFunction):
    """
    Represents a user-defined function in the abstract syntax tree (AST).

    Attributes:
        body_node: The node representing the body of the function.
        param_nodes: A list of tuples: [(name_tok, default_value_node), ...].
        auto_return: A flag indicating whether the function automatically returns the last
        evaluated expression.
    """

    def __init__(self, name, body_node, param_nodes, auto_return, instance=None, owner_class=None):
        """
        Initializes a Function instance.

        Args:
            name: The name of the function.
            body_node: The node representing the body of the function.
            param_nodes: A list of tuples: [(name_tok, default_value_node), ...].
            auto_return: A flag indicating whether the function automatically returns the last
            evaluated expression.
        """
        super().__init__(name, instance)
        self.body_node = body_node
        self.param_nodes = param_nodes
        self.auto_return = auto_return
        self.owner_class = owner_class

    def execute(self, pos_args, kw_args, call_context=None):
        from sards.core import RunTimeResult, Interpreter, Context

        res = RunTimeResult()
        interpreter = Interpreter()

        if self.instance:
            instance = self.instance
            method_owner = self.owner_class or instance.model.find_method_owner(self.name)
            exec_context = Context(f"method {self.name}", instance.context, self.pos_start, owner_class=method_owner)
            exec_context.symbol_table = SymbolTable(instance.symbol_table)
        else:
            traceback_parent = call_context if call_context is not None else self.context
            exec_context = Context(self.name, traceback_parent, self.pos_start)
            exec_context.symbol_table = SymbolTable(self.context.symbol_table)

        from sards.core.constants import MAX_RECURSION_DEPTH
        from sards.core.error import StackDepthExceededError

        if exec_context.depth > MAX_RECURSION_DEPTH:
            return res.failure(StackDepthExceededError(
                self.pos_start, self.pos_end,
                f"Maximum recursion depth exceeded ({MAX_RECURSION_DEPTH})",
                exec_context
            ))

        res.register(self.check_and_populate_args(self.param_nodes, pos_args, kw_args, exec_context))
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
        copy = Function(self.name, self.body_node, self.param_nodes, self.auto_return, self.instance, self.owner_class)
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

    def execute(self, pos_args, kw_args, call_context=None):
        """
        Executes the built-in function with the given arguments.

        Args:
            pos_args: A list of positional arguments.
            kw_args: A dictionary of keyword arguments.
            call_context: The call-site context (accepted for API compatibility
                          with Function.execute; ignored for built-ins).

        Returns:
            res: The result of the function execution.
        """
        from sards.core import RunTimeResult

        res = RunTimeResult()
        exec_context = self.generate_new_context()

        method_name = f'execute_{self.name}'
        method = getattr(self, method_name, self.no_visit_method)

        return_value = res.register(method(pos_args, kw_args, exec_context))
        if res.should_return():
            return res
        return res.success(return_value)

    def no_visit_method(self, pos_args, kw_args, exec_context):
        """
        Raises an exception if the execute method is not defined.
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

    def execute_show(self, pos_args, kw_args, exec_context):
        """
        Executes the 'show' built-in function with 'sep' and 'end' parameters.
        """
        from sards.core import RunTimeResult
        from sards.data_types import String, Number, List, Dict

        res = RunTimeResult()
        separator = " "
        end_char = "\n"

        for name, value in kw_args.items():
            if name == 'sep':
                if not isinstance(value, String):
                    return res.failure(
                        ArgumentError(self.pos_start, self.pos_end, "'sep' must be a string", self.context))
                separator = value.value
            elif name == 'end':
                if not isinstance(value, String):
                    return res.failure(
                        ArgumentError(self.pos_start, self.pos_end, "'end' must be a string", self.context))
                end_char = value.value
            else:
                return res.failure(
                    ArgumentError(self.pos_start, self.pos_end, f"Unexpected keyword argument '{name}' for show",
                                  self.context))

        def stringify(node, nested=False):
            if isinstance(node, List):
                elements = ", ".join(stringify(el, nested=True) for el in node.elements)
                return f"[{elements}]"
            if isinstance(node, Dict):
                pairs = ", ".join(f"{stringify(k, nested=True)}: {stringify(v, nested=True)}" for k, v in node.elements.items())
                return f"{{{pairs}}}"
            if isinstance(node, String):
                return f"'{node.value}'" if nested else str(node.value)
            if hasattr(node, 'value'):
                return str(node.value)
            # if node is a python string (e.g. dict key) we should probably quote it
            if isinstance(node, str):
                return f"'{node}'" if nested else node
            return str(node)

        output = separator.join([stringify(arg) for arg in pos_args])
        print(output, end=end_char)

        return res.success(Number(0))

    def execute_listen(self, pos_args, kw_args, exec_context):
        """
        Executes the 'listen' built-in function.
        """
        from sards.core import RunTimeResult
        res = RunTimeResult()
        if len(pos_args) > 0 or len(kw_args) > 0:
            return res.failure(ArgumentError(self.pos_start, self.pos_end, "listen() takes no arguments", self.context))

        text = input()
        return res.success(String(text))

    def execute_Integer(self, pos_args, kw_args, exec_context):  # pylint: disable=C0103
        """
        Executes the 'Integer' built-in function.
        """
        from sards.core import RunTimeResult
        res = RunTimeResult()
        if len(pos_args) != 1 or len(kw_args) > 0:
            return res.failure(
                ArgumentError(self.pos_start, self.pos_end, "Integer() takes exactly one argument", self.context))

        try:
            number = int(pos_args[0].value)
        except (ValueError, TypeError) as exc:
            return res.failure(
                ArgumentError(self.pos_start, self.pos_end, "Argument must be a value convertible to an integer",
                              self.context))

        return res.success(Number(number))

    def execute_String(self, pos_args, kw_args, exec_context):  # pylint: disable=C0103
        """
        Executes the 'String' built-in function.
        """
        from sards.core import RunTimeResult
        res = RunTimeResult()
        if len(pos_args) != 1 or len(kw_args) > 0:
            return res.failure(
                ArgumentError(self.pos_start, self.pos_end, "String() takes exactly one argument", self.context))

        try:
            string = str(pos_args[0].value)
        except (ValueError, TypeError) as exc:
            return res.failure(
                ArgumentError(self.pos_start, self.pos_end, "Argument must be a value convertible to a string",
                              self.context))

        return res.success(String(string))

    def execute_type(self, pos_args, kw_args, exec_context):
        """
        Executes the 'type' built-in function.
        """
        from sards.core import RunTimeResult
        res = RunTimeResult()
        if len(pos_args) != 1 or len(kw_args) > 0:
            return res.failure(
                ArgumentError(self.pos_start, self.pos_end, "type() takes exactly one argument", self.context))

        data = pos_args[0]
        if isinstance(data, Number):
            output = "<type Number>"
        elif isinstance(data, String):
            output = "<type String>"
        elif isinstance(data, List):
            output = "<type List>"
        else:
            output = f"<type {type(data).__name__}>"

        return res.success(String(output))

    def execute_super(self, pos_args, kw_args, exec_context):
        """
        Executes the 'super()' built-in.

        Must be called from inside a method body where 'this' is available and
        the execution context has an owner_class set.  Returns a SuperProxy
        bound to the current instance, allowing calls like super().method(args)
        to resolve to the *parent* class's version of an overridden method.

        Example (Sardine):
            model Animal {
                open method speak() { show("...") }
            }
            model Dog: Animal {
                open method speak() {
                    super().speak()   # calls Animal.speak()
                    show("Woof!")
                }
            }
        """
        from sards.core import RunTimeResult
        from sards.oops_types import SuperProxy

        res = RunTimeResult()

        if pos_args or kw_args:
            return res.failure(
                ArgumentError(
                    self.pos_start, self.pos_end,
                    "super() takes no arguments",
                    exec_context
                )
            )

        # Built-in exec_context is freshly generated; walk the parent chain to
        # find the method context that carries 'this' and owner_class.
        search_ctx = self.context   # self.context = the scope super() was called from
        instance = None
        owner_class = None
        while search_ctx is not None:
            if instance is None:
                candidate = search_ctx.symbol_table.get("this") if search_ctx.symbol_table else None
                if candidate is not None:
                    instance = candidate
            if owner_class is None and search_ctx.owner_class is not None:
                owner_class = search_ctx.owner_class
            if instance is not None and owner_class is not None:
                break
            search_ctx = search_ctx.parent

        if instance is None:
            return res.failure(
                ArgumentError(
                    self.pos_start, self.pos_end,
                    "super() can only be called inside a method body",
                    exec_context
                )
            )

        if owner_class is None:
            return res.failure(
                ArgumentError(
                    self.pos_start, self.pos_end,
                    "super() could not determine the current class \u2014 "
                    "make sure you are calling it inside a named method",
                    exec_context
                )
            )

        proxy = SuperProxy(instance, owner_class)
        proxy.set_context(self.context)
        proxy.set_pos(self.pos_start, self.pos_end)
        return res.success(proxy)

    def execute_is_a(self, pos_args, kw_args, exec_context):
        """
        Executes the 'is_a()' built-in.

        Checks whether an object is an instance of the given model or any of
        its ancestor models (polymorphic type check).

        Signature:  is_a(obj, ModelClass) -> 1 (True) or 0 (False)

        Example (Sardine):
            d = Dog("Buddy", 3, "Woof", "Lab")
            show(is_a(d, Dog))     # 1
            show(is_a(d, Animal))  # 1  — Dog inherits from Animal
            show(is_a(d, Person))  # 0
        """
        from sards.core import RunTimeResult
        from sards.oops_types import ModelInstance, Model

        res = RunTimeResult()

        if len(pos_args) != 2 or kw_args:
            return res.failure(
                ArgumentError(
                    self.pos_start, self.pos_end,
                    "is_a() takes exactly 2 positional arguments: is_a(object, ModelClass)",
                    exec_context
                )
            )

        obj, model_class = pos_args

        if not isinstance(model_class, Model):
            return res.failure(
                ArgumentError(
                    self.pos_start, self.pos_end,
                    "Second argument to is_a() must be a model class",
                    exec_context
                )
            )

        if not isinstance(obj, ModelInstance):
            # Primitive types are never instances of any user-defined model
            return res.success(Number(0))

        # Use the existing is_descendant_of helper which already handles MRO
        result = obj.model.is_descendant_of(model_class)
        return res.success(Number(1 if result else 0))

    def execute_error(self, pos_args, kw_args, exec_context):
        from sards.core import RunTimeResult
        from sards.core.error import IllegalOperationError
        res = RunTimeResult()

        if kw_args:
            return res.failure(
                ArgumentError(
                    self.pos_start, self.pos_end,
                    "error() takes no keyword arguments",
                    exec_context
                )
            )

        msg = "Illegal operation"
        if len(pos_args) >= 1:
            msg = pos_args[0].value

        return res.failure(
            IllegalOperationError(
                self.pos_start, self.pos_end,
                msg,
                exec_context.parent
            )
        )

    def execute_len(self, pos_args, kw_args, exec_context):
        from sards.core import RunTimeResult
        from sards.data_types import Number, List, String, Dict
        from sards.core.error import IllegalOperationError
        res = RunTimeResult()

        if len(pos_args) != 1 or kw_args:
            return res.failure(
                ArgumentError(
                    self.pos_start, self.pos_end,
                    "len() takes exactly 1 argument",
                    exec_context
                )
            )

        arg = pos_args[0]
        if isinstance(arg, List):
            val = len(arg.elements)
        elif isinstance(arg, String):
            val = len(arg.value)
        elif isinstance(arg, Dict):
            val = len(arg.elements)
        else:
            return res.failure(
                IllegalOperationError(
                    self.pos_start, self.pos_end,
                    f"Type '{type(arg).__name__}' has no length",
                    exec_context
                )
            )

        return res.success(Number(val))

    def execute_range(self, pos_args, kw_args, exec_context):
        from sards.core import RunTimeResult
        from sards.data_types import Number, List
        from sards.core.error import IllegalOperationError
        res = RunTimeResult()

        if len(pos_args) < 1 or len(pos_args) > 3 or kw_args:
            return res.failure(
                ArgumentError(
                    self.pos_start, self.pos_end,
                    "range() takes 1, 2, or 3 arguments",
                    exec_context
                )
            )

        for idx, arg in enumerate(pos_args):
            if not isinstance(arg, Number) or isinstance(arg.value, float):
                return res.failure(
                    IllegalOperationError(
                        arg.pos_start, arg.pos_end,
                        f"Argument {idx + 1} to range() must be an integer Number",
                        exec_context
                    )
                )

        vals = [arg.value for arg in pos_args]
        if len(vals) == 1:
            start = 0
            end = vals[0]
            step = 1
        elif len(vals) == 2:
            start = vals[0]
            end = vals[1]
            step = 1
        else:
            start = vals[0]
            end = vals[1]
            step = vals[2]

        if step == 0:
            return res.failure(
                IllegalOperationError(
                    pos_args[-1].pos_start, pos_args[-1].pos_end,
                    "range() step cannot be 0",
                    exec_context
                )
            )

        elements = []
        for i in range(start, end, step):
            elements.append(Number(i).set_context(exec_context))

        return res.success(
            List(elements)
            .set_context(exec_context)
            .set_pos(self.pos_start, self.pos_end)
        )

    def execute_exit(self, pos_args, kw_args, exec_context):
        from sards.core import RunTimeResult
        res = RunTimeResult()
        if pos_args or kw_args:
            return res.failure(
                ArgumentError(
                    self.pos_start, self.pos_end,
                    "exit() takes no arguments",
                    exec_context
                )
            )
        import sys
        sys.exit(0)


class BoundMethod:
    """
    Wraps a Python function and binds it to a primitive instance.
    When executed, it passes the instance as the first argument.
    """
    def __init__(self, name, instance, python_func):
        self.name = name
        self.instance = instance
        self.python_func = python_func
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

    def execute(self, pos_args, kw_args, call_context=None):
        from sards.core import RunTimeResult
        res = RunTimeResult()
        val = res.register(self.python_func(self.instance, pos_args, kw_args, call_context))
        if res.should_return():
            return res
        return res.success(val)

    def copy(self):
        copy = BoundMethod(self.name, self.instance, self.python_func)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<bound method {self.name} of {self.instance}>"


BuiltInFunction.show = BuiltInFunction('show')
BuiltInFunction.listen = BuiltInFunction('listen')
BuiltInFunction.Integer = BuiltInFunction('Integer')
BuiltInFunction.String = BuiltInFunction('String')
BuiltInFunction.type = BuiltInFunction('type')
BuiltInFunction.super = BuiltInFunction('super')
BuiltInFunction.is_a = BuiltInFunction('is_a')
BuiltInFunction.error = BuiltInFunction('error')
BuiltInFunction.len = BuiltInFunction('len')
BuiltInFunction.range = BuiltInFunction('range')
BuiltInFunction.exit = BuiltInFunction('exit')