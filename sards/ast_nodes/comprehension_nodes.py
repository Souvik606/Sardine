"""
AST Nodes for list and dictionary comprehensions in Sardine.

Comprehension Syntax:
  List via Cycle : [expr Cycle var = start : end (: step)? (when cond)?]
  List via trace : [expr trace var <- collection (when cond)?]
  Dict via Cycle : {key_expr : val_expr Cycle var = start : end (: step)? (when cond)?}
  Dict via trace : {key_expr : val_expr trace var <- collection (when cond)?}
"""


class ListComprehensionNode:
    """
    Represents a list comprehension expression.

    Attributes:
        expr_node       : the expression to collect (one per iteration)
        loop_type       : 'Cycle' | 'trace'
        --- Cycle-specific ---
        var_name_tok    : loop variable token  (Cycle)
        start_node      : start expression     (Cycle)
        end_node        : end expression       (Cycle)
        step_node       : step expression or None (Cycle)
        --- trace-specific ---
        var_name_tokens : list of variable tokens (trace)
        collection_node : collection to iterate   (trace)
        --- shared ---
        condition_node  : optional filter expression (when clause) or None
        pos_start / pos_end
    """

    def __init__(self, expr_node, loop_type,
                 var_name_tok=None, start_node=None, end_node=None, step_node=None,
                 var_name_tokens=None, collection_node=None,
                 condition_node=None,
                 pos_start=None, pos_end=None):
        self.expr_node = expr_node
        self.loop_type = loop_type

        # Cycle fields
        self.var_name_tok = var_name_tok
        self.start_node = start_node
        self.end_node = end_node
        self.step_node = step_node

        # trace fields
        self.var_name_tokens = var_name_tokens
        self.collection_node = collection_node

        # shared optional filter
        self.condition_node = condition_node

        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'ListComp({self.loop_type}, expr={self.expr_node!r})'


class DictComprehensionNode:
    """
    Represents a dictionary comprehension expression.

    Attributes:
        key_node        : expression for each key
        val_node        : expression for each value
        loop_type       : 'Cycle' | 'trace'
        (same Cycle / trace / condition fields as ListComprehensionNode)
    """

    def __init__(self, key_node, val_node, loop_type,
                 var_name_tok=None, start_node=None, end_node=None, step_node=None,
                 var_name_tokens=None, collection_node=None,
                 condition_node=None,
                 pos_start=None, pos_end=None):
        self.key_node = key_node
        self.val_node = val_node
        self.loop_type = loop_type

        # Cycle fields
        self.var_name_tok = var_name_tok
        self.start_node = start_node
        self.end_node = end_node
        self.step_node = step_node

        # trace fields
        self.var_name_tokens = var_name_tokens
        self.collection_node = collection_node

        # shared optional filter
        self.condition_node = condition_node

        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        return f'DictComp({self.loop_type}, key={self.key_node!r}, val={self.val_node!r})'
