class ModelNode:
    """
    Represents a 'model' (class) definition in the AST.
    """

    def __init__(self, name_tok, parent_name_toks, body_nodes):
        self.name_tok = name_tok
        self.parent_name_toks = parent_name_toks
        self.body_nodes = body_nodes

        self.pos_start = self.name_tok.pos_start
        self.pos_end = (
            self.body_nodes[-1].pos_end if self.body_nodes
            else (self.parent_name_toks[-1].pos_end if self.parent_name_toks
                  else self.name_tok.pos_end)
        )

    def __repr__(self):
        return f"(Model: {self.name_tok.value}, Parents: {self.parent_name_toks}, Body: {self.body_nodes})"


class AttrNode:
    """
    Represents an 'attr' declaration in the AST.
    """

    def __init__(self, declarations, access_modifier_tok, pos_start, pos_end):
        self.declarations = declarations
        self.access_modifier_tok = access_modifier_tok
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f"(Attributes: {self.declarations}, Access: {self.access_modifier_tok})"


class InitNode:  # pylint: disable=R0903
    """
    Represents an 'init' (constructor) definition in the AST.
    Now supports default parameter values.

    Attributes:
        param_nodes: A list of tuples: [(name_tok, default_value_node), ...]
                     default_value_node is None if no default.
        body_node: The node representing the body of the constructor.
        pos_start: The starting position of the 'init' keyword.
        pos_end: The ending position of the constructor body.
    """
    def __init__(self, param_nodes, body_node, pos_start, pos_end):
        self.param_nodes = param_nodes
        self.body_node = body_node
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        # Updated __repr__ to show parameters and their defaults
        param_reprs = []
        for name_tok, default_value in self.param_nodes:
            if default_value:
                param_reprs.append(f"({name_tok.value}={default_value})")
            else:
                param_reprs.append(name_tok.value)
        return f"(Init: ({', '.join(param_reprs)}), Body: {self.body_node})"


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