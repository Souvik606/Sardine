"""
AST Node: FStringNode

Represents a $"..." interpolated string expression.
Each part is either:
  - ('literal', <str>)  — a plain text segment
  - ('expr',    <AST node>)  — an evaluated expression
"""


class FStringNode:
    """
    Represents a $"..." interpolated (f-string style) string literal.

    Attributes:
    - parts: list of tuples: ('literal', str) | ('expr', AST node)
    - pos_start: start position of the whole $"..." token
    - pos_end: end position of the whole $"..." token
    """

    def __init__(self, parts, pos_start, pos_end):
        self.parts = parts
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        parts_repr = ', '.join(
            f'lit:{p!r}' if kind == 'literal' else f'expr:{p!r}'
            for kind, p in self.parts
        )
        return f'FStringNode([{parts_repr}])'
