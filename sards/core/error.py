"""
Module: Position and Error Tracking

This module provides utility classes for tracking the position of characters in an input text
and handling errors encountered during tokenization, parsing, or runtime execution.

Error Code Scheme
-----------------
E1001–E1099 : Lexer / Illegal character errors
E2001–E2099 : Syntax / parse errors
E3001–E3099 : Name / scope errors
E4001–E4099 : Type errors
E5001–E5099 : Operation / arithmetic errors
E6001–E6099 : Argument / call errors
E7001–E7099 : Index / attribute / key access errors
E8001–E8099 : Module / import errors
E9001–E9099 : Runtime / general errors
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
        - If the character is a newline (`\\n`) or statement terminator (`;`),
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


def _levenshtein(a, b):
    """
    Compute the Levenshtein edit distance between two strings.
    Used for 'Did you mean ...?' suggestions.
    """
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[n]


def fuzzy_match(name, candidates, max_distance=3):
    """
    Find the closest candidate to *name* using Levenshtein distance.

    Parameters:
    - name (str): The name that was not found.
    - candidates (iterable): Known names to search through.
    - max_distance (int): Maximum edit distance to consider a match.

    Returns:
    - str or None: The closest match within max_distance, or None.
    """
    best = None
    best_dist = max_distance + 1
    for c in candidates:
        d = _levenshtein(name.lower(), c.lower())
        if d < best_dist:
            best_dist = d
            best = c
    return best if best_dist <= max_distance else None


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
    if text is None or not isinstance(text, str):
        return ""
    if pos_start is None or getattr(pos_start, 'line', None) is None or getattr(pos_start, 'col', None) is None:
        return ""
    if pos_end is None or getattr(pos_end, 'line', None) is None or getattr(pos_end, 'col', None) is None:
        pos_end = pos_start

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

    Attributes:
    - error_code (str): Short code like 'E2001' shown in the header.
    - hint (str | None): Optional resolution suggestion shown after the message.
    """

    # Default code — subclasses override this as a class attribute
    error_code = 'E0000'

    def __init__(self, pos_start, pos_end, error_name, details, hint=None):
        """
        Initialize a BaseError.

        Parameters:
        - pos_start (Position): Start of error.
        - pos_end (Position): End of error.
        - error_name (str): Short name of error type (e.g. "SyntaxError").
        - details (str): Human-readable description of what went wrong.
        - hint (str, optional): A resolution suggestion to display after the message.
        """
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details
        self.hint = hint

    def to_string(self):
        """
        Create a formatted error message with error code, file, line,
        source snippet, details, and optional hint.

        Returns a Python-style error block
        """
        try:
            relative_path = os.path.relpath(
                self.pos_start.file_name, start=os.curdir
            ).replace('\\', '/')
        except ValueError:
            # relpath can fail across drives on Windows
            relative_path = self.pos_start.file_name

        header  = f"  [{self.error_code}] File {relative_path}, line {self.pos_start.line + 1}"
        snippet = string_with_arrows(
            self.pos_start.file_text, self.pos_start, self.pos_end
        )
        result = (
            f"{header}\n"
            f"{snippet}\n"
            f"{self.error_name}: {self.details}"
        )
        if self.hint:
            result += f"\n  Hint: {self.hint}"
        return result


# ------------------------------
# COMPILE-TIME ERRORS
# ------------------------------

class IllegalCharError(BaseError):
    """
    [E1001] Error for encountering a character not in the language alphabet.
    Example: an unsupported symbol like '@'.
    """
    error_code = 'E1001'

    def __init__(self, pos_start, pos_end, details='', hint=None):
        if hint is None:
            hint = "Remove or replace the unrecognised character."
        super().__init__(pos_start, pos_end, "Illegal Character Error", details, hint)


class ExpectedCharError(BaseError):
    """
    [E1002] Error when a particular character was expected but not found.
    Example: missing closing parenthesis `(` without `)`.
    """
    error_code = 'E1002'

    def __init__(self, pos_start, pos_end, details='', hint=None):
        super().__init__(pos_start, pos_end, "Expected Character", details, hint)


class InvalidSyntaxError(BaseError):
    """
    [E2001] Error for invalid grammar or sequence of tokens.
    Example: `1 + * 2`
    """
    error_code = 'E2001'

    def __init__(self, pos_start, pos_end, details='', hint=None):
        super().__init__(pos_start, pos_end, "Invalid Syntax Error", details, hint)


# ------------------------------
# RUNTIME ERRORS
# ------------------------------

