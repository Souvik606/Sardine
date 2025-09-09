"""
Module: Position and Error Tracking

This module provides utility classes for tracking the position of characters in an input text
and handling errors encountered during tokenization, parsing, or runtime execution.
"""

# ------------------------------
# POSITION CLASS
# ------------------------------

class Position:
    """
    Tracks the current position in the input text, including index, line, and column.
    Useful for error reporting, so the interpreter can say exactly
    where (file, line, column) a problem occurred.
    """

    def __init__(self, index, line, col, file_name, file_text):
        """
        Initialize a Position object.

        Parameters:
        - index (int): The absolute character index in the input string.
        - line (int): The current line number (0-based).
        - col (int): The current column number (0-based).
        - file_name (str): File being processed (for error messages).
        - file_text (str): The full text of the file (for context in errors).
        """
        self.index = index
        self.line = line
        self.col = col
        self.file_name = file_name
        self.file_text = file_text

    def advance(self, current_char=None):
        """
        Move the position forward by one character.
        - Always increments `index` and `col`.
        - If the character is a newline (`\n`) or statement terminator (`;`),
          resets column to 0 and increments line.

        Returns:
        - self (Position): Updated position object.
        """
        self.index += 1
        self.col += 1

        if current_char == '\n' or current_char == ';':
            self.line += 1
            self.col = 0

        return self

    def copy(self):
        """
        Create and return a copy of this Position.
        Useful because errors need to freeze a snapshot of where they happened.

        Returns:
        - Position: new object with same values.
        """
        return Position(self.index, self.line, self.col, self.file_name, self.file_text)


# ------------------------------
# BASE ERROR CLASS
# ------------------------------

class BaseError:
    """
    Base class for all errors (both compile-time and runtime).
    Stores where the error occurred and what it was.
    """

    def __init__(self, pos_start, pos_end, error_name, details):
        """
        Initialize a BaseError.

        Parameters:
        - pos_start (Position): Start of error.
        - pos_end (Position): End of error.
        - error_name (str): Short name of error type (e.g. "SyntaxError").
        - details (str): Human-readable description of what went wrong.
        """
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def to_string(self):
        """
        Create a formatted error message with file, line, and details.

        Returns:
        - str: Example -> "Invalid Syntax: unexpected token
                          File test.lang, line 3"
        """
        return (
            f"{self.error_name}: {self.details}\n"
            f"File {self.pos_start.file_name}, line {self.pos_start.line + 1}"
        )


# ------------------------------
# COMPILE-TIME ERRORS
# ------------------------------

class IllegalCharError(BaseError):
    """
    Error for encountering a character not in the language alphabet.
    Example: "$" if not allowed.
    """
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, "Illegal Character Error", details)


class InvalidSyntaxError(BaseError):
    """
    Error for invalid grammar or sequence of tokens.
    Example: `1 + * 2`
    """
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, "Invalid Syntax Error", details)


class ExpectedCharError(BaseError):
    """
    Error when a particular character was expected but not found.
    Example: missing closing parenthesis `(` without `)`.
    """
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, "Expected Character", details)

class DictKeyError(Error): # pylint: disable=too-few-public-methods
    """
    Handles errors caused by non-existent dictionary keys or invalid key types. 

    Inherits from:
    - Error
    """
    def __init__(self,pos_start,pos_end,details):
        super().__init__(pos_start,pos_end,'Dictionary Key Error',details)

# ------------------------------
# RUNTIME ERRORS
# ------------------------------

class RunTimeError(BaseError):
    """
    Base class for all runtime errors.
    Stores execution context so traceback can be generated.
    """

    def __init__(self, pos_start, pos_end, details, context):
        """
        Initialize a RunTimeError.

        Parameters:
        - pos_start (Position): Where runtime error started.
        - pos_end (Position): Where runtime error ended.
        - details (str): Error explanation.
        - context (Context): Current execution context (call stack info).
        """
        super().__init__(pos_start, pos_end, "RunTimeError", details)
        self.context = context

    def generate_traceback(self):
        """
        Walk back through contexts to produce Python-like traceback.

        Returns:
        - str: Traceback text showing file, line, and function call chain.
        """
        result = ''
        position = self.pos_start
        context = self.context

        while context:
            result = (
                f"File {position.file_name}, line {position.line + 1}, "
                f"in {context.display_name}\n"
            ) + result
            # step into parent context
            position = context.parent_entry_pos
            context = context.parent

        return (
            "Traceback (most recent call last):\n" +
            result +
            f"{self.error_name}: {self.details}"
        )

    def to_string(self):
        """
        Override default error string.
        Returns the full traceback instead of a one-line message.
        """
        return self.generate_traceback()


# ------------------------------
# SPECIFIC RUNTIME ERRORS
# ------------------------------

class IllegalOperationError(RunTimeError):
    """
    Error for invalid operations (e.g. adding string to number if not allowed).
    """
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, details, context)
        self.error_name = "IllegalOperationError"


class DivisionByZeroError(RunTimeError):
    """
    Error for division by zero (runtime math exception).
    """
    def __init__(self, pos_start, pos_end, details,context):
        super().__init__(pos_start, pos_end, "Division by zero", context)
        self.error_name = "DivisionByZeroError"


class IndexOutOfBoundsError(RunTimeError):
    """
    Error for invalid list/array indexing.
    Example: arr[10] when len(arr) == 3.
    """
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, details, context)
        self.error_name = "IndexOutOfBoundsError"
        

class NameError(RunTimeError):
    """
    Error for using an undefined variable/function name.
    Example: print(x) when x is not defined.
    """
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, details, context)
        self.error_name = "NameError"


class ArgumentError(RuntimeError):
    """
    Error for function call argument mismatches.
    Example: myFunc(1, 2, 3) when definition is myFunc(a, b).
    """
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, details, context)
        self.error_name = "ArgumentError"

class NotImplementedError(RuntimeError):
    """
    Error for function call argument mismatches.
    Example: myFunc(1, 2, 3) when definition is myFunc(a, b).
    """
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, details, context)
        self.error_name = "NotImplementedError"

class InvalidErrorTypeError(RunTimeError):
    """
    Error raised when a 'trap' block specifies an invalid or unsupported error type.
    Example: trap UnknownError e { ... }
    """
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, details, context)
        self.error_name = "InvalidErrorTypeError"