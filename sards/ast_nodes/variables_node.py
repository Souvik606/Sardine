"""
This module defines the SymbolTable, VariableUseNode, and VariableAssignNode classes,
which represent variable-related nodes and symbol tables in the abstract syntax tree (AST).

Classes:
    SymbolTable: A class to represent a symbol table for storing variable names and values.
    VariableUseNode: A class to represent a variable usage node in the AST.
    AssignNode: A class to represent an assignment node in the AST.
    IndexAccessNode: A class to represent index access on any node.
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

    def __repr__(self):
        table=''

        for key,val in self.symbols.items():
            table+=f'{key}:{val} '

        return table

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


class IndexAccessNode:
    """
    Represents index access on an object.
    """
    def __init__(self, object_node, index_node):
        self.object_node = object_node
        self.index_node = index_node
        self.pos_start = self.object_node.pos_start
        self.pos_end = self.index_node.pos_end

    def __repr__(self):
        return f"({self.object_node}[{self.index_node}])"

class AssignNode:
    """
    Represents one or more assignments in the AST.
    """
    def __init__(self, left_nodes, value_nodes):
        self.left_nodes = left_nodes
        self.value_nodes = value_nodes
        self.pos_start = self.left_nodes[0].pos_start
        self.pos_end = self.value_nodes[-1].pos_end

    def __repr__(self):
        parts = []
        for left, val in zip(self.left_nodes, self.value_nodes):
            parts.append(f"({left}:{val})")
        return ",".join(parts)
