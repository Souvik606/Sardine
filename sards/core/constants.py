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
T_FSTRING = 'FSTRING'  # Interpolated string $"..." token
T_IDENTIFIER = 'IDENTIFIER'  # Identifier token
T_KEYWORD = 'KEYWORD'
T_ERROR='ERROR'
T_PLUS = 'PLUS'  # Addition operator (+)
T_PLUSEQUAL = 'PLUSEQUAL' # Augmented addition operator (+=)
T_MINUS = 'MINUS'  # Subtraction operator (-)
T_MINUSEQUAL = 'MINUSEQUAL' # Augmented subtraction operator (-=)
T_MUL = 'MUL'  # Multiplication operator (*)
T_MULEQUAL = 'MULEQUAL' # Augmented multiplication operator (*=)
T_DIVIDE = 'DIV'  # Division operator (/)
T_DIVIDEEQUAL = 'DIVEQUAL' # Augmented division operator (/=)
T_MODULUS = 'MOD' # Modulus operator (%)
T_MODULUSEQUAL = 'MODEQUAL' # Augmented modulus operator (%=)
T_FLOOR = 'FLOOR' # Floor division operator (//)
T_FLOOREQUAL = 'FLOOREQUAL' # Augmented floor division operator (//=)
T_EXP = 'EXP'  # Exponentiation operator (**)
T_EXPEQUAL = 'EXPEQUAL' #Augmented exponentiation operator (**=)
T_BITAND = 'BITAND'  # Bitwise AND operator (&)
T_BITANDEQUAL = 'BITANDEQUAL' # Augmented bitwise AND operator (&=)
T_BITXOR = 'BITXOR'  # Bitwise XOR operator (^)
T_BITXOREQUAL = 'BITXOREQUAL' # Augmented bitwise XOR operator (^=)
T_BITOR = 'BITOR'  # Bitwise OR operator (|)
T_BITOREQUAL = 'BITOREQUAL' # Augmented bitwise OR operator (|=)
T_BITNOT = 'BITNOT'  # Bitwise NOT operator (~)
T_LSHIFT = 'LSHIFT'  # Left shift operator (<<)
T_LSHIFTEQUAL = 'LSHIFTEQUAL' # Augmented left shift operator (<<=)
T_RSHIFT = 'RSHIFT'  # Right shift operator (>>)
T_RSHIFTEQUAL = 'RSHIFTEQUAL' # Augmented right shift operator (>>=)
T_EQ = 'EQUAL' # Assignment operator (=)
T_NEQ = 'NOTEQUAL' # Not equal operator (!=)
T_EE = 'DOUBLEEQUAL' # Equality operator (==)
T_LT = 'LESSTHAN' # Less than operator (<)
T_GT = 'GREATERTHAN' # Greater than operator (>)
T_LTE = 'LESSERTHANEQUAL' # Less than or equal to operator (<=)
T_GTE = 'GREATERTHANEQUAL' # Greater than or equal to operator (>=)
T_LARROW= 'LARROW' # Left arrow operator (<-)
T_LPAREN = 'LPAREN' # Left parenthesis (
T_RPAREN = 'RPAREN' # Right parenthesis )
T_LPAREN2 = 'LPAREN2' # Left curvy bracket {
T_RPAREN2 = 'RPAREN2' # Right curvy bracket }
T_LPAREN3 = 'LPAREN3' # Left square bracket [
T_RPAREN3 = 'RPAREN3' # Right square bracket ]
T_COLON = 'COLON'
T_DOT="DOT"
T_COMMA = 'COMMA'
T_NEWLINE = 'NEWLINE'
T_EOF = 'EOF'  # End of File
T_QUESTION = 'QUESTION'

# Keywords list

KEYWORDS = ['define', 'and', 'or', 'not', 'when', 'orwhen', 'otherwise', 'Cycle', 'whenever',
            'method', 'yield', 'escape', 'proceed', 'menu', 'choice', 'fallback','risk','trap','clean',
            'model','attr','init','open','secret','guarded','trace',
            'summon', 'from', 'as']

ERROR_TYPES=['RunTimeError','IllegalOperationError','DivisionByZeroError','IndexOutOfBoundsError',
             'NameError','ArgumentError','InvalidErrorTypeError','ModuleError']