class RunTimeError(BaseError):
    """
    [E9001] Base class for all runtime errors.
    Stores execution context so traceback can be generated.
    """
    error_code = 'E9001'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        """
        Initialize a RunTimeError.

        Parameters:
        - pos_start (Position): Where runtime error started.
        - pos_end (Position): Where runtime error ended.
        - details (str): Error explanation.
        - context (Context): Current execution context (call stack info).
        - hint (str, optional): Resolution suggestion.
        """
        super().__init__(pos_start, pos_end, "RunTimeError", details, hint)
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
            if position is None or getattr(position, 'file_name', None) is None or getattr(position, 'file_text', None) is None:
                relative_path = "<unknown>"
                snippet = ""
                line_str = "?"
            else:
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
                line_str = str(position.line + 1)

            frames.append(
                f"  File {relative_path}, line {line_str}, "
                f"in {context.display_name}\n"
                f"{snippet}"
            )

            position = context.parent_entry_pos
            context  = context.parent

        frames.reverse()
        traceback_body = '\n'.join(frames)

        result = (
            f"[{self.error_code}] Traceback (most recent call last):\n"
            + traceback_body + '\n'
            + f"{self.error_name}: {self.details}"
        )
        if self.hint:
            result += f"\n  Hint: {self.hint}"
        return result

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
    [E5001] Error for invalid operations (e.g. adding string to number if not allowed).
    """
    error_code = 'E5001'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        super().__init__(pos_start, pos_end, details, context, hint)
        self.error_name = "IllegalOperationError"


class DivisionByZeroError(RunTimeError):
    """
    [E5002] Error for division by zero (runtime math exception).
    """
    error_code = 'E5002'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        if hint is None:
            hint = "Check that the divisor is not zero before dividing. Example: `when b != 0 { result = a / b }`"
        super().__init__(pos_start, pos_end, "Division by zero", context, hint)
        self.error_name = "DivisionByZeroError"


class IndexOutOfBoundsError(RunTimeError):
    """
    [E7001] Error for invalid list/array indexing.
    Example: arr[10] when len(arr) == 3.
    """
    error_code = 'E7001'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        if hint is None:
            hint = "Use `len(collection) - 1` to find the last valid index, or check bounds before accessing."
        super().__init__(pos_start, pos_end, details, context, hint)
        self.error_name = "IndexOutOfBoundsError"


class NameError(RunTimeError):
    """
    [E3001] Error for using an undefined variable/function name.
    Example: show(x) when x is not defined.
    """
    error_code = 'E3001'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        super().__init__(pos_start, pos_end, details, context, hint)
        self.error_name = "NameError"


class ArgumentError(RunTimeError):
    """
    [E6001] Error for function call argument mismatches.
    Example: myFunc(1, 2, 3) when definition is myFunc(a, b).
    """
    error_code = 'E6001'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        super().__init__(pos_start, pos_end, details, context, hint)
        self.error_name = "ArgumentError"


class NotImplementedError(RunTimeError):
    """
    [E9004] Error for unimplemented features.
    """
    error_code = 'E9004'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        super().__init__(pos_start, pos_end, details, context, hint)
        self.error_name = "NotImplementedError"


class InvalidErrorTypeError(RunTimeError):
    """
    [E9003] Error raised when a 'trap' block specifies an invalid or unsupported error type.
    Example: trap UnknownError e { ... }
    """
    error_code = 'E9003'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        if hint is None:
            hint = (
                "Valid error types are: RunTimeError, IllegalOperationError, "
                "DivisionByZeroError, IndexOutOfBoundsError, NameError, ArgumentError, "
                "TypeError, AttributeError, DictKeyError, ValueError, ModuleError, "
                "StackDepthExceededError."
            )
        super().__init__(pos_start, pos_end, details, context, hint)
        self.error_name = "InvalidErrorTypeError"


class DictKeyError(RunTimeError):
    """
    [E7003] Error raised when a dictionary key is not found.
    """
    error_code = 'E7003'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        if hint is None:
            hint = "Check whether the key exists before accessing it."
        super().__init__(pos_start, pos_end, details, context, hint)
        self.error_name = "DictKeyError"


class ValueError(RunTimeError):
    """
    [E9005] Error for invalid values.
    """
    error_code = 'E9005'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        super().__init__(pos_start, pos_end, details, context, hint)
        self.error_name = "ValueError"


class TypeError(RunTimeError):
    """
    [E4001] Error for performing an operation on an inappropriate type.
    Example: calling an attribute that is not a method, like my_obj.age()
    """
    error_code = 'E4001'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        super().__init__(pos_start, pos_end, details, context, hint)
        self.error_name = "TypeError"


class AttributeError(RunTimeError):
    """
    [E7002] Error for accessing a non-existent attribute or method on an object.
    Example: my_obj.fake_property
    """
    error_code = 'E7002'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        super().__init__(pos_start, pos_end, details, context, hint)
        self.error_name = "AttributeError"


class ModuleError(RunTimeError):
    """
    [E8001] Error raised when a module cannot be found or a name inside a module
    cannot be resolved.
    Example: summon nonexistent_module
             summon foo from mymodule  # but 'foo' is not defined in mymodule
    """
    error_code = 'E8001'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        super().__init__(pos_start, pos_end, details, context, hint)
        self.error_name = "ModuleError"


class StackDepthExceededError(RunTimeError):
    """
    [E9002] Error raised when the runtime recursion depth exceeds the maximum allowed limit.
    """
    error_code = 'E9002'

    def __init__(self, pos_start, pos_end, details, context, hint=None):
        if hint is None:
            hint = (
                "This usually means a function is calling itself infinitely. "
                "Check your recursive functions for a proper base case."
            )
        super().__init__(pos_start, pos_end, details, context, hint)
        self.error_name = "StackDepthExceededError"