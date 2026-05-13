from sards.data_types import Number
from sards.oops_types import ModelInstance
from sards.user_functions import Function


class Model:
    """
    Represents a class blueprint at runtime.
    """

    def __init__(self, name, all_attributes, init_node, method_nodes, parents=None):
        self.name = name
        self.all_attributes = all_attributes
        self.init_node = init_node
        self.method_nodes = method_nodes
        self.parents = parents or []
        self.pos_start = None
        self.pos_end = None
        self.context = None

    def find_method(self, name):
        if name in self.method_nodes:
            return self.method_nodes[name]
        for parent in self.parents:
            method_info = parent.find_method(name)
            if method_info:
                return method_info
        return None

    def find_method_owner(self, name):
        if name in self.method_nodes:
            return self
        for parent in self.parents:
            owner = parent.find_method_owner(name)
            if owner:
                return owner
        return None

    def find_attribute(self, name):
        for attr_name, _, _ in self.all_attributes:
            if name == attr_name:
                return next((attr for attr in self.all_attributes if attr[0] == name), None)
        for parent in self.parents:
            attr_info = parent.find_attribute(name)
            if attr_info:
                return attr_info
        return None

    def find_attribute_owner(self, name):
        for attr_name, _, _ in self.all_attributes:
            if name == attr_name:
                return self
        for parent in self.parents:
            owner = parent.find_attribute_owner(name)
            if owner:
                return owner
        return None

    def is_descendant_of(self, other_model):
        if self.name == other_model.name:
            return True
        for p in self.parents:
            if p.is_descendant_of(other_model):
                return True
        return False

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def execute(self, pos_args, kw_args):
        from sards.core import Context, RunTimeResult, Interpreter, ArgumentError

        res = RunTimeResult()
        interpreter = Interpreter()

        instance = ModelInstance(self)
        instance.set_context(self.context)
        instance.set_pos(self.pos_start, self.pos_end)

        if self.context:
            instance.symbol_table.parent = self.context.symbol_table

        full_attr_list = self.all_attributes[:]
        for p in self.parents:
            full_attr_list = p.all_attributes + full_attr_list

        for name, default_value_node, access_level in full_attr_list:
            if default_value_node:
                default_value = res.register(interpreter.visit(default_value_node, self.context))
                if res.should_return(): return res
                instance.symbol_table.set(name, default_value)
            else:
                instance.symbol_table.set(name, Number(0))

        if self.init_node:
            init_func = Function(
                "init",
                self.init_node.body_node,
                self.init_node.param_nodes,
                False
            ).set_context(self.context)
            init_func.set_pos(self.init_node.pos_start, self.init_node.pos_end)

            exec_context = Context("init", self.context, self.pos_start)
            exec_context.symbol_table = instance.symbol_table
            exec_context.symbol_table.set("this", instance)

            res.register(init_func.check_and_populate_args(
                init_func.param_nodes,
                pos_args,
                kw_args,
                exec_context
            ))
            if res.should_return(): return res

            res.register(interpreter.visit(init_func.body_node, exec_context))
            if res.should_return(): return res

        elif pos_args or kw_args:
            return res.failure(ArgumentError(
                self.pos_start, self.pos_end,
                f"'{self.name}' does not have an 'init' method and takes no arguments for instantiation",
                self.context
            ))

        return res.success(instance)

    def copy(self):
        copy = Model(self.name, self.all_attributes, self.init_node, self.method_nodes, self.parents)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<model {self.name}>"