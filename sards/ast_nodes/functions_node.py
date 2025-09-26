"""
This module defines the FunctionDefinitionNode and FunctionCallNode classes,
which represent function definition and function call nodes in the abstract syntax tree (AST).

Classes:
    FunctionDefinitionNode: A class to represent a function definition node in the AST.
    FunctionCallNode: A class to represent a function call node in the AST.
"""

class FunctionDefinitionNode: # pylint: disable=R0903
    """
    Represents a function definition node in the abstract syntax tree (AST).

    Attributes:
        var_name_tok: The token representing the function name.
        arg_name_toks: A list of tokens representing the argument names.
        body_node: The node representing the body of the function.
        auto_return: A flag indicating whether the function automatically returns
                     the last evaluated expression.
        pos_start: The starting position of the function definition in the source code.
        pos_end: The ending position of the function definition in the source code.
    """
    def __init__(self, var_name_tok, arg_name_toks, body_node, auto_return):
        self.var_name_tok = var_name_tok
        self.arg_name_toks = arg_name_toks
        self.body_node = body_node
        self.auto_return = auto_return

        if self.var_name_tok:
            self.pos_start = self.var_name_tok.pos_start
        elif len(self.arg_name_toks) > 0:
            self.pos_start = self.arg_name_toks[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start

        self.pos_end = self.body_node.pos_end

    def __repr__(self):
        return f'{self.var_name_tok}:{self.arg_name_toks}:{self.body_node}'


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