class TryNode:  # pylint: disable=R0903
    """
    Represents a 'try' (risk) block node in the abstract syntax tree (AST).

    Attributes:
        body_node: The node representing the body of the try block.
        trap_nodes: A list of CatchNode instances (trap blocks).
        clean_node: A FinallyNode instance (clean block).
        pos_start: The starting position of the try-expression.
        pos_end: The ending position of the try-expression.
    """
    def __init__(self, body_node, trap_nodes=None, clean_node=None):
        self.body_node = body_node
        self.trap_nodes = trap_nodes or []
        self.clean_node = clean_node
        self.pos_start = self.body_node.pos_start
        self.pos_end = (
            self.clean_node.pos_end if self.clean_node
            else (self.trap_nodes[-1].pos_end if self.trap_nodes
                  else self.body_node.pos_end)
        )

    def __repr__(self):
        return f"{self.body_node}, Traps: {self.trap_nodes},{self.clean_node})"


class CatchNode:  # pylint: disable=R0903
    """
    Represents a 'catch' (trap) block node in the abstract syntax tree (AST).

    Attributes:
        error_type: The token representing the error type.
        error_name: The token representing the error variable name (optional).
        body_node: The node representing the body of the trap block.
        pos_start: The starting position of the trap block.
        pos_end: The ending position of the trap block.
    """
    def __init__(self, error_type=None, error_name=None, body_node=None):
        self.error_type = error_type
        self.error_name = error_name
        self.body_node = body_node
        self.pos_start = (
            self.error_type.pos_start if self.error_type
            else self.body_node.pos_start
        )
        self.pos_end = self.body_node.pos_end

    def __repr__(self):
        return f"{self.error_type}, {self.error_name}, {self.body_node}"


class FinallyNode:  # pylint: disable=R0903
    """
    Represents a 'finally' (clean) block node in the abstract syntax tree (AST).

    Attributes:
        body_node: The node representing the body of the clean block.
        pos_start: The starting position of the clean block.
        pos_end: The ending position of the clean block.
    """
    def __init__(self, body_node):
        self.body_node = body_node
        self.pos_start = self.body_node.pos_start
        self.pos_end = self.body_node.pos_end

    def __repr__(self):
        return f" {self.body_node}"