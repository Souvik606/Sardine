"""
module_type.py

Defines the Module value type — a first-class value that wraps a loaded
Sardine module's symbol table, allowing dot-access on module members.

Example:
    summon math           # math is a Module instance
    show(math.PI)         # delegates to math's symbol table
"""

from sards.core.error import AttributeError as SardineAttributeError


class Module:
    """
    Represents a fully loaded Sardine module as a runtime value.

    Attributes:
        name (str)              : The short module name (e.g. 'math').
        symbol_table            : The SymbolTable produced when the module was executed.
        pos_start, pos_end      : Positional info (set after construction).
        context                 : Runtime context (set after construction).
    """

    def __init__(self, name, symbol_table):
        self.name = name
        self.symbol_table = symbol_table
        self.pos_start = None
        self.pos_end = None
        self.context = None

    # ------------------------------------------------------------------
    # Standard value interface
    # ------------------------------------------------------------------

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def copy(self):
        copy = Module(self.name, self.symbol_table)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    # ------------------------------------------------------------------
    # Attribute access — supports  module.name
    # ------------------------------------------------------------------

    def get_attr(self, name, _calling_context=None):
        value = self.symbol_table.get(name)
        if value is None:
            return None, SardineAttributeError(
                self.pos_start, self.pos_end,
                f"Module '{self.name}' has no member '{name}'",
                self.context
            )
        return value, None

    # ------------------------------------------------------------------
    # Truthiness / repr
    # ------------------------------------------------------------------

    def is_true(self):
        from sards.data_types.number_type import Number
        return Number(1), None

    def __repr__(self):
        return f"<module '{self.name}'>"
