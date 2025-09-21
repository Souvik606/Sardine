"""
This module defines the ReturnNode, ContinueNode, and BreakNode classes,
which represent jump statements in the abstract syntax tree (AST).

Classes:
    ReturnNode: A class to represent a 'return' statement node in the AST.
    ContinueNode: A class to represent a 'continue' statement node in the AST.
    BreakNode: A class to represent a 'break' statement node in the AST.
"""

class ReturnNode: # pylint: disable=R0903
    """
    Represents a 'return' statement node in the abstract syntax tree (AST).

    Attributes:
        node_to_return: The node representing the value to return.
        pos_start: The starting position of the 'return' statement in the source code.
        pos_end: The ending position of the 'return' statement in the source code.
    """
    def __init__(self, node_to_return, pos_start, pos_end):
        self.node_to_return = node_to_return
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'({self.node_to_return})'

class ContinueNode: # pylint: disable=R0903
    """
    Represents a 'continue' statement node in the abstract syntax tree (AST).

    Attributes:
        pos_start: The starting position of the 'continue' statement in the source code.
        pos_end: The ending position of the 'continue' statement in the source code.
    """
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end

class BreakNode: # pylint: disable=R0903
    """
    Represents a 'break' statement node in the abstract syntax tree (AST).

    Attributes:
        pos_start: The starting position of the 'break' statement in the source code.
        pos_end: The ending position of the 'break' statement in the source code.
    """
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end
