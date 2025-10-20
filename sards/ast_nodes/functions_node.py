class FunctionDefinitionNode:
    """
    Represents a function OR method definition in the AST.
    Now supports default parameter values.
    """
    def __init__(self, var_name_tok, param_nodes, body_node, auto_return, access_modifier_tok=None):
        self.var_name_tok = var_name_tok
        self.param_nodes = param_nodes
        self.body_node = body_node
        self.auto_return = auto_return
        self.access_modifier_tok = access_modifier_tok

        if self.access_modifier_tok:
            self.pos_start = self.access_modifier_tok.pos_start
        elif self.var_name_tok:
            self.pos_start = self.var_name_tok.pos_start
        elif len(self.param_nodes) > 0:
            self.pos_start = self.param_nodes[0][0].pos_start
        else:
            self.pos_start = self.body_node.pos_start

        self.pos_end = self.body_node.pos_end

    def __repr__(self):
        arg_reprs = []
        for arg_name, default_value in self.param_nodes:
            if default_value:
                arg_reprs.append(f"({arg_name}={default_value})")
            else:
                arg_reprs.append(f"{arg_name}")
        
        return (f'{self.access_modifier_tok}:{self.var_name_tok}:'
                f'ARGS=[{", ".join(arg_reprs)}]:{self.body_node}')


class FunctionCallNode:  # pylint: disable=R0903
    """
    Represents a function call node in the abstract syntax tree (AST).
    Now supports both positional and keyword arguments.
    """
    def __init__(self, call_node, positional_param_nodes, keyword_param_nodes):
        self.call_node = call_node
        self.positional_param_nodes = positional_param_nodes

        self.keyword_param_nodes = keyword_param_nodes

        self.pos_start = self.call_node.pos_start

        if len(self.keyword_param_nodes) > 0:
            self.pos_end = self.keyword_param_nodes[-1][1].pos_end
        elif len(self.positional_param_nodes) > 0:
            self.pos_end = self.positional_param_nodes[-1].pos_end
        else:
            self.pos_end = self.call_node.pos_end

    def __repr__(self):
        keyword_reprs = [f"({name}={value})" for name, value in self.keyword_param_nodes]
        all_args = self.positional_param_nodes + keyword_reprs
        return f'{self.call_node}:ARGS=({", ".join(map(str, all_args))})'