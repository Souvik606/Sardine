"""
Module: parser

This module implements a recursive descent parser for mathematical expressions.
It converts a sequence of tokens into an Abstract Syntax Tree (AST) by following
rules for arithmetic expressions, including handling unary and binary operations.

Classes:
- ParseResult: Stores the result of a parsing operation, including success or failure.
- NumberNode: Represents a numeric literal in the AST.
- UnaryOperationNode: Represents a unary operation (e.g., negation) in the AST.
- BinaryOperationNode: Represents a binary operation (e.g., addition, multiplication) in the AST.
- Parser: Performs parsing by analyzing token sequences and constructing an AST.

Methods:
- ParseResult:
  - register(res): Handles the propagation of errors and nodes during parsing.
  - success(node): Marks parsing as successful with a resulting node.
  - failure(error): Marks parsing as failed with an error.

- Parser:
  - advance(): Moves to the next token in the sequence.
  - parse(): Initiates parsing and returns the final AST or an error.
  - factor(): Parses factors (numbers, parentheses, unary operations).
  - term(): Parses terms (handles multiplication and division operations).
  - expression(): Parses full expressions (handles addition and subtraction operations).
"""

from sards.ast_nodes import *
from sards.ast_nodes.fstring_node import FStringNode
from sards.ast_nodes.comprehension_nodes import ListComprehensionNode, DictComprehensionNode
from sards.data_types import ListNode, StringNode, DictNode
from .constants import *
from .error import InvalidSyntaxError
from .lexer import Token, Lexer

class ParseResult:
    """Stores the result of a parsing operation, including errors and the parsed node."""

    def __init__(self):
        self.error = None
        self.node = None
        self.last_registered_advance_count = 0
        self.advance_count = 0
        self.to_reverse_count = 0

    def register_advancement(self):
        """Advances through token after parsing operation."""
        self.last_registered_advance_count = 1
        self.advance_count += 1

    def register(self, res):
        """Registers the result of a parsing operation, propagating errors and nodes."""
        self.last_registered_advance_count = res.advance_count
        self.advance_count += res.advance_count
        if res.error:
            self.error = res.error
        return res.node

    def success(self, node):
        """Marks the parsing as successful and stores the resulting node."""
        self.node = node
        return self

    def failure(self, error):
        """Marks the parsing as failed and stores the associated error."""
        if not self.error or self.advance_count == 0:
            self.error = error
        return self

    def try_register(self, res):
        """Registers the result of a parsing operation, returning None on encountering errors."""
        if res.error:
            self.to_reverse_count = res.advance_count
            return None
        return self.register(res)


class NumberNode: # pylint: disable=R0903
    """Represents a numeric literal in the Abstract Syntax Tree (AST)."""

    def __init__(self, token):
        self.token = token
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end

    def __repr__(self):
        return f'{self.token}'


class UnaryOperationNode: # pylint: disable=R0903
    """Represents a unary operation (e.g., negation) in the AST."""

    def __init__(self, operator, node):
        self.operator = operator
        self.node = node
        self.pos_start = self.operator.pos_start
        self.pos_end = self.node.pos_end

    def __repr__(self):
        return f'({self.operator}, {self.node})'


class BinaryOperationNode: # pylint: disable=R0903
    """Represents a binary operation (e.g., addition, multiplication) in the AST."""

    def __init__(self, left_node, operator, right_node):
        self.left_node = left_node
        self.operator = operator
        self.right_node = right_node
        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f'({self.left_node}, {self.operator}, {self.right_node})'


class TernaryOperationNode: # pylint: disable=R0903
    """Represents a ternary operation ( e.g. a>b ? show(a) : show(b) )"""

    def __init__(self, comp_node, true_node, false_node):
        self.comp_node = comp_node
        self.true_node = true_node
        self.false_node = false_node
        self.pos_start = self.comp_node.pos_start
        self.pos_end = self.false_node.pos_end

    def __repr__(self):
        return f'({self.comp_node} ? {self.true_node} : {self.false_node})'


