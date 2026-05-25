class ForEachLoopNode:  # pylint: disable=R0903
    """
    Represents a 'trace' loop node in the abstract syntax tree (AST).

    Attributes:
        var_name_tokens: A list of tokens for the loop variable(s)
                         (e.g., 'item' or 'key', 'value').
        collection_node: The node representing the collection to iterate over.
        body_node: The node representing the body of the loop.
        pos_start: The starting position of the trace-expression.
        pos_end: The ending position of the trace-expression.
    """
    def __init__(self, var_name_tokens, collection_node, body_node):
        self.var_name_tokens = var_name_tokens
        self.collection_node = collection_node
        self.body_node = body_node
        self.pos_start = self.var_name_tokens[0].pos_start
        self.pos_end = self.body_node.pos_end

    def __repr__(self):
        return (f"(Trace {self.var_name_tokens} <- {self.collection_node} "
                f"Body: {self.body_node})")