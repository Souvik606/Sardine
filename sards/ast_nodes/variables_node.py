"""
This module defines the SymbolTable, VariableUseNode, and VariableAssignNode classes,
which represent variable-related nodes and symbol tables in the abstract syntax tree (AST).

Classes:
    SymbolTable: A class to represent a symbol table for storing variable names and values.
    VariableUseNode: A class to represent a variable usage node in the AST.
    VariableAssignNode: A class to represent a variable assignment node in the AST.
"""

class SymbolTable: # pylint: disable=R0903
    """
    Represents a symbol table for storing variable names and values.

    Attributes:
        symbols: A dictionary to store variable names and their corresponding values.
        parent: A reference to the parent symbol table, if any.
    """
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def get(self, name):
        """
        Retrieves the value of a variable from the symbol table.

        Args:
            name: The name of the variable.

        Returns:
            The value of the variable, or None if the variable is not found.
        """
        value = self.symbols.get(name, None)
        if value is None and self.parent:
            return self.parent.get(name)
        return value

    def set(self, name, value):
        """
        Sets the value of a variable in the symbol table.

        Args:
            name: The name of the variable.
            value: The value to assign to the variable.
        """
        self.symbols[name] = value

    def remove(self, name):
        """
        Removes a variable from the symbol table.

        Args:
            name: The name of the variable to remove.
        """
        del self.symbols[name]

class VariableUseNode: # pylint: disable=R0903
    """
    Represents a variable usage node in the abstract syntax tree (AST).

    Attributes:
        var_name_tok: The token representing the variable name.
        pos_start: The starting position of the variable usage in the source code.
        pos_end: The ending position of the variable usage in the source code.
    """
    def __init__(self, var_name_tok, index_node=None):
        if index_node is None:
            index_node = []
        self.var_name_tok = var_name_tok
        self.index_node=index_node
        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.var_name_tok.pos_end if not index_node else self.index_node[-1].pos_end

    def __repr__(self):
        if not self.index_node: return f'({self.var_name_tok.value})'
        else:return f'({self.var_name_tok.value}:{self.index_node})'


class VariableAssignNode:  # pylint: disable=R0903
    """
    Represents one or more variable assignments in the AST.

    Attributes:
        var_name_toks: List of tokens representing variable names.
        value_nodes: List of nodes representing values to assign.
        index_nodes: List of lists of index nodes (parallel to var_name_toks).
        pos_start: The starting position of the assignment.
        pos_end: The ending position of the assignment.
    """
    def __init__(self, var_name_toks, value_nodes, index_nodes=None):
        if index_nodes is None:
            index_nodes = [None] * len(var_name_toks)

        self.var_name_toks = var_name_toks
        self.value_nodes = value_nodes
        self.index_nodes = index_nodes
        self.pos_start = self.var_name_toks[0].pos_start
        self.pos_end = self.value_nodes[-1].pos_end

    def __repr__(self):
        parts = []
        for tok, idxs, val in zip(self.var_name_toks, self.index_nodes, self.value_nodes):
            if not idxs:
                parts.append(f"({tok.value}:{val})")
            else:
                parts.append(f"(({tok.value}:{idxs}):{val})")
        return ",".join(parts)
