"""
This module defines the ReturnNode, ContinueNode, and BreakNode classes,
which represent jump statements in the abstract syntax tree (AST).

Classes:
    ReturnNode: A class to represent a 'return' statement node in the AST.
    ContinueNode: A class to represent a 'continue' statement node in the AST.
    BreakNode: A class to represent a 'break' statement node in the AST.
"""

class ReturnNode:  # pylint: disable=R0903
    """
    Represents a 'yield' (return) statement node in the abstract syntax tree (AST).

    Attributes:
        nodes_to_return: A list of nodes representing the values to return.
        This list can be empty (for a bare 'yield').
        pos_start: The starting position of the 'yield' statement in the source code.
        pos_end: The ending position of the 'yield' statement in the source code.
    """
    def __init__(self, nodes_to_return, pos_start, pos_end):
        self.nodes_to_return = nodes_to_return
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'({self.nodes_to_return})'

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
