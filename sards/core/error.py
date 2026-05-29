"""
Module: Position and Error Tracking

This module provides utility classes for tracking the position of characters in an input text
and handling errors encountered during tokenization, parsing, or runtime execution.
"""

import os

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
# SOURCE DISPLAY HELPER
# ------------------------------

def string_with_arrows(text, pos_start, pos_end):
    """
    Produces a snippet of source text with a caret (^) underline pointing to the
    exact range of the error — similar to how Python displays syntax errors.

    Example output:
        switch x {
        ^^^^^^

    Parameters:
    - text (str): The full source text.
    - pos_start (Position): Start of the error token.
    - pos_end (Position): End of the error token.

    Returns:
    - str: Two lines — the source line, then the caret underline.
    """
    lines = text.splitlines()

    # Only show the line where the error *starts*
    idx = max(0, min(pos_start.line, len(lines) - 1))
    line = lines[idx]

    col_start = max(0, min(pos_start.col, len(line)))

    # If the error ends on the same line, use that column; otherwise
    # highlight to end-of-line.  Never go past line length.
    if pos_end.line == pos_start.line:
        col_end = max(col_start + 1, min(pos_end.col, len(line)))
    else:
        col_end = max(col_start + 1, len(line))

    indent  = '    '
    snippet = indent + line + '\n'
    snippet += indent + ' ' * col_start + '^' * (col_end - col_start)
    return snippet


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
        Create a formatted error message with file, line, source snippet and details.

        Returns a Python-style error block, e.g.:

            File test.sard, line 3
                switch x {
                ^^^^^^
            Invalid Syntax Error: Invalid keyword 'switch'
        """
        try:
            relative_path = os.path.relpath(
                self.pos_start.file_name, start=os.curdir
            ).replace('\\', '/')
        except ValueError:
            # relpath can fail across drives on Windows
            relative_path = self.pos_start.file_name

        header  = f"  File {relative_path}, line {self.pos_start.line + 1}"
        snippet = string_with_arrows(
            self.pos_start.file_text, self.pos_start, self.pos_end
        )
        return (
            f"{header}\n"
            f"{snippet}\n"
            f"{self.error_name}: {self.details}"
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
        Walk back through contexts to produce Python-like traceback with
        source-line snippets and caret pointers at each call site.

        Returns:
        - str: Full traceback text.
        """
        frames = []
        position = self.pos_start
        context  = self.context

        while context:
            try:
                relative_path = os.path.relpath(
                    position.file_name, start=os.curdir
                ).replace('\\', '/')
            except ValueError:
                relative_path = position.file_name

            snippet = string_with_arrows(
                position.file_text, position, self.pos_end
                if context.parent is None else position
            )

            frames.append(
                f"  File {relative_path}, line {position.line + 1}, "
                f"in {context.display_name}\n"
                f"{snippet}"
            )

            position = context.parent_entry_pos
            context  = context.parent

        frames.reverse()
        traceback_body = '\n'.join(frames)

        return (
            "Traceback (most recent call last):\n"
            + traceback_body + '\n'
            + f"{self.error_name}: {self.details}"
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
    def __init__(self, pos_start, pos_end, details, context):
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


class ArgumentError(RunTimeError):
    """
    Error for function call argument mismatches.
    Example: myFunc(1, 2, 3) when definition is myFunc(a, b).
    """
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, details, context)
        self.error_name = "ArgumentError"

class NotImplementedError(RunTimeError):
    """
    Error for unimplemented features.
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

class DictKeyError(RunTimeError):
    """
    Error raised when a dictionary key is not found.
    """
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, details, context)
        self.error_name = "DictKeyError"

class ValueError(RunTimeError):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, details, context)
        self.error_name = "ValueError"

class TypeError(RunTimeError):
    """
    Error for performing an operation on an inappropriate type.
    Example: calling an attribute that is not a method, like my_obj.age()
    """
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, details, context)
        self.error_name = "TypeError"

class AttributeError(RunTimeError):
    """
    Error for accessing a non-existent attribute or method on an object.
    Example: my_obj.fake_property
    """
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, details, context)
        self.error_name = "AttributeError"

class ModuleError(RunTimeError):
    """
    Error raised when a module cannot be found or a name inside a module
    cannot be resolved.
    Example: summon nonexistent_module
             summon foo from mymodule  # but 'foo' is not defined in mymodule
    """
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, details, context)
        self.error_name = "ModuleError"

class StackDepthExceededError(RunTimeError):
    """
    Error raised when the runtime recursion depth exceeds the maximum allowed limit.
    """
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, details, context)
        self.error_name = "StackDepthExceededError"