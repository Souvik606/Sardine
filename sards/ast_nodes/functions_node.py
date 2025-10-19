"""
This module defines the FunctionDefinitionNode and FunctionCallNode classes,
which represent function definition and function call nodes in the abstract syntax tree (AST).

Classes:
    FunctionDefinitionNode: A class to represent a function definition node in the AST.
    FunctionCallNode: A class to represent a function call node in the AST.
"""

class FunctionDefinitionNode:
    """
    Represents a function OR method definition in the AST.
    """

    def __init__(self, var_name_tok, arg_name_toks, body_node, auto_return, access_modifier_tok=None):
        self.var_name_tok = var_name_tok
        self.arg_name_toks = arg_name_toks
        self.body_node = body_node
        self.auto_return = auto_return
        self.access_modifier_tok = access_modifier_tok

        if self.access_modifier_tok:
            self.pos_start = self.access_modifier_tok.pos_start
        elif self.var_name_tok:
            self.pos_start = self.var_name_tok.pos_start
        elif len(self.arg_name_toks) > 0:
            self.pos_start = self.arg_name_toks[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start

        self.pos_end = self.body_node.pos_end

    def __repr__(self):
        return (f'{self.access_modifier_tok}:{self.var_name_tok}:'
                f'{self.arg_name_toks}:{self.body_node}')

class FunctionCallNode: # pylint: disable=R0903
    """
    Represents a function call node in the abstract syntax tree (AST).

    Attributes:
        call_node: The node representing the function being called.
        arg_nodes: A list of nodes representing the arguments passed to the function.
        pos_start: The starting position of the function call in the source code.
        pos_end: The ending position of the function call in the source code.
    """
    def __init__(self, call_node, arg_nodes):
        self.call_node = call_node
        self.arg_nodes = arg_nodes

        self.pos_start = self.call_node.pos_start

        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[-1].pos_end
        else:
            self.pos_end = self.call_node.pos_end

    def __repr__(self):
        return f'{self.call_node}:{self.arg_nodes}'