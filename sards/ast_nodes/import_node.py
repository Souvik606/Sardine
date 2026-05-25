"""
This module defines SummonNode, which represents a Sardine import statement.

Grammar variants:
  summon math
  summon math as m
  summon sin, cos from math
  summon factorial as fact from math
  summon * from math
"""


class SummonNode:
    """
    AST node for a 'summon' (import) statement.

    Attributes:
        module_tok     : Token — the module name identifier, e.g. Token(IDENTIFIER, 'math')
        names          : list of (original_tok, alias_tok | None)
                         Empty list means "import the whole module".
        module_alias   : Token | None — alias used when importing the whole module
                         ('summon math as m' → module_alias.value == 'm')
        wildcard       : bool — True for 'summon * from math'
        pos_start      : Position
        pos_end        : Position
    """

    def __init__(self, module_tok, names=None, module_alias=None, wildcard=False,
                 pos_start=None, pos_end=None):
        self.module_tok = module_tok
        self.names = names or [] 
        self.module_alias = module_alias  # Token or None
        self.wildcard = wildcard          # bool

        self.pos_start = pos_start or module_tok.pos_start
        self.pos_end = pos_end or module_tok.pos_end

    def __repr__(self):
        if self.wildcard:
            return f"(summon * from {self.module_tok.value})"
        if self.names:
            pairs = ", ".join(
                f"{o.value} as {a.value}" if a else o.value
                for o, a in self.names
            )
            return f"(summon {pairs} from {self.module_tok.value})"
        alias = f" as {self.module_alias.value}" if self.module_alias else ""
        return f"(summon {self.module_tok.value}{alias})"
