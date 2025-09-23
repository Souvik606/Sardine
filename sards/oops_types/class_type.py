from sards.ast_nodes import SymbolTable
from sards.oops_types import ModelInstance
from sards.user_functions import Function

class Model:
    """
    Represents a class blueprint at runtime.
    """
    def __init__(self, name, attr_nodes, init_node, method_nodes):
        self.name = name
        self.attr_nodes = attr_nodes
        self.init_node = init_node
        self.method_nodes = method_nodes
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

    def execute(self, args):
        from sards.core import Context, RunTimeResult, Interpreter

        res = RunTimeResult()
        interpreter = Interpreter()
        instance = ModelInstance(self)
        instance.set_context(self.context)
        instance.set_pos(self.pos_start, self.pos_end)

        instance.symbol_table.parent = self.context.symbol_table
        
        for attr_node in self.attr_nodes:
            for name_tok, default_value_node in attr_node.declarations:
                if default_value_node:
                    default_value = res.register(interpreter.visit(default_value_node, self.context))
                    if res.should_return(): return res
              
                    instance.symbol_table.set(name_tok.value, default_value)
       
        if self.init_node:
            init_func = Function("init",
                self.init_node.body_node,
                [tok.value for tok in self.init_node.param_name_toks],
                False
            ).set_context(self.context)

            exec_context = Context("init", self.context, self.pos_start)
            exec_context.symbol_table = SymbolTable(instance.symbol_table)
            exec_context.symbol_table.set("this", instance)

            res.register(init_func.check_and_populate_args(init_func.arg_names, args, exec_context))
            if res.should_return(): return res

            res.register(interpreter.visit(init_func.body_node, exec_context))
            if res.should_return(): return res

        return res.success(instance)

    def copy(self):
        copy = Model(self.name, self.attr_nodes, self.init_node, self.method_nodes)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<model {self.name}>"