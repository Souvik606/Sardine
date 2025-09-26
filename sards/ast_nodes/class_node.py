class ModelNode:  # pylint: disable=R0903
    """
    Represents a 'model' (class) definition in the AST.

    Attributes:
        name_tok: The token for the model's name.
        body_nodes: A list of nodes inside the model (AttrNode, InitNode, FunctionDefinitionNode).
        pos_start: The starting position of the model definition.
        pos_end: The ending position of the model definition.
    """
    def __init__(self, name_tok, body_nodes):
        self.name_tok = name_tok
        self.body_nodes = body_nodes

        self.pos_start = self.name_tok.pos_start
        self.pos_end = (
            self.body_nodes[-1].pos_end if self.body_nodes
            else self.name_tok.pos_end
        )

    def __repr__(self):
        return f"(Model: {self.name_tok.value}, Body: {self.body_nodes})"


class AttrNode:  # pylint: disable=R0903
    """
    Represents an 'attr' declaration in the AST.

    Attributes:
        declarations: A list of tuples, where each tuple contains
                      (identifier_token, optional_default_value_node).
        pos_start: The starting position of the 'attr' keyword.
        pos_end: The ending position of the closing '>'.
    """
    def __init__(self, declarations, pos_start, pos_end):
        self.declarations = declarations
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f"(Attributes: {self.declarations})"


class InitNode:  # pylint: disable=R0903
    """
    Represents an 'init' (constructor) definition in the AST.

    Attributes:
        param_name_toks: A list of tokens for the parameter names.
        body_node: The node representing the body of the constructor.
        pos_start: The starting position of the 'init' keyword.
        pos_end: The ending position of the constructor body.
    """
    def __init__(self, param_name_toks, body_node, pos_start, pos_end):
        self.param_name_toks = param_name_toks
        self.body_node = body_node
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        params = [p.value for p in self.param_name_toks]
        return f"(Init: ({params}), Body: {self.body_node})"


class AttrAccessNode:  # pylint: disable=R0903
    """
    Represents accessing an attribute of an object (e.g., obj.attr).

    Attributes:
        object_node: The node representing the object being accessed.
        attr_name_tok: The token for the attribute's name.
        pos_start: The starting position of the object node.
        pos_end: The ending position of the attribute name token.
    """
    def __init__(self, object_node, attr_name_tok):
        self.object_node = object_node
        self.attr_name_tok = attr_name_tok

        self.pos_start = self.object_node.pos_start
        self.pos_end = self.attr_name_tok.pos_end

    def __repr__(self):
        return f"({self.object_node}.{self.attr_name_tok.value})"