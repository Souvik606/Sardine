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
from sards.data_types import ListNode, StringNode, DictNode
from .constants import *
from .error import InvalidSyntaxError
from .lexer import Token

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
                                   "Expected '+', '-', '*', '/'"))
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
            while self.current_tok.type == T_NEWLINE:
                res.register_advancement()
                self.advance()

            if self.current_tok.type!=T_EOF and self.current_tok.type!=T_RPAREN2 and not(
                self.current_tok.type==T_KEYWORD and self.current_tok.value in ("yield","escape","proceed")
            ):
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

        if token.type==T_IDENTIFIER and ((self.peek() and self.peek().type==T_LPAREN)
        or (self.peek() and self.peek().type==T_DOT)):
            call_node=res.register(self.call())
            if res.error:
                return res
            return res.success(call_node)

        statement_node = res.register(self.statements())
        if res.error: return res
        node = res.register(res.success(statement_node))
        if res.error:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected int,float,identifier"))
        return res.success(node)

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

        declarations = res.register(self.attr_list())
        if res.error: return res

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

        KEYWORD:init LPAREN (IDENTIFIER (COMMA IDENTIFIER)*)? RPAREN LPAREN2 NEWLINE*
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

        param_name_toks = []
        if self.current_tok.type == T_IDENTIFIER:
            param_name_toks.append(self.current_tok)
            res.register_advancement()
            self.advance()
            while self.current_tok.type == T_COMMA:
                res.register_advancement()
                self.advance()
                if self.current_tok.type != T_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected identifier"
                    ))
                param_name_toks.append(self.current_tok)
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
        return res.success(InitNode(param_name_toks, body_node, pos_start, pos_end))

    def method_definition(self):
        """
        Grammar Rule:

        (KEYWORD:open | KEYWORD:guarded | KEYWORD:secret)? KEYWORD:method IDENTIFIER?
        LPAREN (IDENTIFIER (COMMA IDENTIFIER)*)? RPAREN
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

        param_name_toks = []
        if self.current_tok.type == T_IDENTIFIER:
            param_name_toks.append(self.current_tok)
            res.register_advancement()
            self.advance()
            while self.current_tok.type == T_COMMA:
                res.register_advancement()
                self.advance()
                if self.current_tok.type != T_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end, "Expected identifier"
                    ))
                param_name_toks.append(self.current_tok)
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

        return res.success(FunctionDefinitionNode(name_tok, param_name_toks, body_node, False,access_modifier_tok))

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

        return res.success(VariableAssignNode([var_name_tok], [value_node], [None]))

    def list_expression(self):
        """
        Grammar Rule:

        LPAREN3 (expression(COMMA expression)*)? RPAREN RPAREN3
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

        if self.current_tok.type == T_RPAREN3:
            res.register_advancement()
            self.advance()
        else:
            element_nodes.append(res.register(self.expression()))
            if res.error:
                return res
            while self.current_tok and self.current_tok.type == T_COMMA:
                res.register_advancement()
                self.advance()

                element_nodes.append(res.register(self.expression()))
                if res.error:
                    return res

            if self.current_tok.type != T_RPAREN3:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start,
                                       self.current_tok.pos_end,
                                       "Expected ',' or ']"))

            res.register_advancement()
            self.advance()

        return res.success(ListNode(element_nodes, pos_start, self.current_tok.pos_end.copy()))

    def dict_expression(self):
        """
        Grammar Rule:

        LPAREN2 (expression COLON expression(COMMA expression COLON expression)*)? RPAREN2
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

        if self.current_tok.type == T_RPAREN2:
            res.register_advancement()
            self.advance()
        else:
            key_node = res.register(self.expression())
            if res.error:
                return res
            if self.current_tok.type != T_COLON:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start,
                                       self.current_tok.pos_end,
                                       "Expected ':'"))
            res.register_advancement()
            self.advance()
            value_node = res.register(self.expression())
            if res.error:
                return res
            keyval_nodes.append((key_node, value_node))

            while self.current_tok and self.current_tok.type == T_COMMA:
                res.register_advancement()
                self.advance()

                key_node = res.register(self.expression())
                if res.error:
                    return res
                if self.current_tok.type != T_COLON:
                    return res.failure(
                        InvalidSyntaxError(self.current_tok.pos_start,
                                           self.current_tok.pos_end,
                                           "Expected ':'"))
                res.register_advancement()
                self.advance()
                value_node = res.register(self.expression())
                if res.error:
                    return res
                keyval_nodes.append((key_node, value_node))

            if self.current_tok.type != T_RPAREN2:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start,
                                       self.current_tok.pos_end,
                                       "Expected ',' or '}'"))

            res.register_advancement()
            self.advance()

        return res.success(DictNode(keyval_nodes, pos_start, self.current_tok.pos_end.copy()))

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

    def function_definition(self):
        """
        Grammar Rule:

        function-definition:
            KEYWORD:method IDENTIFIER? LPAREN (IDENTIFIER (COMMA IDENTIFIER)*)? RPAREN
            LPAREN2 (multiline | jump-statements)* RPAREN2
        """
        res = ParseResult()

        # 'method'
        if not (self.current_tok.type == T_KEYWORD and self.current_tok.value == 'method'):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected 'method'"))
        res.register_advancement()
        self.advance()

        # optional identifier (function name)
        if self.current_tok.type == T_IDENTIFIER:
            var_name_tok = self.current_tok
            res.register_advancement()
            self.advance()
            if self.current_tok.type != T_LPAREN:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start,
                                       self.current_tok.pos_end,
                                       "Expected '('"))
        else:
            var_name_tok = None
            if self.current_tok.type != T_LPAREN:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start,
                                       self.current_tok.pos_end,
                                       "Expected '('"))

        res.register_advancement()
        self.advance()

        # arguments
        arg_name_toks = []
        if self.current_tok.type == T_IDENTIFIER:
            arg_name_toks.append(self.current_tok)
            res.register_advancement()
            self.advance()

            while self.current_tok and self.current_tok.type == T_COMMA:
                res.register_advancement()
                self.advance()

                if self.current_tok.type != T_IDENTIFIER:
                    return res.failure(
                        InvalidSyntaxError(self.current_tok.pos_start,
                                           self.current_tok.pos_end,
                                           "Expected identifier"))

                arg_name_toks.append(self.current_tok)
                res.register_advancement()
                self.advance()

            if self.current_tok.type != T_RPAREN:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start,
                                       self.current_tok.pos_end,
                                       "Expected ',' or ')'"))
        else:
            if self.current_tok.type != T_RPAREN:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end,
                                       "Expected identifier or ')'"))

        res.register_advancement()
        self.advance()

        # '{'
        if self.current_tok.type != T_LPAREN2:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start,
                                                  self.current_tok.pos_end,
                                                  "Expected '{'"))
        res.register_advancement()
        self.advance()

        # body
        body_nodes, pos_start = [], self.current_tok.pos_start
        while self.current_tok.type != T_RPAREN2 and self.current_tok.type != T_EOF:
            if self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("yield","proceed","escape")):
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
        if self.current_tok.type != T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '}'"))
        res.register_advancement()
        self.advance()

        return res.success(FunctionDefinitionNode(var_name_tok, arg_name_toks, body_node, False))

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

        KEYWORD:choice ternary-expression LPAREN2 ((expression|statements) RPAREN2)|
        (NEWLINE multiline RPAREN2)
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

        choice_val = res.register(self.ternary_expression())
        if res.error:
            return res

        if not self.current_tok.type == T_LPAREN2:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start,
                                                  self.current_tok.pos_end,
                                                  "Expected '{'"))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

            body = res.register(self.multiline())
            if res.error:
                return res
            case = (choice_val, body, True)
            if not self.current_tok.type == T_RPAREN2:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start,
                                       self.current_tok.pos_end,
                                       "Expected '}'"))

            res.register_advancement()
            self.advance()
        else:
            if self.current_tok.type == T_IDENTIFIER and self.peek() and self.peek().type == T_EQ:
                body_node = res.register(self.statements())
            else:
                body_node = res.register(self.expression())
            if res.error:
                return res
            case = (choice_val, body_node, False)
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

        KEYWORD:fallback LPAREN2 ((expression|statements) RPAREN2)| (NEWLINE multiline RPAREN2)
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

        if self.current_tok.type == T_NEWLINE:
            res.register_advancement()
            self.advance()

            body = res.register(self.multiline())
            if res.error:
                return res
            default_case = (None, body, True)
            if not self.current_tok.type == T_RPAREN2:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start,
                                       self.current_tok.pos_end,
                                       "Expected '}'"))

            res.register_advancement()
            self.advance()
        else:
            if self.current_tok.type == T_IDENTIFIER and self.peek() and self.peek().type == T_EQ:
                body_node = res.register(self.statements())
            else:
                body_node = res.register(self.expression())
            if res.error:
                return res
            default_case = (None, body_node, False)
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

        # '{'
        if not self.current_tok.type == T_LPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '{'"))
        res.register_advancement()
        self.advance()

        # body
        body_nodes, pos_start = [], self.current_tok.pos_start
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
                                   "Expected '}'"))
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

        # '{'
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

        # '}'
        if not self.current_tok.type == T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '}'"))
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

        # '{'
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

        # '}'
        if not self.current_tok.type == T_RPAREN2:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected '}'"))
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

        (PLUS | MINUS) unary | exponent
        """
        res = ParseResult()
        token = self.current_tok

        if token.type in (T_PLUS, T_MINUS):
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

        node = res.register(res.success(left_node))
        if res.error:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected 'define',int,float,identifier,'+','-' or '('"))
        return res.success(node)

    def call(self):
        """
        Grammar Rule:

        attr-access (LPAREN (expression(COMMA expression)*)? RPAREN)*
        """
        res = ParseResult()
        atom = res.register(self.attr_access())
        if res.error:
            return res

        while self.current_tok.type == T_LPAREN:
            res.register_advancement()
            self.advance()
            arg_nodes = []

            if self.current_tok.type == T_RPAREN:
                res.register_advancement()
                self.advance()
            else:
                arg_nodes.append(res.register(self.expression()))
                if res.error:
                    return res

                while self.current_tok.type == T_COMMA:
                    res.register_advancement()
                    self.advance()
                    arg_nodes.append(res.register(self.expression()))
                    if res.error:
                        return res

                if self.current_tok.type != T_RPAREN:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected ',' or ')'"
                    ))
                res.register_advancement()
                self.advance()

            atom = FunctionCallNode(atom, arg_nodes)

        return res.success(atom)

    def attr_access(self):
        """
        Grammar Rule:

        factor (DOT IDENTIFIER)*
        """
        res = ParseResult()
        atom = res.register(self.factor())
        if res.error:
            return res

        while self.current_tok.type == T_DOT:
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

        return res.success(atom)

    def factor(self):
        """
        Parses factors (numbers, parentheses, and unary operations).

        Grammar Rule:

        factor: INT | FLOAT | STRING | IDENTIFIER (LPAREN3 expression RPAREN3)* |
        LPAREN expression RPAREN | list-expression | dict-expression
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

        return res.failure(
            InvalidSyntaxError(token.pos_start,
                               token.pos_end,
                               "Expected int, float,identifier,'+','-'or '('"))

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
            IDENTIFIER (LPAREN3 expression RPAREN3)*
            (COMMA IDENTIFIER (LPAREN3 expression RPAREN3)*)*
            (PLUSEQUAL | MINUSEQUAL | MULEQUAL | DIVEQUAL | MODEQUAL | FLOOREQUAL | EXPEQUAL)
            expression (COMMA expression)*
        """
        res = ParseResult()

        var_name_toks = []
        index_nodes = []
        value_nodes = []

        # --- Parse LHS (variables and optional indices)
        while True:
            if self.current_tok.type != T_IDENTIFIER:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected identifier"
                    )
                )

            var_name_toks.append(self.current_tok)
            res.register_advancement()
            self.advance()

            indices = []
            while self.current_tok and self.current_tok.type == T_LPAREN3:
                res.register_advancement()
                self.advance()

                expr = res.register(self.expression())
                if res.error:
                    return res
                indices.append(expr)

                if self.current_tok.type != T_RPAREN3:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected ')'"
                        )
                    )
                res.register_advancement()
                self.advance()

            index_nodes.append(indices if indices else None)

            if self.current_tok.type != T_COMMA:
                break
            res.register_advancement()
            self.advance()

        operator = None

        # --- Expect '='
        if self.current_tok.type != T_EQ:
            # --- Expect augmented operator
            if self.current_tok.type in (T_PLUSEQUAL, T_MINUSEQUAL, T_MULEQUAL, T_DIVIDEEQUAL, T_MODULUSEQUAL, T_FLOOREQUAL, T_EXPEQUAL):
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
                        "Expected '=' or '+=' or '-=' or '*=' or '/=' or '%=' or '//=' or '**='"
                    )
                )
        res.register_advancement()
        self.advance()

        # --- Parse RHS (expressions)
        while True:
            expr = res.register(self.expression())
            if res.error:
                return res
            if not operator:
                value_nodes.append(expr)
            else:
                val1 = expr
                value_nodes.append(BinaryOperationNode(left_node=VariableUseNode(var_name_tok=var_name_toks[len(value_nodes)], index_node=index_nodes[len(value_nodes)]), operator=operator, right_node=expr))

            if self.current_tok.type != T_COMMA:
                break
            res.register_advancement()
            self.advance()

        # --- Validation: number of vars == number of values
        if len(var_name_toks) != len(value_nodes):
            if operator and len(value_nodes) == 1:
                # Allow cases like: a, b += 5
                for i in range(1, len(var_name_toks)):
                    value_nodes.append(BinaryOperationNode(
                        left_node=VariableUseNode(var_name_tok=var_name_toks[i], index_node=index_nodes[i]),
                        operator=operator,
                        right_node=val1
                    ))
            else:
                return res.failure(
                    InvalidSyntaxError(
                        var_name_toks[0].pos_start,
                        value_nodes[-1].pos_end,
                        f"Mismatched assignment count: {len(var_name_toks)} variables, {len(value_nodes)} values"
                    )
            )

        return res.success(VariableAssignNode(var_name_toks, value_nodes, index_nodes))

    def jump_statements(self):
        res = ParseResult()

        if not (self.current_tok.type == T_KEYWORD and (self.current_tok.value in ("proceed","escape","yield"))):
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start,
                                                  self.current_tok.pos_end,
                                                  "Expected 'proceed' or 'escape' or 'yield' "))

        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'proceed':
            res.register_advancement()
            self.advance()
            return res.success(ContinueNode(self.current_tok.pos_start.copy(),
                                            self.current_tok.pos_start.copy()))

        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'escape':
            res.register_advancement()
            self.advance()
            return res.success(BreakNode(self.current_tok.pos_start.copy(),
                                         self.current_tok.pos_start.copy()))

        if self.current_tok.type == T_KEYWORD and self.current_tok.value == 'yield':
            res.register_advancement()
            self.advance()

            expression = res.try_register(self.expression())
            if not expression:
                self.reverse(res.to_reverse_count)

            return res.success(
                ReturnNode(expression, self.current_tok.pos_start.copy(),
                           self.current_tok.pos_start.copy()))

    def expression(self):
        """
        Grammar Rule:

        jump_statements | ternary-expression
        """
        res = ParseResult()

        ternary_node = res.register(self.ternary_expression())
        if res.error:
            return res
        node = res.register(res.success(ternary_node))
        if res.error:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected int,float,identifier"))
        return res.success(node)

    def logical_expression(self):
        """
        Grammar Rule:

        comp-expression ((KEYWORD:AND | KEYWORD:OR) comp-expression)*
        """
        res = ParseResult()
        left_node = res.register(self.comp_expression())
        if res.error:
            return res

        while (self.current_tok and
               self.current_tok.type == T_KEYWORD and
               self.current_tok.value in ('and', 'or')):
            operator = self.current_tok
            res.register_advancement()
            self.advance()

            right_node = res.register(self.comp_expression())
            if res.error:
                return res

            left_node = BinaryOperationNode(left_node, operator, right_node)

        node = res.register(res.success(left_node))
        if res.error:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected int,float,identifier"))
        return res.success(node)

    def comp_expression(self):
        """
        Grammar Rule:

        KEYWORD:NOT comp-expression | arith-expression
        ((EE | NEQ | LT | GT | LTE | GTE) arith-expression)*
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

        left_node = res.register(self.arith_expression())
        if res.error:
            return res
        while self.current_tok and self.current_tok.type in (T_EE,T_NEQ, T_LT, T_GT, T_GTE, T_LTE):
            operator = self.current_tok
            res.register_advancement()
            self.advance()
            right_node = res.register(self.arith_expression())
            if res.error:
                return res
            left_node = BinaryOperationNode(left_node, operator, right_node)

        node = res.register(res.success(left_node))
        if res.error:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected int,float,identifier,'+','-','not' or '('"))
        return res.success(node)

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

        node = res.register(res.success(left_node))
        if res.error:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start,
                                   self.current_tok.pos_end,
                                   "Expected 'define',int,float,identifier,'+','-' or '('"))
        return res.success(node)
