"""
Module: token_definitions

This module defines constants used for tokenization, including digit characters 
and token types for mathematical expressions.
"""
import string

# Set of characters representing numerical digits
DIGITS = '0123456789'
LETTERS = string.ascii_letters
LETTERS_DIGITS = DIGITS + LETTERS

# Token Types for mathematical operations and symbols
T_INT = 'INT'  # Integer number token
T_FLOAT = 'FLOAT'  # Floating-point number token
T_STRING = 'STRING'
T_IDENTIFIER = 'IDENTIFIER'  # Identifier token
T_KEYWORD = 'KEYWORD'
T_ERROR='ERROR'
T_PLUS = 'PLUS'  # Addition operator (+)
T_MINUS = 'MINUS'  # Subtraction operator (-)
T_MUL = 'MUL'  # Multiplication operator (*)
T_DIVIDE = 'DIV'  # Division operator (/)
T_MODULUS = 'MOD'
T_FLOOR = 'FLOOR'
T_EXP = 'EXP'  # Exponentiation operator (**)
T_EQ = 'EQUAL'
T_NEQ = 'NOTEQUAL'
T_EE = 'DOUBLEEQUAL'
T_LT = 'LESSTHAN'
T_GT = 'GREATERTHAN'
T_LTE = 'LESSERTHANEQUAL'
T_GTE = 'GREATERTHANEQUAL'
T_ARROW="ARROW"
T_LPAREN = 'LPAREN'  # Left parenthesis (
T_RPAREN = 'RPAREN'  # Right parenthesis )
T_LPAREN2 = 'LPAREN2'
T_RPAREN2 = 'RPAREN2'
T_LPAREN3 = 'LPAREN3'
T_RPAREN3 = 'RPAREN3'
T_COLON = 'COLON'
T_COMMA = 'COMMA'
T_NEWLINE = 'NEWLINE'
T_EOF = 'EOF'  # End of File
T_QUESTION = 'QUESTION'

# Keywords list

KEYWORDS = ['define', 'and', 'or', 'not', 'when', 'orwhen', 'otherwise', 'Cycle', 'whenever',
            'method', 'yield', 'escape', 'proceed', 'menu', 'choice', 'fallback','risk','trap','clean']

ERROR_TYPES=['RunTimeError','IllegalOperationError','DivisionByZeroError','IndexOutOfBoundsError',
             'NameError','ArgumentError','InvalidErrorTypeError']