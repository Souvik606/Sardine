"""
Module: lexer

This module implements a simple lexical analyzer (lexer) for mathematical expressions.
It reads an input string and converts it into a sequence of tokens,
handling numbers, operators, and parentheses.

Classes:
- Token: Represents a single token with a type and an optional value.
- Lexer: Performs lexical analysis, converting input text into tokens.

Functions:
- run: Executes the lexer on a given input and returns tokens or errors.
"""

from .constants import *
from .error import Position, IllegalCharError, ExpectedCharError


class Token:
    """
    Represents a token in the input with a specific type and optional value.

    Attributes:
    - type (str): The type of the token (e.g., INT, FLOAT, PLUS).
    - value (any, optional): The value of the token (e.g., a number for INT/FLOAT,
        or None for operators).
    - pos_start (Position, optional): The starting position of the token.
    - pos_end (Position, optional): The ending position of the token.
    """

    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end

    def __repr__(self):
        """
        Returns a string representation of the token.

        Returns:
        - str: Formatted string representation of the token.
        """
        return f'{self.type}: {self.value}' if self.value is not None else (f'{self.type}:'
                f'{self.pos_start.line if self.pos_start else ""}')


class Lexer:
    """
    Performs lexical analysis by reading input text and generating tokens.

    Attributes:
    - filename (str): The name of the source file being processed.
    - text (str): The input string to be tokenized.
    - pos (Position): The current position in the input text.
    - current_char (str, optional): The character currently being processed.
    """

    def __init__(self, filename, text):
        self.filename = filename
        self.text = text
        self.pos = Position(-1, 0, -1, filename, text)
        self.current_char = None
        self.advance()

    def advance(self):
        """
        Moves to the next character in the input text.

        Updates the current character and position.
        """
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.index] if self.pos.index < len(self.text) else None

    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in LETTERS_DIGITS + '_':
            id_str += self.current_char
            self.advance()

        if id_str in KEYWORDS:token_type=T_KEYWORD
        elif id_str in ERROR_TYPES:token_type=T_ERROR
        else:token_type=T_IDENTIFIER

        return Token(token_type, id_str, pos_start, self.pos)

    def make_equals(self):
        pos_start = self.pos.copy()
        self.advance()
        token_type = T_EQ

        if self.current_char == '=':
            self.advance()
            token_type = T_EE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_floor(self):
        pos_start = self.pos.copy()
        self.advance()
        token_type = T_DIVIDE

        if self.current_char == '/':
            self.advance()
            token_type = T_FLOOR
            if self.current_char == '=':
                self.advance()
                token_type = T_FLOOREQUAL
        elif self.current_char == '=':
            self.advance()
            token_type = T_DIVIDEEQUAL

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_mul(self):
        pos_start = self.pos.copy()
        self.advance()
        token_type = T_MUL

        if self.current_char == '*':
            self.advance()
            token_type = T_EXP
            if self.current_char == '=':
                self.advance()
                token_type = T_EXPEQUAL
        elif self.current_char == '=':
            self.advance()
            token_type = T_MULEQUAL

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_plus(self):
        pos_start = self.pos.copy()
        self.advance()
        token_type = T_PLUS

        if self.current_char == "=":
            self.advance()
            token_type = T_PLUSEQUAL

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_sub(self):
        pos_start=self.pos.copy()
        self.advance()
        token_type=T_MINUS

        if self.current_char==">":
            self.advance()
            token_type=T_ARROW
        elif self.current_char=="=":
            self.advance()
            token_type=T_MINUSEQUAL

        return Token(token_type,pos_start=pos_start,pos_end=self.pos)
    
    def make_mod(self):
        pos_start = self.pos.copy()
        self.advance()
        token_type = T_MODULUS

        if self.current_char == '=':
            self.advance()
            token_type = T_MODULUSEQUAL

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            return Token(T_NEQ, pos_start=pos_start, pos_end=self.pos), None

        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "'=' (after !)")

    def make_lesser(self):
        pos_start = self.pos.copy()
        self.advance()
        token_type = T_LT

        if self.current_char == '=':
            self.advance()
            token_type = T_LTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_greater(self):
        pos_start = self.pos.copy()
        self.advance()
        token_type = T_GT

        if self.current_char == '=':
            self.advance()
            token_type = T_GTE

        return Token(token_type, pos_start=pos_start, pos_end=self.pos)

    def make_string(self):
        string = ''
        pos_start = self.pos.copy()
        escape_character = False
        self.advance()

        escape_characters = {'n': '\n', 't': '\t'}

        while self.current_char is not None and self.current_char != '"' or escape_character:
            if escape_character:
                string += escape_characters.get(self.current_char, self.current_char)
                escape_character = False
            else:
                if self.current_char == '\\':
                    escape_character = True
                else:
                    string += self.current_char
            self.advance()

        self.advance()
        return Token(T_STRING, string, pos_start, self.pos)

    def make_number(self):
        """
        Extracts a numerical value (integer or float) from the input text.

        Returns:
        - Token: A token of type INT or FLOAT based on the extracted number.
        """
        number = ''
        is_float = False
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if is_float:
                    break
                is_float = True
                number += '.'
            else:
                number += self.current_char
            self.advance()

        return (Token(T_FLOAT, float(number), pos_start, self.pos) if is_float
                else Token(T_INT, int(number), pos_start, self.pos))

    def enumerate_tokens(self):
        """
        Tokenizes the input text into a list of tokens.

        Returns:
        - list: A list of Token objects.
        - Error or None: Returns an error if an invalid character is encountered.
        """
        tokens = []

        while self.current_char is not None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in [';', '\n']:
                tokens.append(Token(T_NEWLINE, pos_start=self.pos))
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())
            elif self.current_char == '"':
                tokens.append(self.make_string())
            elif self.current_char == '+':
                tokens.append(self.make_plus())
            elif self.current_char == '-':
                tokens.append(self.make_sub())
            elif self.current_char == '*':
                tokens.append(self.make_mul())
            elif self.current_char == '/':
                tokens.append(self.make_floor())
            elif self.current_char == '%':
                tokens.append(self.make_mod())
            elif self.current_char == '=':
                tokens.append(self.make_equals())
            elif self.current_char == '!':
                tok, error = self.make_not_equals()
                if error:
                    return [], error
                tokens.append(tok)
            elif self.current_char == '>':
                tokens.append(self.make_greater())
            elif self.current_char == '<':
                tokens.append(self.make_lesser())
            elif self.current_char == '(':
                tokens.append(Token(T_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(T_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == '{':
                tokens.append(Token(T_LPAREN2, pos_start=self.pos))
                self.advance()
            elif self.current_char == '}':
                tokens.append(Token(T_RPAREN2, pos_start=self.pos))
                self.advance()
            elif self.current_char == '[':
                tokens.append(Token(T_LPAREN3, pos_start=self.pos))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(T_RPAREN3, pos_start=self.pos))
                self.advance()
            elif self.current_char == ':':
                tokens.append(Token(T_COLON, pos_start=self.pos))
                self.advance()
            elif self.current_char == ',':
                tokens.append(Token(T_COMMA, pos_start=self.pos))
                self.advance()
            elif self.current_char == '?':
                tokens.append(Token(T_QUESTION, pos_start=self.pos))
                self.advance()
            elif self.current_char == '.':
                tokens.append(Token(T_DOT, pos_start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f'"{char}"')

        tokens.append(Token(T_EOF, pos_start=self.pos))
        return tokens, None

