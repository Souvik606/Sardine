"""
Module: Position and Error Tracking

This module provides utility classes for tracking the position of characters in an input text
and handling errors encountered during tokenization or parsing.

Classes:
- Position: Maintains the current position in the input text, including index, line, and column.
- Error: Serves as a base class for error handling, storing details about errors that occur.
- IllegalCharError: A specific error subclass for handling illegal character occurrences.
- InvalidSyntaxError: A specific error subclass for handling invalid syntax occurrences.
- RunTimeError: Handles runtime errors encountered during execution.
"""


class Position:
    """
    Tracks the current position in the input text, including index, line, and column.

    Attributes:
    - index (int): The current character index in the input text.
    - line (int): The current line number in the input text.
    - col (int): The current column number in the input text.
    - file_name (str): The name of the file being processed.
    - file_text (str): The full content of the file being processed.
    """

    def __init__(self, index, line, col, file_name, file_text):
        """
        Initializes a Position instance.

        Parameters:
        - index (int): The character index in the input text.
        - line (int): The line number in the input text.
        - col (int): The column number in the input text.
        - file_name (str): The name of the file being processed.
        - file_text (str): The full content of the file.
        """
        self.index = index
        self.line = line
        self.col = col
        self.file_name = file_name
        self.file_text = file_text

    def advance(self, current_char=None):
        """
        Moves the position forward by one character.

        If the character is a newline ('\n'), it increments the line number
        and resets the column number. Otherwise, it simply increments the column number.

        Parameters:
        - current_char (str, optional): The character currently being processed.

        Returns:
        - Position: The updated position object.
        """
        self.index += 1
        self.col += 1
        if current_char == '\n' or current_char == ';':
            self.line += 1
            self.col = 0
        return self

    def copy(self):
        """
        Creates and returns a copy of the current position.

        Returns:
        - Position: A new instance of Position with the same values.
        """
        return Position(self.index, self.line, self.col, self.file_name, self.file_text)


class Error: # pylint: disable=too-few-public-methods
    """
    Represents a general error encountered during tokenization or parsing.

    Attributes:
    - pos_start (Position): The starting position of the error.
    - pos_end (Position): The ending position of the error.
    - error_name (str): The name/type of the error.
    - details (str): Additional details about the error.
    """

    def __init__(self, pos_start, pos_end, error_name, details):
        """
        Initializes an Error instance.

        Parameters:
        - pos_start (Position): The starting position of the error.
        - pos_end (Position): The ending position of the error.
        - error_name (str): A description of the error type.
        - details (str): Additional information about the error.
        """
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def to_string(self):
        """
        Formats and returns the error message.

        Returns:
        - str: A formatted error message containing the error name, details,
               and file location information.
        """
        return (
            f"{self.error_name}: {self.details}\n"
            f"File {self.pos_start.file_name}, line {self.pos_start.line + 1}"
        )

class IllegalCharError(Error): # pylint: disable=too-few-public-methods
    """
    Handles errors caused by illegal characters in the input text.

    Inherits from:
    - Error
    """

    def __init__(self, pos_start, pos_end, details=''):
        """
        Initializes an IllegalCharError instance.

        Parameters:
        - pos_start (Position): The starting position of the illegal character.
        - pos_end (Position): The ending position of the illegal character.
        - details (str, optional): Additional information about the error. Defaults
            to an empty string.
        """
        super().__init__(pos_start, pos_end, 'Illegal Character', details)

class IllegalOperationError(Error): # pylint: disable=too-few-public-methods
    """
    Handles errors caused by illegal operations.

    Inherits from:
    - Error
    """

    def __init__(self, pos_start, pos_end, details=''):
        """
        Initializes an IllegalOperationError instance.

        Parameters:
        - pos_start (Position): The starting position of the illegal operation.
        - pos_end (Position): The ending position of the illegal operation.
        - details (str, optional): Additional information about the error. Defaults
            to an empty string.
        """
        super().__init__(pos_start, pos_end, 'Illegal Operation', details)
        
class ExpectedCharError(Error): # pylint: disable=too-few-public-methods
    """
    Handles errors caused by absence of expected characters in the input text.

    Inherits from:
    - Error
    """

    def __init__(self,pos_start,pos_end,details):
        super().__init__(pos_start,pos_end,'Expected Character',details)

class InvalidSyntaxError(Error): # pylint: disable=too-few-public-methods
    """
    Handles errors caused by invalid syntax in the input text.

    Inherits from:
    - Error
    """

    def __init__(self, pos_start, pos_end, details=''):
        """
        Initializes an InvalidSyntaxError instance.

        Parameters:
        - pos_start (Position): The starting position of the syntax error.
        - pos_end (Position): The ending position of the syntax error.
        - details (str, optional): Additional information about the error.
                                    Defaults to an empty string.
        """
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)


class RunTimeError(Error):
    """
    Represents an error encountered during the execution phase.

    Attributes:
    - context (Context): The execution context where the error occurred.

    Inherits from:
    - Error
    """

    def __init__(self, pos_start, pos_end, details, context):
        """
        Initializes a RunTimeError instance.

        Parameters:
        - pos_start (Position): The starting position of the runtime error.
        - pos_end (Position): The ending position of the runtime error.
        - details (str): A description of the runtime error.
        - context (Context): The execution context where the error occurred.
        """
        super().__init__(pos_start, pos_end, 'Run Time Error', details)
        self.context = context

    def to_string(self):
        """
        Returns a formatted traceback of the runtime error.

        Returns:
        - str: A string representing the traceback of the error.
        """
        return self.generate_traceback()

    def generate_traceback(self):
        """
        Generates a traceback for the runtime error, showing where it occurred in the program.

        Returns:
        - str: A formatted string containing the error traceback.
        """
        result = ''
        position = self.pos_start
        context = self.context

        while context:
            result = (
                f"{self.error_name}: {self.details}\n"
                f"File {position.file_name}, line {position.line + 1}, "
                f"in {context.display_name}\n"
            )

            position = context.parent_entry_pos
            context = context.parent

        return 'Traceback (most recent call last):\n' + result