class Parser: # pylint: disable=R0904
    """Performs recursive descent parsing of tokenized mathematical expressions."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.current_tok = None
        self.tok_index = -1
        self.current_depth = 0
        self.advance()

    def advance(self):
        """Moves to the next token in the token sequence."""
        self.tok_index += 1
        self.update_current_tok()
        return self.current_tok

    def reverse(self, amount=1):
        """Moves to a previous token in the token sequence by specified amount."""
        self.tok_index -= amount
        self.update_current_tok()
        return self.current_tok

    def _enter_depth(self):
        from sards.core.constants import MAX_AST_DEPTH
        self.current_depth += 1
        if self.current_depth > MAX_AST_DEPTH:
            return InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expression is too complex (maximum nesting depth of {MAX_AST_DEPTH} exceeded)"
            )
        return None

    def _exit_depth(self):
        self.current_depth -= 1

    def update_current_tok(self):
        """Updates current token in the token sequence."""
        if 0 <= self.tok_index < len(self.tokens):
            self.current_tok = self.tokens[self.tok_index]

    def peek(self):
        """Check the next token in the token sequence."""
        next_index = self.tok_index + 1
        if next_index < len(self.tokens):
            return self.tokens[next_index]
        return None

    def parse(self):
        """Initiates parsing and returns the final AST or an error if parsing fails."""
        result = self.multiline()

        if not result.error and self.current_tok.type != T_EOF:
            return result.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end,
                                   f"Unexpected token '{self.current_tok.value or self.current_tok.type}'"))
        return result

    def check_is_statement(self):
        current_tok_index=self.tok_index
        is_statement=False

        while self.current_tok.type!=T_NEWLINE and self.current_tok.type!=T_EOF:
            if self.current_tok.type==T_EQ:
                is_statement=True
                break
            self.advance()

        self.tok_index=current_tok_index
        self.update_current_tok()
        return is_statement

    def multiline(self):
        """
        Grammar Rule:
        multiline: NEWLINE* (singleline) (NEWLINE* (singleline))* NEWLINE*
        """

        res = ParseResult()
        statements = []
        pos_start = self.current_tok.pos_start.copy()

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        if self.current_tok.type!=T_EOF:
            first_stmt = res.register(self.singleline())
            if res.error:
                return res
            statements.append(first_stmt)

        while True:
            newlines_count = 0
            while self.current_tok.type == T_NEWLINE:
                res.register_advancement()
                self.advance()
                newlines_count += 1

            if self.current_tok.type!=T_EOF and self.current_tok.type!=T_RPAREN2 and not(
                self.current_tok.type==T_KEYWORD and self.current_tok.value in ("yield","escape","proceed")
            ):
                if newlines_count == 0 and len(statements) > 0:
                    prev_pos_end = statements[-1].pos_end
                    curr_pos_start = self.current_tok.pos_start
                    if prev_pos_end.line == curr_pos_start.line:
                        return res.failure(InvalidSyntaxError(
                            self.current_tok.pos_start, self.current_tok.pos_end,
                            "Expected newline to separate statements"
                        ))
                stmt = res.register(self.singleline())
                if res.error:
                    return res
                statements.append(stmt)
            else:
                break

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()
        result=res.success(ListNode(statements, pos_start, self.current_tok.pos_end.copy()))
        return result

    def singleline(self):
        res = ParseResult()
        token = self.current_tok

        if token.type == T_KEYWORD and token.value == 'model':
            class_def = res.register(self.class_definition())
            if res.error:
                return res
            return res.success(class_def)

        if token.type == T_KEYWORD and token.value == 'risk':
            exception_expr = res.register(self.exception_handling())
            if res.error:
                return res
            return res.success(exception_expr)

        if token.type == T_KEYWORD and token.value == 'when':
            if_expr = res.register(self.if_expression())
            if res.error:
                return res
            return res.success(if_expr)

        if token.type == T_KEYWORD and token.value == 'Cycle':
            for_expr = res.register(self.for_expression())
            if res.error:
                return res
            return res.success(for_expr)

        if token.type == T_KEYWORD and token.value == 'whenever':
            while_expr = res.register(self.while_expression())
            if res.error:
                return res
            return res.success(while_expr)

        if token.type == T_KEYWORD and token.value == 'method':
            method_expr = res.register(self.function_definition())
            if res.error:
                return res
            return res.success(method_expr)

        if token.type == T_KEYWORD and token.value == 'menu':
            switch_statement = res.register(self.switch_statement())
            if res.error:
                return res
            return res.success(switch_statement)

        if token.type == T_KEYWORD and token.value == 'trace':
            foreach_statement = res.register(self.foreach_expression())
            if res.error:
                return res
            return res.success(foreach_statement)

        if token.type == T_KEYWORD and token.value == 'summon':
            summon_stmt = res.register(self.summon_statement())
            if res.error:
                return res
            return res.success(summon_stmt)

        if token.type == T_IDENTIFIER:
            next_tok = self.peek()
            if next_tok and next_tok.type in (T_IDENTIFIER, T_LPAREN2, T_INT, T_FLOAT, T_STRING):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Invalid keyword '{token.value}'"
                ))

        # Try assignment first
        saved_tok_index = self.tok_index
        saved_current_tok = self.current_tok
        
        stmt = res.try_register(self.statements())
        if stmt:
            return res.success(stmt)
            
        self.tok_index = saved_tok_index
        self.current_tok = saved_current_tok
        
        # Fallback to expression
        expr = res.register(self.expression())
        if res.error:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   f"Unexpected token '{self.current_tok.value or self.current_tok.type}'"))
        return res.success(expr)

    def class_definition(self):
        """
        Grammar Rule:

        KEYWORD:model IDENTIFIER (COLON IDENTIFIER (COMMA IDENTIFIER)*)?
        LPAREN2 NEWLINE* (class-member NEWLINE*)* RPAREN2
        """
        res = ParseResult()

        if not(self.current_tok.type==T_KEYWORD and self.current_tok.value=="model"):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'model'"
            ))
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected a model name"
            ))
        model_name_tok = self.current_tok
        res.register_advancement()
        self.advance()

        parent_name_toks = []
        if self.current_tok.type == T_COLON:
            res.register_advancement()
            self.advance()

            if self.current_tok.type != T_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end, "Expected parent class name"
                ))
            parent_name_toks.append(self.current_tok)
            res.register_advancement()
            self.advance()

            while self.current_tok.type == T_COMMA:
                res.register_advancement()
                self.advance()
                if self.current_tok.type != T_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end, "Expected parent class name"
                    ))
                parent_name_toks.append(self.current_tok)
                res.register_advancement()
                self.advance()

        if self.current_tok.type != T_LPAREN2:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'"
            ))

        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        body_nodes = []
        while self.current_tok.type != T_RPAREN2:
            member_node = res.register(self.class_member())
            if res.error: return res
            body_nodes.append(member_node)

            while self.current_tok.type == T_NEWLINE:
                res.register_advancement()
                self.advance()

        if self.current_tok.type != T_RPAREN2:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'"
            ))
        res.register_advancement()
        self.advance()

        return res.success(ModelNode(model_name_tok, parent_name_toks, body_nodes))

    def class_member(self):
        """
        Grammar Rule:

        attr-declaration | constructor-definition | method-definition
        """
        res = ParseResult()
        tok = self.current_tok

        if tok.type == T_KEYWORD:
            if tok.value in ('open', 'guarded', 'secret'):
                next_tok = self.peek()
                if next_tok.type==T_KEYWORD and next_tok.value=="attr":
                    return self.attr_declaration()
                if next_tok.type==T_KEYWORD and next_tok.value=='method':
                    return self.method_definition()

            elif tok.value == 'attr':
                return self.attr_declaration()
            elif tok.value == 'init':
                return self.constructor_definition()
            elif tok.value == 'method':
                return self.method_definition()

        return res.failure(InvalidSyntaxError(
            tok.pos_start, tok.pos_end,
            "Expected 'attr', 'init', or 'method' (or an access modifier)"
        ))

    def attr_declaration(self):
        """
        Grammar Rule:

        (KEYWORD:open | KEYWORD:guarded | KEYWORD:secret)? KEYWORD:attr LT attr-list GT
        """
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        access_modifier_tok = None

        if self.current_tok.type==T_KEYWORD and self.current_tok.value in ('open', 'guarded', 'secret'):
            access_modifier_tok = self.current_tok
            res.register_advancement()
            self.advance()

        if not (self.current_tok.type==T_KEYWORD and self.current_tok.value=='attr'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'attr'"
            ))
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_LT:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected '<'"
            ))
        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        declarations = res.register(self.attr_list())
        if res.error: return res

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        if self.current_tok.type != T_GT:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected '>'"
            ))
        pos_end = self.current_tok.pos_end.copy()
        res.register_advancement()
        self.advance()

        return res.success(AttrNode(declarations, access_modifier_tok, pos_start, pos_end))

    def attr_list(self):
        """
        Grammar Rule:

        attr-item (COMMA attr-item)*
        """
        res = ParseResult()
        declarations = []

        first_item = res.register(self.attr_item())
        if res.error:
            return res
        declarations.append(first_item)

        while self.current_tok.type == T_COMMA:
            res.register_advancement()
            self.advance()

            while self.current_tok.type == T_NEWLINE:
                res.register_advancement()
                self.advance()

            item = res.register(self.attr_item())
            if res.error:
                return res
            declarations.append(item)

        return res.success(declarations)

    def attr_item(self):
        """
        Grammar Rule:

        IDENTIFIER (EQUAL expression)?
        """
        res = ParseResult()

        if self.current_tok.type != T_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected an attribute name (identifier)"
            ))

        name_tok = self.current_tok
        res.register_advancement()
        self.advance()

        default_value_node = None
        if self.current_tok.type == T_EQ:
            res.register_advancement()
            self.advance()

            default_value_node = res.register(self.expression())
            if res.error:
                return res

        return res.success((name_tok, default_value_node))

    def constructor_definition(self):
        """
        Grammar Rule:

        KEYWORD:init LPAREN (param-list)? RPAREN LPAREN2 NEWLINE*
        (initializer-list)? (multiline | jump-statements)* NEWLINE* RPAREN2
        """
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()

        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'init'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'init'"
            ))
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_LPAREN:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '('"
            ))
        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        param_nodes = res.register(self.param_list())
        if res.error:
            return res

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        if self.current_tok.type != T_RPAREN:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected ',' or ')'"
            ))
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_LPAREN2:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '{'"
            ))
        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        body_nodes = []
        if self.current_tok.type == T_IDENTIFIER and self.peek() and self.peek().type == T_COLON:
            initializers = res.register(self.initializer_list())
            if res.error:
                return res
            body_nodes.extend(initializers)

        body_pos_start = self.current_tok.pos_start.copy()

        while self.current_tok.type != T_RPAREN2 and self.current_tok.type != T_EOF:
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("escape", "proceed", "yield")):
                jump_node = res.register(self.jump_statements())
                if res.error:
                    return res
                body_nodes.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())
                if res.error:
                    return res
                if not multiline_node:
                    if not (self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                            self.current_tok.type == T_RPAREN2):
                        return res.failure(InvalidSyntaxError(
                            self.current_tok.pos_start, self.current_tok.pos_end,
                            "Expected statement or '}'"
                        ))
                if multiline_node:
                    body_nodes.extend(multiline_node.element_nodes)

        while self.current_tok.type==T_NEWLINE:
            res.register_advancement()
            self.advance()

        if self.current_tok.type != T_RPAREN2:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '}'"
            ))
        pos_end = self.current_tok.pos_end.copy()
        res.register_advancement()
        self.advance()

        body_node = ListNode(body_nodes, body_pos_start, pos_end)
        return res.success(InitNode(param_nodes, body_node, pos_start, pos_end))

    def method_definition(self):
        """
        Grammar Rule:

        (KEYWORD:open | KEYWORD:guarded | KEYWORD:secret)? KEYWORD:method IDENTIFIER?
        LPAREN (param-list)? RPAREN
        LPAREN2 (multiline |jump-statements)* RPAREN2
        """
        res = ParseResult()
        access_modifier_tok = None

        if self.current_tok.type==T_KEYWORD and self.current_tok.value in ('open', 'guarded', 'secret'):
            access_modifier_tok = self.current_tok
            res.register_advancement()
            self.advance()

        if not (self.current_tok.type==T_KEYWORD and self.current_tok.value=='method'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'method'"
            ))
        res.register_advancement()
        self.advance()

        name_tok = None
        if self.current_tok.type == T_IDENTIFIER:
            name_tok = self.current_tok
            res.register_advancement()
            self.advance()

        if self.current_tok.type != T_LPAREN:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected '('"
            ))
        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        param_nodes = res.register(self.param_list())
        if res.error:
            return res

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        if self.current_tok.type != T_RPAREN:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected ',' or ')'"
            ))
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_LPAREN2:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'"
            ))
        res.register_advancement()
        self.advance()

        body_nodes, pos_start = [], self.current_tok.pos_start
        brace_open_line = pos_start.line + 1
        while self.current_tok.type != T_RPAREN2 and self.current_tok.type != T_EOF:
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("yield", "proceed", "escape")):
                jump_node = res.register(self.jump_statements())
                if res.error: return res
                body_nodes.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())

                if res.error: return res
                if not multiline_node:
                    if not (self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                            self.current_tok.type == T_RPAREN2
                    ):
                        return res.failure(
                            InvalidSyntaxError(self.current_tok.pos_start,
                                               self.current_tok.pos_end,
                                               "Expected identifier,when,whenever,method or Cycle"))
                if multiline_node: body_nodes.extend(multiline_node.element_nodes)

        body_node = ListNode(body_nodes, pos_start, self.current_tok.pos_end)

        if self.current_tok.type != T_RPAREN2:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'"
            ))
        res.register_advancement()
        self.advance()

        return res.success(FunctionDefinitionNode(name_tok, param_nodes, body_node, False, access_modifier_tok))

    def initializer_list(self):
        """
        Grammar Rule:

        initializer-item ((COMMA NEWLINE* | NEWLINE+) initializer-item)*
        """
        res = ParseResult()
        initializers = []

        first_item = res.register(self.initializer_item())
        if res.error:
            return res
        initializers.append(first_item)

        while True:
            separator_found = False

            if self.current_tok.type == T_COMMA:
                separator_found = True
                res.register_advancement()
                self.advance()
                while self.current_tok.type == T_NEWLINE:
                    res.register_advancement()
                    self.advance()
            elif self.current_tok.type == T_NEWLINE:
                separator_found = True
                while self.current_tok.type == T_NEWLINE:
                    res.register_advancement()
                    self.advance()

            if not separator_found:
                break

            if self.current_tok.type != T_IDENTIFIER:
                self.reverse(res.last_registered_advance_count)
                break

            item = res.register(self.initializer_item())
            if res.error:
                return res
            initializers.append(item)

        return res.success(initializers)

    def initializer_item(self):
        """
        Grammar Rule:

        IDENTIFIER COLON expression
        """
        res = ParseResult()

        if self.current_tok.type != T_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected identifier"
            ))

        var_name_tok = self.current_tok
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_COLON:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected ':'"
            ))
        res.register_advancement()
        self.advance()

        value_node = res.register(self.expression())
        if res.error:
            return res

        return res.success(AssignNode([VariableUseNode(var_name_tok)], [value_node]))

    def list_expression(self):
        """
        Grammar Rule:

        list-expression:
            LPAREN3 NEWLINE* (expression (NEWLINE* COMMA NEWLINE* expression)*)? RPAREN3

        list-comprehension (Cycle):
            LPAREN3 expression KEYWORD:Cycle IDENTIFIER EQUAL expression COLON expression
                    (COLON expression)? (KEYWORD:when expression)? RPAREN3

        list-comprehension (trace):
            LPAREN3 expression KEYWORD:trace IDENTIFIER (COMMA IDENTIFIER)* LARROW expression
                    (KEYWORD:when expression)? RPAREN3
        """
        res = ParseResult()
        element_nodes = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != T_LPAREN3:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '['"))

        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        if self.current_tok.type == T_RPAREN3:
            # empty list []
            res.register_advancement()
            self.advance()
            return res.success(ListNode([], pos_start, self.current_tok.pos_end.copy()))

        # Parse the first (and possibly only) expression
        first_expr = res.register(self.expression())
        if res.error:
            return res

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        # ── List comprehension with Cycle ─────────────────────────────
        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'Cycle':
            return self._parse_list_comp_cycle(res, first_expr, pos_start)

        # ── List comprehension with trace ─────────────────────────────
        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'trace':
            return self._parse_list_comp_trace(res, first_expr, pos_start)

        # ── Plain list literal ────────────────────────────────────────
        element_nodes.append(first_expr)

        while self.current_tok and self.current_tok.type == T_COMMA:
            res.register_advancement()
            self.advance()

            while self.current_tok.type == T_NEWLINE:
                res.register_advancement()
                self.advance()

            element_nodes.append(res.register(self.expression()))
            if res.error:
                return res

            while self.current_tok.type == T_NEWLINE:
                res.register_advancement()
                self.advance()

        if self.current_tok.type != T_RPAREN3:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected ',' or ']",
                                   hint="Did you forget a comma ',' between list elements?"))

        res.register_advancement()
        self.advance()

        return res.success(ListNode(element_nodes, pos_start, self.current_tok.pos_end.copy()))

    def _parse_list_comp_cycle(self, res, expr_node, pos_start):
        """
        Parse the Cycle clause of a list comprehension after the expr has been read.
        [expr Cycle var = start : end (: step)? (when cond)?]
        """
        # consume 'Cycle'
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected loop variable name after 'Cycle'"))
        var_name_tok = self.current_tok
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_EQ:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected '='"))
        res.register_advancement()
        self.advance()

        start_node = res.register(self.expression())
        if res.error: return res

        if self.current_tok.type != T_COLON:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected ':'"))
        res.register_advancement()
        self.advance()

        end_node = res.register(self.expression())
        if res.error: return res

        step_node = None
        if self.current_tok.type == T_COLON:
            res.register_advancement()
            self.advance()
            step_node = res.register(self.expression())
            if res.error: return res

        condition_node = None
        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'when':
            res.register_advancement()
            self.advance()
            condition_node = res.register(self.expression())
            if res.error: return res

        if self.current_tok.type != T_RPAREN3:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected ']' to close list comprehension"))
        pos_end = self.current_tok.pos_end.copy()
        res.register_advancement()
        self.advance()

        node = ListComprehensionNode(
            expr_node=expr_node, loop_type='Cycle',
            var_name_tok=var_name_tok,
            start_node=start_node, end_node=end_node, step_node=step_node,
            condition_node=condition_node,
            pos_start=pos_start, pos_end=pos_end
        )
        return res.success(node)

    def _parse_list_comp_trace(self, res, expr_node, pos_start):
        """
        Parse the trace clause of a list comprehension after the expr has been read.
        [expr trace var <- collection (when cond)?]
        """
        # consume 'trace'
        res.register_advancement()
        self.advance()

        var_name_tokens = []
        if self.current_tok.type != T_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected at least one variable name after 'trace'"))
        var_name_tokens.append(self.current_tok)
        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_COMMA:
            res.register_advancement()
            self.advance()
            if self.current_tok.type != T_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier after ','"))
            var_name_tokens.append(self.current_tok)
            res.register_advancement()
            self.advance()

        if self.current_tok.type != T_LARROW:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected '<-'"))
        res.register_advancement()
        self.advance()

        collection_node = res.register(self.expression())
        if res.error: return res

        condition_node = None
        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'when':
            res.register_advancement()
            self.advance()
            condition_node = res.register(self.expression())
            if res.error: return res

        if self.current_tok.type != T_RPAREN3:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected ']' to close list comprehension"))
        pos_end = self.current_tok.pos_end.copy()
        res.register_advancement()
        self.advance()

        node = ListComprehensionNode(
            expr_node=expr_node, loop_type='trace',
            var_name_tokens=var_name_tokens, collection_node=collection_node,
            condition_node=condition_node,
            pos_start=pos_start, pos_end=pos_end
        )
        return res.success(node)


    def dict_expression(self):
        """
        Grammar Rule:
        dict-expression:
            LPAREN2 NEWLINE* (dict-entry (NEWLINE* COMMA NEWLINE* dict-entry)*)?
            NEWLINE* RPAREN2

        dict-comprehension (Cycle):
            LPAREN2 expression COLON expression KEYWORD:Cycle IDENTIFIER EQUAL expression
                    COLON expression (COLON expression)? (KEYWORD:when expression)? RPAREN2

        dict-comprehension (trace):
            LPAREN2 expression COLON expression KEYWORD:trace IDENTIFIER (COMMA IDENTIFIER)*
                    LARROW expression (KEYWORD:when expression)? RPAREN2
        """
        res = ParseResult()
        keyval_nodes = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != T_LPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '{'"))
        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        if self.current_tok.type == T_RPAREN2:
            # empty dict {}
            res.register_advancement()
            self.advance()
            return res.success(DictNode([], pos_start, self.current_tok.pos_end.copy()))

        # Parse the first key:value pair
        first_entry = res.register(self.dict_entry())
        if res.error:
            return res
        first_key, first_val = first_entry

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        # ── Dict comprehension with Cycle ──────────────────────────────
        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'Cycle':
            return self._parse_dict_comp_cycle(res, first_key, first_val, pos_start)

        # ── Dict comprehension with trace ──────────────────────────────
        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'trace':
            return self._parse_dict_comp_trace(res, first_key, first_val, pos_start)

        # ── Plain dict literal ─────────────────────────────────────────
        keyval_nodes.append(first_entry)

        while self.current_tok.type == T_COMMA:
            res.register_advancement()
            self.advance()

            while self.current_tok.type == T_NEWLINE:
                res.register_advancement()
                self.advance()

            if self.current_tok.type == T_RPAREN2:
                break

            entry = res.register(self.dict_entry())
            if res.error:
                return res
            keyval_nodes.append(entry)

            while self.current_tok.type == T_NEWLINE:
                res.register_advancement()
                self.advance()

        if self.current_tok.type != T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected ',' or '}'",
                                   hint="Did you forget a comma ',' between dictionary entries?"))

        res.register_advancement()
        self.advance()

        return res.success(
            DictNode(keyval_nodes, pos_start, self.current_tok.pos_end.copy()))

    def _parse_dict_comp_cycle(self, res, key_node, val_node, pos_start):
        """
        {key : val Cycle var = start : end (: step)? (when cond)?}
        """
        # consume 'Cycle'
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected loop variable name after 'Cycle'"))
        var_name_tok = self.current_tok
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_EQ:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected '='"))
        res.register_advancement()
        self.advance()

        start_node = res.register(self.expression())
        if res.error: return res

        if self.current_tok.type != T_COLON:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected ':'"))
        res.register_advancement()
        self.advance()

        end_node = res.register(self.expression())
        if res.error: return res

        step_node = None
        if self.current_tok.type == T_COLON:
            res.register_advancement()
            self.advance()
            step_node = res.register(self.expression())
            if res.error: return res

        condition_node = None
        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'when':
            res.register_advancement()
            self.advance()
            condition_node = res.register(self.expression())
            if res.error: return res

        if self.current_tok.type != T_RPAREN2:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '}' to close dict comprehension"))
        pos_end = self.current_tok.pos_end.copy()
        res.register_advancement()
        self.advance()

        node = DictComprehensionNode(
            key_node=key_node, val_node=val_node, loop_type='Cycle',
            var_name_tok=var_name_tok,
            start_node=start_node, end_node=end_node, step_node=step_node,
            condition_node=condition_node,
            pos_start=pos_start, pos_end=pos_end
        )
        return res.success(node)

    def _parse_dict_comp_trace(self, res, key_node, val_node, pos_start):
        """
        {key : val trace var <- collection (when cond)?}
        """
        # consume 'trace'
        res.register_advancement()
        self.advance()

        var_name_tokens = []
        if self.current_tok.type != T_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected at least one variable name after 'trace'"))
        var_name_tokens.append(self.current_tok)
        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_COMMA:
            res.register_advancement()
            self.advance()
            if self.current_tok.type != T_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier after ','"))
            var_name_tokens.append(self.current_tok)
            res.register_advancement()
            self.advance()

        if self.current_tok.type != T_LARROW:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected '<-'"))
        res.register_advancement()
        self.advance()

        collection_node = res.register(self.expression())
        if res.error: return res

        condition_node = None
        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'when':
            res.register_advancement()
            self.advance()
            condition_node = res.register(self.expression())
            if res.error: return res

        if self.current_tok.type != T_RPAREN2:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '}' to close dict comprehension"))
        pos_end = self.current_tok.pos_end.copy()
        res.register_advancement()
        self.advance()

        node = DictComprehensionNode(
            key_node=key_node, val_node=val_node, loop_type='trace',
            var_name_tokens=var_name_tokens, collection_node=collection_node,
            condition_node=condition_node,
            pos_start=pos_start, pos_end=pos_end
        )
        return res.success(node)

    def dict_entry(self):
        """
        Grammar Rule:
        dict-entry: expression NEWLINE* COLON NEWLINE* expression
        """
        res = ParseResult()

        key_node = res.register(self.expression())
        if res.error:
            return res

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        if self.current_tok.type != T_COLON:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected ':'"))
        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        value_node = res.register(self.expression())
        if res.error:
            return res

        return res.success((key_node, value_node))

    def exception_handling(self):
        """
        Grammar Rule:

        exception-handling:
            try-expression NEWLINE* ( trap-block NEWLINE* (trap-block)* NEWLINE* clean-block? | clean-block)
        """
        res = ParseResult()

        # Parse the 'risk' block
        try_node = res.register(self.try_expression())
        if res.error:
            return res

        while self.current_tok.type==T_NEWLINE:
            res.register_advancement()
            self.advance()

        trap_nodes = []
        clean_node = None

        # One or more trap blocks
        while self.current_tok.type == T_KEYWORD and self.current_tok.value == "trap":
            trap_node = res.register(self.catch_expression())
            if res.error:
                return res
            trap_nodes.append(trap_node)

            while self.current_tok.type==T_NEWLINE:
                res.register_advancement()
                self.advance()

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        # Optional clean block
        if self.current_tok.type == T_KEYWORD and self.current_tok.value == "clean":
            clean_node = res.register(self.finally_expression())
            if res.error:
                return res

        # Must have at least one trap or clean
        if not trap_nodes and not clean_node:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'trap' or 'clean' after 'risk'"
                )
            )

        return res.success(TryNode(try_node.body_node, trap_nodes, clean_node))

    def try_expression(self):
        """
        Grammar Rule:
            try-expression: KEYWORD:risk LPAREN2
            (multiline | jump-statements)* RPAREN2
        """
        res = ParseResult()

        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == "risk"):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'risk'")
            )
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_LPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'")
            )
        res.register_advancement()
        self.advance()

        body_nodes, pos_start = [], self.current_tok.pos_start
        while self.current_tok.type != T_RPAREN2 and self.current_tok.type != T_EOF:
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("escape", "proceed", "yield")):
                jump_node = res.register(self.jump_statements())
                if res.error: return res
                body_nodes.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())
                if res.error: return res
                if not multiline_node:
                    if not (self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                            self.current_tok.type == T_RPAREN2
                    ):
                        return res.failure(
                            InvalidSyntaxError(self.current_tok.pos_start,
                                               self.current_tok.pos_end,
                                               "Expected identifier,when,whenever,method or Cycle"))
                if multiline_node: body_nodes.extend(multiline_node.element_nodes)

        body_node = ListNode(body_nodes, pos_start, self.current_tok.pos_end)

        if self.current_tok.type != T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'")
            )
        res.register_advancement()
        self.advance()

        return res.success(TryNode(body_node))

    def catch_expression(self):
        """
        Grammar Rule:
            catch-expression: KEYWORD:trap (ERROR (IDENTIFIER)?)?
                              LPAREN2 (multiline | jump-statements)* RPAREN2
        """
        res = ParseResult()

        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == "trap"):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'trap'")
            )
        res.register_advancement()
        self.advance()

        error_type_tok = None
        error_name_tok = None

        # Optional ERROR (IDENTIFIER)?
        if self.current_tok.type == T_ERROR:
            error_type_tok = self.current_tok
            res.register_advancement()
            self.advance()

            if self.current_tok.type == T_IDENTIFIER:
                error_name_tok = self.current_tok
                res.register_advancement()
                self.advance()

        if self.current_tok.type != T_LPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'")
            )
        res.register_advancement()
        self.advance()

        body_nodes, pos_start = [], self.current_tok.pos_start
        while self.current_tok.type != T_RPAREN2 and self.current_tok.type != T_EOF:
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("escape", "proceed", "yield")):
                jump_node = res.register(self.jump_statements())
                if res.error: return res
                body_nodes.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())
                if res.error: return res
                if not multiline_node:
                    if not (self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                            self.current_tok.type == T_RPAREN2
                    ):
                        return res.failure(
                            InvalidSyntaxError(self.current_tok.pos_start,
                                               self.current_tok.pos_end,
                                               "Expected identifier,when,whenever,method or Cycle"))
                if multiline_node: body_nodes.extend(multiline_node.element_nodes)

        body_node = ListNode(body_nodes, pos_start, self.current_tok.pos_end)

        if self.current_tok.type != T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'")
            )
        res.register_advancement()
        self.advance()

        return res.success(CatchNode(error_type_tok, error_name_tok, body_node))

    def finally_expression(self):
        """
        Grammar Rule:
            finally-expression: KEYWORD:clean
            LPAREN2 (multiline | jump-statements)* RPAREN2
        """
        res = ParseResult()

        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == "clean"):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'clean'")
            )
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_LPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'")
            )
        res.register_advancement()
        self.advance()

        body_nodes, pos_start = [], self.current_tok.pos_start
        while self.current_tok.type != T_RPAREN2 and self.current_tok.type != T_EOF:
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("escape", "proceed", "yield")):
                jump_node = res.register(self.jump_statements())
                if res.error: return res
                body_nodes.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())
                if res.error: return res
                if not multiline_node:
                    if not (self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                            self.current_tok.type == T_RPAREN2
                    ):
                        return res.failure(
                            InvalidSyntaxError(self.current_tok.pos_start,
                                               self.current_tok.pos_end,
                                               "Expected identifier,when,whenever,method or Cycle"))
                if multiline_node: body_nodes.extend(multiline_node.element_nodes)

        body_node = ListNode(body_nodes, pos_start, self.current_tok.pos_end)

        if self.current_tok.type != T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'")
            )
        res.register_advancement()
        self.advance()

        return res.success(FinallyNode(body_node))

    def param_item(self):
        """
        Grammar Rule: IDENTIFIER (EQUAL expression)?
        """
        res = ParseResult()

        if self.current_tok.type != T_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected parameter name (identifier)"
            ))

        param_name_tok = self.current_tok
        res.register_advancement()
        self.advance()

        default_value = None
        if self.current_tok.type == T_EQ:
            res.register_advancement()
            self.advance()
            default_value = res.register(self.expression())
            if res.error: return res

        return res.success((param_name_tok, default_value))

    def param_list(self):
        """
        Grammar Rule: (param-item (COMMA param-item)*)?
        """
        res = ParseResult()
        params = []

        if self.current_tok.type == T_RPAREN:
            # Handles empty parameter list
            return res.success(params)

        # Parse the first parameter
        item = res.register(self.param_item())
        if res.error: return res
        params.append(item)

        # Parse subsequent parameters
        while self.current_tok.type == T_COMMA:
            res.register_advancement()
            self.advance()

            while self.current_tok.type == T_NEWLINE:
                res.register_advancement()
                self.advance()

            item = res.register(self.param_item())
            if res.error: return res
            params.append(item)

        return res.success(params)

    def function_definition(self):
        """
        Grammar Rule:
        function-definition:
            KEYWORD:method IDENTIFIER LPAREN (param-list)? RPAREN
            LPAREN2 (multiline | jump-statements)* RPAREN2
        """
        res = ParseResult()

        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'method'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected 'method'"))
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected identifier for function name"
            ))

        var_name_tok = self.current_tok
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_LPAREN:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '('"))

        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        arg_nodes = res.register(self.param_list())
        if res.error:
            return res

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        if self.current_tok.type != T_RPAREN:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected ',' or ')'",
                                   hint="Did you forget a comma ',' between parameters?"))

        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_LPAREN2:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start,
                                                  self.current_tok.pos_end,
                                                  "Expected '{'"))
        res.register_advancement()
        self.advance()

        body_nodes, pos_start = [], self.current_tok.pos_start
        brace_open_line = pos_start.line + 1
        while self.current_tok.type != T_RPAREN2 and self.current_tok.type != T_EOF:
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("yield", "proceed", "escape")):
                jump_node = res.register(self.jump_statements())
                if res.error: return res
                body_nodes.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())
                if res.error: return res
                if not multiline_node:
                    if not (self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                            self.current_tok.type == T_RPAREN2
                    ):
                        return res.failure(
                            InvalidSyntaxError(self.current_tok.pos_start,
                                               self.current_tok.pos_end,
                                               "Expected identifier,when,whenever,method or Cycle"))
                if multiline_node: body_nodes.extend(multiline_node.element_nodes)

        body_node = ListNode(body_nodes, pos_start, self.current_tok.pos_end)

        if self.current_tok.type != T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '}'",
                                   hint=f"Unexpected end of file. You opened a block '{{' on line {brace_open_line} that was never closed."))
        res.register_advancement()
        self.advance()

        return res.success(FunctionDefinitionNode(var_name_tok, arg_nodes, body_node, False))

    def anonymous_func_expr(self):
        """
        Grammar Rule:
            anonymous-func-expr:
            KEYWORD:method IDENTIFIER LPAREN (param-list)? RPAREN
            LPAREN2 (multiline | jump-statements)* RPAREN2
        """
        res = ParseResult()

        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'method'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected 'method'"))
        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_LPAREN:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '('"))

        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        arg_nodes = res.register(self.param_list())
        if res.error:
            return res

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        if self.current_tok.type != T_RPAREN:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected ',' or ')'"))

        res.register_advancement()
        self.advance()

        if self.current_tok.type != T_LPAREN2:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start,
                                                  self.current_tok.pos_end,
                                                  "Expected '{'"))
        res.register_advancement()
        self.advance()

        body_nodes, pos_start = [], self.current_tok.pos_start
        brace_open_line = pos_start.line + 1
        while self.current_tok.type != T_RPAREN2 and self.current_tok.type != T_EOF:
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("yield", "proceed", "escape")):
                jump_node = res.register(self.jump_statements())
                if res.error: return res
                body_nodes.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())
                if res.error: return res
                if not multiline_node:
                    if not (self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                            self.current_tok.type == T_RPAREN2
                    ):
                        return res.failure(
                            InvalidSyntaxError(self.current_tok.pos_start,
                                               self.current_tok.pos_end,
                                               "Expected identifier,when,whenever,method or Cycle"))
                if multiline_node: body_nodes.extend(multiline_node.element_nodes)

        body_node = ListNode(body_nodes, pos_start, self.current_tok.pos_end)

        if self.current_tok.type != T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '}'",
                                   hint=f"Unexpected end of file. You opened a block '{{' on line {brace_open_line} that was never closed."))
        res.register_advancement()
        self.advance()

        return res.success(FunctionDefinitionNode(None, arg_nodes, body_node, False))

    def switch_statement(self):
        """
        Grammar Rule:

        KEYWORD:menu ternary-expression LPAREN2 NEWLINE* (case-statement* NEWLINE*)*
        default-statement? NEWLINE* (case_statement* NEWLINE*)* RPAREN2
        """
        res = ParseResult()
        cases = []
        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'menu'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected 'menu'"))

        res.register_advancement()
        self.advance()

        selection = res.register(self.ternary_expression())
        if res.error:
            return res

        if not self.current_tok.type == T_LPAREN2:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start,
                                                  self.current_tok.pos_end,
                                                  "Expected '{'"))

        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        found_default = False
        count = 0

        while (self.current_tok.type == T_KEYWORD and
              (self.current_tok.value in ('choice', 'fallback'))):
            if (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'choice'):
                case = res.register(self.case_statement())
                if res.error:
                    return res
                cases.append(case)
                while self.current_tok.type == T_NEWLINE:
                    res.register_advancement()
                    self.advance()
            else:
                if found_default:
                    return res.failure(InvalidSyntaxError(self.current_tok.pos_start,
                                                          self.current_tok.pos_end,
                                                          "Multiple 'fallback' statements found"))
                found_default = True
                case = res.register(self.default_statement())
                if res.error:
                    return res
                cases.append(case)
                while self.current_tok.type == T_NEWLINE:
                    res.register_advancement()
                    self.advance()
            count = count + 1

        if count == 0:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end,
                                   "Expected 'choice' or 'fallback'"))

        if not self.current_tok.type == T_RPAREN2:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start,
                                                  self.current_tok.pos_end,
                                                  "Expected '}'"))

        res.register_advancement()
        self.advance()

        return res.success(SwitchNode(selection, cases, False))

    def case_statement(self):
        """
        Grammar Rule:

        KEYWORD:choice ternary-expression LPAREN2 NEWLINE*
        (multiline | jump-statements)* RPAREN2
        """
        res = ParseResult()
        case = None

        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'choice'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected 'choice'"))
        res.register_advancement()
        self.advance()

        if self.current_tok.type == T_LPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected expression after 'choice'"))

        choice_val = res.register(self.ternary_expression())
        if res.error:
            return res

        if not self.current_tok.type == T_LPAREN2:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start,
                                                  self.current_tok.pos_end,
                                                  "Expected '{'"))

        res.register_advancement()
        self.advance()

        body_nodes, pos_start = [], self.current_tok.pos_start
        while self.current_tok.type != T_RPAREN2 and self.current_tok.type != T_EOF:
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("escape", "proceed", "yield")):
                jump_node = res.register(self.jump_statements())
                if res.error: return res
                body_nodes.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())
                if res.error: return res
                if not multiline_node:
                    if not (self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                            self.current_tok.type == T_RPAREN2
                    ):
                        return res.failure(
                            InvalidSyntaxError(self.current_tok.pos_start,
                                               self.current_tok.pos_end,
                                               "Expected statement or '}'"))
                if multiline_node: body_nodes.extend(multiline_node.element_nodes)

        body_node = ListNode(body_nodes, pos_start, self.current_tok.pos_end)
        case = (choice_val, body_node, True)

        if not self.current_tok.type == T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '}'"))

        res.register_advancement()
        self.advance()

        return res.success(case)

    def default_statement(self):
        """
        Grammar Rule:

        KEYWORD:fallback LPAREN2 NEWLINE*
        (multiline | jump-statements)* RPAREN2
        """
        res = ParseResult()
        default_case = None

        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'fallback'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected 'fallback'"))
        res.register_advancement()
        self.advance()

        if not self.current_tok.type == T_LPAREN2:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start,
                                                  self.current_tok.pos_end,
                                                  "Expected '{'"))

        res.register_advancement()
        self.advance()

        body_nodes, pos_start = [], self.current_tok.pos_start
        while self.current_tok.type != T_RPAREN2 and self.current_tok.type != T_EOF:
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("escape", "proceed", "yield")):
                jump_node = res.register(self.jump_statements())
                if res.error: return res
                body_nodes.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())
                if res.error: return res
                if not multiline_node:
                    if not (self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                            self.current_tok.type == T_RPAREN2
                    ):
                        return res.failure(
                            InvalidSyntaxError(self.current_tok.pos_start,
                                               self.current_tok.pos_end,
                                               "Expected statement or '}'"))
                if multiline_node: body_nodes.extend(multiline_node.element_nodes)

        body_node = ListNode(body_nodes, pos_start, self.current_tok.pos_end)
        default_case = (None, body_node, True)

        if not self.current_tok.type == T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '}'"))

        res.register_advancement()
        self.advance()

        return res.success(default_case)

    def while_expression(self):
        """
        while-expression:
            KEYWORD:whenever expression
            LPAREN2 (multiline | jump-statements)* RPAREN2
        """
        res = ParseResult()

        # 'whenever'
        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'whenever'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected 'whenever'"))
        res.register_advancement()
        self.advance()

        # condition
        condition = res.register(self.expression())
        if res.error: return res

        if isinstance(condition, AssignNode):
            return res.failure(
                InvalidSyntaxError(condition.pos_start, condition.pos_end,
                                   "Assignment is not allowed in a 'whenever' condition",
                                   hint="Did you mean '==' for comparison instead of '=' for assignment?"))

        # '{'
        if not self.current_tok.type == T_LPAREN2:
            _hint = None
            if self.current_tok.type == T_EQ:
                _hint = "Did you mean '==' for comparison instead of '=' for assignment?"
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '{'",
                                   hint=_hint))
        res.register_advancement()
        self.advance()

        # body
        body_nodes, pos_start = [], self.current_tok.pos_start
        brace_open_line = pos_start.line + 1
        while self.current_tok.type != T_RPAREN2 and self.current_tok.type != T_EOF:
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("escape", "proceed","yield")):
                jump_node = res.register(self.jump_statements())
                if res.error: return res
                body_nodes.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())
                if res.error: return res
                if not multiline_node:
                    if not(self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not(
                        self.current_tok.type==T_RPAREN2
                    ):
                        return res.failure(
                            InvalidSyntaxError(self.current_tok.pos_start,
                                               self.current_tok.pos_end,
                                               "Expected identifier,when,whenever,method or Cycle"))
                if multiline_node:body_nodes.extend(multiline_node.element_nodes)

        body_node = ListNode(body_nodes, pos_start, self.current_tok.pos_end)

        # '}'
        if not self.current_tok.type == T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '}'",
                                   hint=f"Unexpected end of file. You opened a block '{{' on line {brace_open_line} that was never closed."))
        res.register_advancement()
        self.advance()

        return res.success(WhileNode(condition, body_node, False))

    def for_expression(self):
        """
        for-expression:
            KEYWORD:Cycle IDENTIFIER EQUAL expression COLON expression (COLON expression)?
            LPAREN2 (multiline | jump-statements)* RPAREN2
        """
        res = ParseResult()
        step_value = None

        # 'Cycle'
        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'Cycle'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected 'Cycle'"))
        res.register_advancement()
        self.advance()

        # Identifier
        if not self.current_tok.type == T_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected identifier"))
        var_name = self.current_tok
        res.register_advancement()
        self.advance()

        # '='
        if not self.current_tok.type == T_EQ:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '='"))
        res.register_advancement()
        self.advance()

        # start expression
        start_value = res.register(self.expression())
        if res.error: return res

        # ':'
        if not self.current_tok.type == T_COLON:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected ':'"))
        res.register_advancement()
        self.advance()

        # end expression
        end_value = res.register(self.expression())
        if res.error: return res

        # optional step expression
        if self.current_tok.type == T_COLON:
            res.register_advancement()
            self.advance()
            step_value = res.register(self.expression())
            if res.error: return res

        # '{'
        if not self.current_tok.type == T_LPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '{'"))
        res.register_advancement()
        self.advance()

        body_node,pos_start=[],self.current_tok.pos_start
        while self.current_tok.type != T_RPAREN2 and self.current_tok.type != T_EOF:
            if self.current_tok.type==T_KEYWORD and (self.current_tok.value in ("escape","proceed","yield")):
                jump_node = res.register(self.jump_statements())
                if res.error: return res
                body_node.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())
                if res.error: return res
                if not multiline_node:
                    if not (self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                            self.current_tok.type == T_RPAREN2
                    ):
                        return res.failure(
                            InvalidSyntaxError(self.current_tok.pos_start,
                                               self.current_tok.pos_end,
                                               "Expected identifier,when,whenever,method or Cycle"))
                if multiline_node: body_node.extend(multiline_node.element_nodes)

        body_node=ListNode(body_node,pos_start,self.current_tok.pos_end)
        # '}'
        if not self.current_tok.type == T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '}'"))
        res.register_advancement()
        self.advance()

        return res.success(ForNode(var_name, start_value, end_value, step_value, body_node,False))

    def foreach_expression(self):
        """
        Grammar Rule:
        foreach-expression:
                KEYWORD:trace IDENTIFIER (COMMA IDENTIFIER)*
                LARROW expression NEWLINE* LPAREN2 (multiline | jump-statements)* RPAREN2
        """
        res = ParseResult()

        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'trace'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected 'trace'"))
        res.register_advancement()
        self.advance()

        var_name_tokens = []
        if self.current_tok.type != T_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected at least one identifier"))

        var_name_tokens.append(self.current_tok)
        res.register_advancement()
        self.advance()

        while self.current_tok.type == T_COMMA:
            res.register_advancement()
            self.advance()
            if self.current_tok.type != T_IDENTIFIER:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start,
                                       self.current_tok.pos_end,
                                       "Expected identifier after ','"))
            var_name_tokens.append(self.current_tok)
            res.register_advancement()
            self.advance()

        if self.current_tok.type != T_LARROW:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '<-'"))
        res.register_advancement()
        self.advance()

        collection_node = res.register(self.expression())
        if res.error:
            return res

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        if self.current_tok.type != T_LPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '{'"))
        res.register_advancement()
        self.advance()

        body_nodes, pos_start = [], self.current_tok.pos_start
        while self.current_tok.type != T_RPAREN2 and self.current_tok.type != T_EOF:
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("yield", "proceed", "escape")):
                jump_node = res.register(self.jump_statements())
                if res.error: return res
                body_nodes.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())
                if res.error: return res
                if not multiline_node:
                    if not (self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                            self.current_tok.type == T_RPAREN2
                    ):
                        return res.failure(
                            InvalidSyntaxError(self.current_tok.pos_start,
                                               self.current_tok.pos_end,
                                               "Expected statement or '}'"))
                if multiline_node: body_nodes.extend(multiline_node.element_nodes)

        body_node = ListNode(body_nodes, pos_start, self.current_tok.pos_end.copy())

        if self.current_tok.type != T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '}'"))
        res.register_advancement()
        self.advance()

        return res.success(ForEachLoopNode(var_name_tokens, collection_node, body_node))

    def summon_statement(self):
        """
        Grammar Rule:
        summon-stmt :=
            'summon' '*' 'from' IDENTIFIER                               # wildcard
          | 'summon' IDENTIFIER 'as' IDENTIFIER 'from' IDENTIFIER        # single name with alias
          | 'summon' IDENTIFIER (',' IDENTIFIER)* 'from' IDENTIFIER      # multiple names
          | 'summon' IDENTIFIER 'as' IDENTIFIER                          # module with alias
          | 'summon' IDENTIFIER                                          # bare module
        """
        res = ParseResult()

        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'summon'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'summon'"
            ))
        pos_start = self.current_tok.pos_start.copy()
        res.register_advancement()
        self.advance()

        # ── Case 1: summon * from MODULE ────────────────────────────────
        if self.current_tok.type == T_MUL:
            res.register_advancement()
            self.advance()

            if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'from'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected 'from' after '*'"
                ))
            res.register_advancement()
            self.advance()

            if self.current_tok.type != T_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected module name after 'from'"
                ))
            module_tok = self.current_tok
            pos_end = module_tok.pos_end.copy()
            res.register_advancement()
            self.advance()

            return res.success(SummonNode(
                module_tok=module_tok, wildcard=True,
                pos_start=pos_start, pos_end=pos_end
            ))

        # ── Must start with IDENTIFIER from here ────────────────────────
        if self.current_tok.type != T_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected module name or identifier after 'summon'"
            ))
        first_tok = self.current_tok
        res.register_advancement()
        self.advance()

        # ── Case 2: summon NAME as ALIAS from MODULE  (single with alias)
        #    or     summon NAME (',' NAME)* from MODULE  (multiple names)
        # Check whether 'from' or 'as' or ',' follows
        is_from_import = False
        peek = self.current_tok

        if peek.type == T_COMMA or (peek.type == T_KEYWORD and peek.value == 'from'):
            is_from_import = True
        elif peek.type == T_KEYWORD and peek.value == 'as':
            # Lookahead: after alias comes either 'from' (name-with-alias) or EOL (module alias)
            saved_i = self.tok_index
            saved_t = self.current_tok
            res.register_advancement(); self.advance()   # consume 'as'
            if self.current_tok.type != T_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected alias name after 'as'"
                ))
            alias_tok = self.current_tok
            res.register_advancement(); self.advance()   # consume alias
            if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'from':
                # Case: summon NAME as ALIAS from MODULE
                res.register_advancement(); self.advance()  # consume 'from'
                if self.current_tok.type != T_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected module name after 'from'"
                    ))
                module_tok = self.current_tok
                pos_end = module_tok.pos_end.copy()
                res.register_advancement(); self.advance()
                return res.success(SummonNode(
                    module_tok=module_tok,
                    names=[(first_tok, alias_tok)],
                    pos_start=pos_start, pos_end=pos_end
                ))
            else:
                # Case: summon NAME as ALIAS  (module alias)
                pos_end = alias_tok.pos_end.copy()
                return res.success(SummonNode(
                    module_tok=first_tok,
                    module_alias=alias_tok,
                    pos_start=pos_start, pos_end=pos_end
                ))

        if is_from_import:
            # Collect comma-separated names: first_tok already consumed
            names = [(first_tok, None)]
            while self.current_tok.type == T_COMMA:
                res.register_advancement(); self.advance()
                if self.current_tok.type != T_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected identifier after ','"
                    ))
                names.append((self.current_tok, None))
                res.register_advancement(); self.advance()

            if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'from'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected 'from'"
                ))
            res.register_advancement(); self.advance()

            if self.current_tok.type != T_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected module name after 'from'"
                ))
            module_tok = self.current_tok
            pos_end = module_tok.pos_end.copy()
            res.register_advancement(); self.advance()

            return res.success(SummonNode(
                module_tok=module_tok, names=names,
                pos_start=pos_start, pos_end=pos_end
            ))

        # ── Case 5: bare summon NAME ────────────────────────────────────
        pos_end = first_tok.pos_end.copy()
        return res.success(SummonNode(
            module_tok=first_tok,
            pos_start=pos_start, pos_end=pos_end
        ))

    def if_expression(self):
        """
        Grammar Rule:
        if-expression:
            KEYWORD:when expression
            LPAREN2 (multiline | jump-statements)* RPAREN2
            (elif-expression | else-expression)?
        """
        res = ParseResult()
        cases = []

        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'when'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected 'when'"))

        res.register_advancement()
        self.advance()

        # condition
        condition = res.register(self.expression())
        if res.error: return res

        if isinstance(condition, AssignNode):
            return res.failure(
                InvalidSyntaxError(condition.pos_start, condition.pos_end,
                                   "Assignment is not allowed in a 'when' condition",
                                   hint="Did you mean '==' for comparison instead of '=' for assignment?"))

        # '{'
        if not self.current_tok.type == T_LPAREN2:
            _hint = None
            if self.current_tok.type == T_EQ:
                _hint = "Did you mean '==' for comparison instead of '=' for assignment?"
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '{'",
                                   hint=_hint))
        res.register_advancement()
        self.advance()

        # body
        body_nodes, pos_start = [], self.current_tok.pos_start
        brace_open_line = pos_start.line + 1
        while self.current_tok.type not in (T_RPAREN2, T_EOF):
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("escape", "proceed","yield")):
                jump_node = res.register(self.jump_statements())
                if res.error: return res
                body_nodes.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())
                if res.error: return res
                if not multiline_node:
                    if not (self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                            self.current_tok.type == T_RPAREN2
                    ):
                        return res.failure(
                            InvalidSyntaxError(self.current_tok.pos_start,
                                               self.current_tok.pos_end,
                                               "Expected identifier,when,whenever,method or Cycle"))
                if multiline_node: body_nodes.extend(multiline_node.element_nodes)

        body_node = ListNode(body_nodes, pos_start, self.current_tok.pos_end)

        # '}'
        if not self.current_tok.type == T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '}'",
                                   hint=f"Unexpected end of file. You opened a block '{{' on line {brace_open_line} that was never closed."))
        res.register_advancement()
        self.advance()

        cases.append((condition, body_node, True))

        # elif/else
        all_cases = res.register(self.elif_or_else_expression())
        if res.error: return res
        new_cases, else_case = all_cases
        cases.extend(new_cases)

        return res.success(IfNode(cases, else_case))

    def elif_or_else_expression(self):
        res = ParseResult()
        cases, else_case = [], None

        while self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'orwhen':
            all_cases = res.register(self.elif_expression())
            if res.error: return res
            cases, else_case = all_cases
        elif self.current_tok.type == T_KEYWORD and self.current_tok.value == 'otherwise':
            else_case = res.register(self.else_expression())
            if res.error: return res

        return res.success((cases, else_case))

    def elif_expression(self):
        """
        Grammar Rule:
        elif-expression:
            KEYWORD:orwhen expression
            LPAREN2 (multiline | jump-statements)* RPAREN2
            (elif-expression | else-expression)?
        """
        res = ParseResult()
        cases = []

        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'orwhen'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected 'orwhen'"))

        res.register_advancement()
        self.advance()

        # condition
        condition = res.register(self.expression())
        if res.error: return res

        if isinstance(condition, AssignNode):
            return res.failure(
                InvalidSyntaxError(condition.pos_start, condition.pos_end,
                                   "Assignment is not allowed in an 'orwhen' condition",
                                   hint="Did you mean '==' for comparison instead of '=' for assignment?"))

        # '{'
        if not self.current_tok.type == T_LPAREN2:
            _hint = None
            if self.current_tok.type == T_EQ:
                _hint = "Did you mean '==' for comparison instead of '=' for assignment?"
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '{'",
                                   hint=_hint))
        res.register_advancement()
        self.advance()

        # body
        body_nodes, pos_start = [], self.current_tok.pos_start
        brace_open_line = pos_start.line + 1
        while self.current_tok.type not in (T_RPAREN2, T_EOF):
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("escape", "proceed","yield")):
                jump_node = res.register(self.jump_statements())
                if res.error: return res
                body_nodes.append(jump_node)
            else:
                multiline_node = res.try_register(self.multiline())
                if res.error: return res
                if not multiline_node:
                    if not (self.current_tok.type == T_KEYWORD and (
                            self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                            self.current_tok.type == T_RPAREN2
                    ):
                        return res.failure(
                            InvalidSyntaxError(self.current_tok.pos_start,
                                               self.current_tok.pos_end,
                                               "Expected identifier,when,whenever,method or Cycle"))
                if multiline_node: body_nodes.extend(multiline_node.element_nodes)

        body_node = ListNode(body_nodes, pos_start, self.current_tok.pos_end)

        # '}'
        if not self.current_tok.type == T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '}'",
                                   hint=f"Unexpected end of file. You opened a block '{{' on line {brace_open_line} that was never closed."))
        res.register_advancement()
        self.advance()

        cases.append((condition, body_node, True))

        # recursion for elif/else
        all_cases = res.register(self.elif_or_else_expression())
        if res.error: return res
        new_cases, else_case = all_cases
        cases.extend(new_cases)

        return res.success((cases, else_case))

    def else_expression(self):
        """
        Grammar Rule:
        else-expression:
            KEYWORD:otherwise LPAREN2 (multiline | jump-statements)* RPAREN2
        """
        res = ParseResult()
        else_case = None

        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'otherwise':
            res.register_advancement()
            self.advance()

            if not self.current_tok.type == T_LPAREN2:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start,
                                       self.current_tok.pos_end,
                                       "Expected '{'"))
            res.register_advancement()
            self.advance()

            # body
            body_nodes, pos_start = [], self.current_tok.pos_start
            while self.current_tok.type not in (T_RPAREN2, T_EOF):
                if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("escape", "proceed","yield")):
                    jump_node = res.register(self.jump_statements())
                    if res.error: return res
                    body_nodes.append(jump_node)
                else:
                    multiline_node = res.try_register(self.multiline())
                    if res.error: return res
                    if not multiline_node:
                        if not (self.current_tok.type == T_KEYWORD and (
                                self.current_tok.value in ("escape", "proceed", "yield"))) and not (
                                self.current_tok.type == T_RPAREN2
                        ):
                            return res.failure(
                                InvalidSyntaxError(self.current_tok.pos_start,
                                                   self.current_tok.pos_end,
                                                   "Expected identifier,when,whenever,method or Cycle"))
                    if multiline_node: body_nodes.extend(multiline_node.element_nodes)

            body_node = ListNode(body_nodes, pos_start, self.current_tok.pos_end)

            if not self.current_tok.type == T_RPAREN2:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start,
                                       self.current_tok.pos_end,
                                       "Expected '}'"))
            res.register_advancement()
            self.advance()

            else_case = (body_node, True)

        return res.success(else_case)

    def ternary_expression(self):
        """
        Grammar Rule:

        (logical-expression|statements) (QUESTION ternary-expression COLON ternary-expression)*
        """
        res = ParseResult()
        if self.current_tok.type == T_IDENTIFIER and self.peek() and self.peek().type == T_EQ:
            comp_node = res.register(self.statements())
        else:
            comp_node = res.register(self.logical_expression())
        if res.error:
            return res
        false_node = true_node = None

        while self.current_tok and self.current_tok.type == T_QUESTION:
            res.register_advancement()
            self.advance()
            true_node = res.register(self.ternary_expression())
            if res.error:
                return res
            if self.current_tok and not self.current_tok.type == T_COLON:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start,
                                       self.current_tok.pos_end,
                                       "Expected ':' "))

            res.register_advancement()
            self.advance()
            false_node = res.register(self.ternary_expression())
            if res.error:
                return res

        if not (true_node and false_node):
            return res.success(comp_node)

        return res.success(TernaryOperationNode(comp_node, true_node, false_node))

    def unary(self):
        """
        Grammar Rule:

        (PLUS | MINUS | BITNOT) unary | exponent
        """
        res = ParseResult()
        token = self.current_tok

        if token.type in (T_PLUS, T_MINUS, T_BITNOT):
            res.register_advancement()
            self.advance()
            factor = res.register(self.unary())
            if res.error:
                return res
            return res.success(UnaryOperationNode(token, factor))

        return self.exponent()


    def exponent(self):
        """
        Grammar Rule:

        call (EXP unary)*
        """
        res = ParseResult()
        left_node = res.register(self.call())
        if res.error:
            return res
        while self.current_tok and self.current_tok.type == T_EXP:
            operator = self.current_tok
            res.register_advancement()
            self.advance()
            right_node = res.register(self.unary())
            if res.error:
                return res
            left_node = BinaryOperationNode(left_node, operator, right_node)

        return res.success(left_node)

    def keyword_item(self):
        """
        Grammar Rule: IDENTIFIER EQUAL expression
        """
        res = ParseResult()

        if not (self.current_tok.type == T_IDENTIFIER and self.peek() and self.peek().type == T_EQ):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected keyword argument (identifier=value)"
            ))

        name_tok = self.current_tok
        res.register_advancement()
        self.advance()

        res.register_advancement()
        self.advance()

        value_node = res.register(self.expression())
        if res.error: return res

        return res.success((name_tok, value_node))

    def keyword_list(self):
        """
        Grammar Rule: keyword-item (COMMA keyword-item)*
        """
        res = ParseResult()
        keywords = []

        item = res.register(self.keyword_item())
        if res.error: return res
        keywords.append(item)

        while self.current_tok.type == T_COMMA:
            res.register_advancement()
            self.advance()

            while self.current_tok.type == T_NEWLINE:
                res.register_advancement()
                self.advance()

            item = res.register(self.keyword_item())
            if res.error: return res
            keywords.append(item)

        return res.success(keywords)

    def positional_list(self):
        """
        Grammar Rule: expression (COMMA expression)*
        """
        res = ParseResult()
        positional_args = []

        expr = res.register(self.expression())
        if res.error: return res
        positional_args.append(expr)

        while self.current_tok.type == T_COMMA:
            peek_idx = 1
            while self.tok_index + peek_idx < len(self.tokens) and self.tokens[self.tok_index + peek_idx].type == T_NEWLINE:
                peek_idx += 1
            next_tok = self.tokens[self.tok_index + peek_idx] if self.tok_index + peek_idx < len(self.tokens) else None
            next_next_tok = self.tokens[self.tok_index + peek_idx + 1] if self.tok_index + peek_idx + 1 < len(self.tokens) else None
            
            if next_tok and next_tok.type == T_IDENTIFIER and next_next_tok and next_next_tok.type == T_EQ:
                break

            res.register_advancement()
            self.advance()

            while self.current_tok.type == T_NEWLINE:
                res.register_advancement()
                self.advance()

            expr = res.register(self.expression())
            if res.error: return res
            positional_args.append(expr)

        return res.success(positional_args)

    def argument_list(self):
        """
        Grammar Rule: positional-list (COMMA keyword-list)? | keyword-list
        """
        res = ParseResult()
        positional_args = []
        keyword_args = []

        if self.current_tok.type == T_IDENTIFIER and self.peek() and self.peek().type == T_EQ:
            keyword_args = res.register(self.keyword_list())
            if res.error: return res

        elif self.current_tok.type != T_RPAREN:
            positional_args = res.register(self.positional_list())
            if res.error: return res

            if self.current_tok.type == T_COMMA:
                res.register_advancement()
                self.advance()

                while self.current_tok.type == T_NEWLINE:
                    res.register_advancement()
                    self.advance()

                if not (self.current_tok.type == T_IDENTIFIER and self.peek() and self.peek().type == T_EQ):
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Positional argument cannot follow keyword argument"
                    ))

                keyword_args = res.register(self.keyword_list())
                if res.error: return res

        return res.success((positional_args, keyword_args))

    def call(self):
        """
        Grammar Rule: factor ( (LPAREN (argument-list)? RPAREN) | (DOT IDENTIFIER) | (LPAREN3 expression RPAREN3) )*
        """
        res = ParseResult()
        atom = res.register(self.factor())
        if res.error:
            return res

        while self.current_tok and self.current_tok.type in (T_LPAREN, T_DOT, T_LPAREN3):
            if self.current_tok.type == T_LPAREN:
                res.register_advancement()
                self.advance()
                positional_args, keyword_args = [], []

                while self.current_tok.type == T_NEWLINE:
                    res.register_advancement()
                    self.advance()

                if self.current_tok.type != T_RPAREN:
                    args = res.register(self.argument_list())
                    if res.error:
                        return res
                    positional_args, keyword_args = args

                while self.current_tok.type == T_NEWLINE:
                    res.register_advancement()
                    self.advance()

                if self.current_tok.type != T_RPAREN:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected ')'"
                    ))
                res.register_advancement()
                self.advance()

                atom = FunctionCallNode(atom, positional_args, keyword_args)

            elif self.current_tok.type == T_DOT:
                res.register_advancement()
                self.advance()

                if self.current_tok.type != T_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected identifier"
                    ))

                attr_name_tok = self.current_tok
                res.register_advancement()
                self.advance()
                atom = AttrAccessNode(atom, attr_name_tok)

            elif self.current_tok.type == T_LPAREN3:
                res.register_advancement()
                self.advance()
                expr = res.register(self.expression())
                if res.error: return res
                if self.current_tok.type != T_RPAREN3:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected ']'"
                    ))
                res.register_advancement()
                self.advance()
                atom = IndexAccessNode(atom, expr)

        return res.success(atom)

    def factor(self):
        """
        Parses factors (numbers, parentheses, and unary operations).

        Grammar Rule:

        factor: INT | FLOAT | STRING | IDENTIFIER (LPAREN3 expression RPAREN3)* |
        LPAREN expression RPAREN | list-expression | dict-expression| anonymous_func_expr
        """
        res = ParseResult()
        token = self.current_tok

        if token.type in (T_INT, T_FLOAT):
            res.register_advancement()
            self.advance()
            return res.success(NumberNode(token))

        if token.type == T_STRING:
            res.register_advancement()
            self.advance()
            return res.success(StringNode(token))

        if token.type == T_FSTRING:
            res.register_advancement()
            self.advance()
            fstring_node = res.register(self._parse_fstring(token))
            if res.error:
                return res
            return res.success(fstring_node)

        if token.type == T_IDENTIFIER:
            res.register_advancement()
            self.advance()
            var_name_tok,index_node=token,[]

            if self.current_tok.type == T_LPAREN3:
                while self.current_tok and self.current_tok.type == T_LPAREN3:
                    res.register_advancement()
                    self.advance()

                    expression = res.register(self.expression())
                    if res.error: return res
                    index_node.append(expression)

                    if self.current_tok.type != T_RPAREN3:
                        return res.failure(InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end, "Expected ']"
                        ))
                    res.register_advancement()
                    self.advance()

            return res.success(VariableUseNode(token,index_node))

        if token.type == T_LPAREN:
            res.register_advancement()
            self.advance()
            expression = res.register(self.expression())
            if res.error:
                return res
            if self.current_tok.type != T_RPAREN:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start,
                                       self.current_tok.pos_end,
                                       "Expected ')'"))
            res.register_advancement()
            self.advance()
            return res.success(expression)

        if token.type == T_LPAREN3:
            list_expression = res.register(self.list_expression())
            if res.error:
                return res
            return res.success(list_expression)
        
        if token.type == T_LPAREN2:
            dict_expression = res.register(self.dict_expression())
            if res.error:
                return res
            return res.success(dict_expression)

        if token.type==T_KEYWORD and token.value=='method':
            anonymous_expr=res.register(self.anonymous_func_expr())
            if res.error:
                return res
            return res.success(anonymous_expr)

        return res.failure(
            InvalidSyntaxError(token.pos_start,
                               token.pos_end,
                               "Expected an expression (value, variable, '(', '[', '{', or operator)"))


    def term(self):
        """Parses terms, handling multiplication and division operations.
        
        Grammar Rule:

        unary ((MUL | DIV | MODULUS | FLOOR_DIV) unary)*
        """
        res = ParseResult()

        left_node = res.register(self.unary())
        if res.error:
            return res

        while self.current_tok and self.current_tok.type in (T_MUL, T_DIVIDE, T_MODULUS, T_FLOOR):
            operator = self.current_tok
            res.register_advancement()
            self.advance()
            right_node = res.register(self.unary())
            if res.error:
                return res
            left_node = BinaryOperationNode(left_node, operator, right_node)

        return res.success(left_node)

    def statements(self):
        """
        statements:
            call (COMMA call)*
            (EQUAL | PLUSEQUAL | MINUSEQUAL | MULEQUAL | DIVEQUAL | MODEQUAL | FLOOREQUAL | EXPEQUAL | BITOREQUAL | BITXOREQUAL | BITANDEQUAL | LSHIFTEQUAL | RSHIFTEQUAL)
            expression (COMMA expression)*
        """
        res = ParseResult()

        left_nodes = []

        # --- Parse LHS (calls/variables/attributes/indices)
        while True:
            left_node = res.register(self.call())
            if res.error: return res
            
            if not isinstance(left_node, (VariableUseNode, AttrAccessNode, IndexAccessNode)):
                return res.failure(InvalidSyntaxError(
                    left_node.pos_start, left_node.pos_end,
                    "Expected variable, attribute, or index for assignment"
                ))
                
            left_nodes.append(left_node)

            if self.current_tok.type != T_COMMA:
                break
            res.register_advancement()
            self.advance()

        operator = None

        # --- Expect '=' or augmented operator
        if self.current_tok.type != T_EQ:
            # --- Expect augmented operator
            if self.current_tok.type in (T_PLUSEQUAL, T_MINUSEQUAL, T_MULEQUAL, T_DIVIDEEQUAL, T_MODULUSEQUAL, T_FLOOREQUAL, T_EXPEQUAL, T_BITOREQUAL, T_BITXOREQUAL, T_BITANDEQUAL, T_LSHIFTEQUAL, T_RSHIFTEQUAL):
                operator = Token(
                    self.current_tok.type.replace('EQUAL', ''),
                    pos_start=self.current_tok.pos_start,
                    pos_end=self.current_tok.pos_end
                )
            else:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected '=' or '+=' or '-=' or '*=' or '/=' or '%=' or '//=' or '**=' or '|=' or '^=' or '&=' or '<<=' or '>>='"
                    )
                )
        res.register_advancement()
        self.advance()

        value_nodes = []
        # --- Parse RHS (expressions)
        while True:
            expr = res.register(self.expression())
            if res.error:
                return res
            if not operator:
                value_nodes.append(expr)
            else:
                val1 = expr
                value_nodes.append(BinaryOperationNode(left_node=left_nodes[len(value_nodes)], operator=operator, right_node=expr))

            if self.current_tok.type != T_COMMA:
                break
            res.register_advancement()
            self.advance()

        # --- Validation: number of vars == number of values
        if len(left_nodes) != len(value_nodes):
            if operator and len(value_nodes) == 1:
                # Allow cases like: a, b += 5
                for i in range(1, len(left_nodes)):
                    value_nodes.append(BinaryOperationNode(
                        left_node=left_nodes[i],
                        operator=operator,
                        right_node=val1
                    ))

        return res.success(AssignNode(left_nodes, value_nodes))

    def jump_statements(self):
        """
        Grammar Rule:
        jump-statements: KEYWORD:proceed | KEYWORD:escape |
        KEYWORD:yield (expression NEWLINE* (COMMA NEWLINE* expression NEWLINE*)*)?

        """
        res = ParseResult()

        if not (self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("proceed", "escape", "yield"))):
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start,
                                                  self.current_tok.pos_end,
                                                  "Expected 'proceed' or 'escape' or 'yield' "))

        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'proceed':
            pos_start = self.current_tok.pos_start.copy()
            res.register_advancement()
            self.advance()
            pos_end = self.current_tok.pos_start.copy()
            return res.success(ContinueNode(pos_start, pos_end))

        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'escape':
            pos_start = self.current_tok.pos_start.copy()
            res.register_advancement()
            self.advance()
            pos_end = self.current_tok.pos_start.copy()
            return res.success(BreakNode(pos_start, pos_end))

        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'yield':
            pos_start = self.current_tok.pos_start.copy()
            res.register_advancement()
            self.advance()

            nodes_to_return = []
            pos_end = self.current_tok.pos_start.copy()

            expression = res.try_register(self.expression())

            if expression:
                nodes_to_return.append(expression)
                pos_end = expression.pos_end.copy()

                while self.current_tok.type == T_NEWLINE:
                    res.register_advancement()
                    self.advance()

                while self.current_tok.type == T_COMMA:
                    res.register_advancement()
                    self.advance()

                    while self.current_tok.type == T_NEWLINE:
                        res.register_advancement()
                        self.advance()

                    expression = res.register(self.expression())
                    if res.error:
                        return res.failure(InvalidSyntaxError(
                            self.current_tok.pos_start, self.current_tok.pos_end,
                            "Expected expression after ',' in 'yield' statement"
                        ))
                    nodes_to_return.append(expression)
                    pos_end = expression.pos_end.copy()

                    while self.current_tok.type == T_NEWLINE:
                        res.register_advancement()
                        self.advance()

            else:
                self.reverse(res.to_reverse_count)
                pos_end = pos_start

            return res.success(
                ReturnNode(nodes_to_return, pos_start, pos_end))

    def expression(self):
        """
        Grammar Rule:

        jump_statements | ternary-expression
        """
        res = ParseResult()

        depth_error = self._enter_depth()
        if depth_error: return res.failure(depth_error)

        ternary_node = res.register(self.ternary_expression())
        if res.error:
            self._exit_depth()
            return res
            
        self._exit_depth()
        return res.success(ternary_node)

    def logical_expression(self):
        """
        Grammar Rule:

        bitwise-expression ((KEYWORD:AND | KEYWORD:OR) bitwise-expression)*
        """
        res = ParseResult()
        left_node = res.register(self.bitwise_expression())
        if res.error:
            return res

        while (self.current_tok and
               self.current_tok.type == T_KEYWORD and
               self.current_tok.value in ('and', 'or')):
            operator = self.current_tok
            res.register_advancement()
            self.advance()

            right_node = res.register(self.bitwise_expression())
            if res.error:
                return res

            left_node = BinaryOperationNode(left_node, operator, right_node)

        return res.success(left_node)

    def bitwise_expression(self):
        """
        Grammar Rule:
        
        bitwise-xor (BITOR bitwise-xor)*
        """
        res = ParseResult()
        left_node = res.register(self.bitwise_xor())
        if res.error:
            return res

        while self.current_tok and self.current_tok.type == T_BITOR:
            operator = self.current_tok
            res.register_advancement()
            self.advance()

            right_node = res.register(self.bitwise_xor())
            if res.error:
                return res

            left_node = BinaryOperationNode(left_node, operator, right_node)

        return res.success(left_node)

    def bitwise_xor(self):
        """
        Grammar Rule:
        
        bitwise-and (BITXOR bitwise-and)*
        """
        res = ParseResult()
        left_node = res.register(self.bitwise_and())
        if res.error:
            return res

        while self.current_tok and self.current_tok.type == T_BITXOR:
            operator = self.current_tok
            res.register_advancement()
            self.advance()

            right_node = res.register(self.bitwise_and())
            if res.error:
                return res

            left_node = BinaryOperationNode(left_node, operator, right_node)

        return res.success(left_node)

    def bitwise_and(self):
        """
        Grammar Rule:
        
        comp-expression (BITAND comp-expression)*
        """
        res = ParseResult()
        left_node = res.register(self.comp_expression())
        if res.error:
            return res

        while self.current_tok and self.current_tok.type == T_BITAND:
            operator = self.current_tok
            res.register_advancement()
            self.advance()

            right_node = res.register(self.comp_expression())
            if res.error:
                return res

            left_node = BinaryOperationNode(left_node, operator, right_node)

        return res.success(left_node)

    def comp_expression(self):
        """
        Grammar Rule:

        KEYWORD:NOT comp-expression | shift-expression
        ((EE | NEQ | LT | GT | LTE | GTE) shift-expression)*
        """
        res = ParseResult()

        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'not':
            operator_token = self.current_tok
            res.register_advancement()
            self.advance()

            node = res.register(self.comp_expression())
            if res.error:
                return res
            return res.success(UnaryOperationNode(operator_token, node))

        left_node = res.register(self.shift_expression())
        if res.error:
            return res
        while self.current_tok and self.current_tok.type in (T_EE,T_NEQ, T_LT, T_GT, T_GTE, T_LTE):
            operator = self.current_tok
            res.register_advancement()
            self.advance()
            right_node = res.register(self.shift_expression())
            if res.error:
                return res
            left_node = BinaryOperationNode(left_node, operator, right_node)

        return res.success(left_node)

    def shift_expression(self):
        """
        Grammar Rule:
        
        arith-expression ((LSHIFT | RSHIFT) arith-expression)*
        """
        res = ParseResult()
        left_node = res.register(self.arith_expression())
        if res.error:
            return res

        while self.current_tok and self.current_tok.type in (T_LSHIFT, T_RSHIFT):
            operator = self.current_tok
            res.register_advancement()
            self.advance()
            right_node = res.register(self.arith_expression())
            if res.error:
                return res
            left_node = BinaryOperationNode(left_node, operator, right_node)

        return res.success(left_node)

    def arith_expression(self):
        """Parses full expressions, handling addition and subtraction operations.
        
        Grammar Rule:

        term ((PLUS | MINUS) term)*
        """
        res = ParseResult()
        left_node = res.register(self.term())
        if res.error:
            return res

        while self.current_tok and self.current_tok.type in (T_PLUS, T_MINUS):
            operator = self.current_tok
            res.register_advancement()
            self.advance()
            right_node = res.register(self.term())
            if res.error:
                return res
            left_node = BinaryOperationNode(left_node, operator, right_node)

        return res.success(left_node)

    # ------------------------------------------------------------------
    # F-string parsing helper
    # ------------------------------------------------------------------

    def _parse_fstring(self, token):
        """
        Parse a T_FSTRING token's raw value into a FStringNode.

        The raw value contains ordinary text and {expr} placeholders.
        We split on the placeholders, then re-lex and re-parse each
        embedded expression using a fresh Lexer + Parser instance.

        Returns a ParseResult wrapping a FStringNode.
        """
        res = ParseResult()
        raw = token.value        
        pos_start = token.pos_start
        pos_end = token.pos_end
        filename = pos_start.file_name if pos_start else '<fstring>'

        parts = []     
        i = 0
        n = len(raw)

        while i < n:
            brace_start = raw.find('{', i)
            if brace_start == -1:
                literal = raw[i:]
                if literal:
                    parts.append(('literal', literal))
                break

            literal = raw[i:brace_start]
            if literal:
                parts.append(('literal', literal))

            depth = 1
            j = brace_start + 1
            while j < n and depth > 0:
                if raw[j] == '{':
                    depth += 1
                elif raw[j] == '}':
                    depth -= 1
                j += 1

            expr_src = raw[brace_start + 1 : j - 1] 

            sub_lexer = Lexer(filename, expr_src)
            sub_tokens, lex_error = sub_lexer.enumerate_tokens()
            if lex_error:
                return res.failure(InvalidSyntaxError(
                    pos_start, pos_end,
                    f"Error in f-string expression {{{expr_src}}}: {lex_error.details}"
                ))

            sub_parser = Parser(sub_tokens)
            sub_res = sub_parser.expression()
            if sub_res.error:
                return res.failure(InvalidSyntaxError(
                    pos_start, pos_end,
                    f"Error in f-string expression {{{expr_src}}}: {sub_res.error.details}"
                ))

            parts.append(('expr', sub_res.node))
            i = j 

        return res.success(FStringNode(parts, pos_start, pos_end))
