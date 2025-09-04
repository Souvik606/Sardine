"""
This module defines the ForNode class, which represents
a 'while' loop node in the abstract syntax tree (AST).

Classes:
    WhileNode: A class to represent a 'while' loop node in the AST.
"""
class WhileNode:
    """
    Represents a 'while' loop node in the abstract syntax tree (AST).

    Attributes:
        condition_node: The node representing the condition value of the loop.
        body_node: The node representing the body of the loop.
        pos_start: The starting position of the 'while' loop in the source code.
        pos_end: The ending position of the 'while' loop in the source code.
        return_null: A flag indicating whether the loop returns null.
    """
    def __init__(self, condition_node, body_node, return_null):
        self.condition_node = condition_node
        self.body_node = body_node
        self.pos_start = self.condition_node.pos_start
        self.pos_end = self.body_node.pos_end
        self.return_null = return_null

    def __repr__(self):
        return f'{self.condition_node}:{self.body_node}'
