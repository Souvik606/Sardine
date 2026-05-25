"""
Module: shell

This module serves as the entry point for executing the lexer and parser.
It provides an interactive Read-Eval-Print Loop (REPL) where users can input
mathematical expressions, which are then tokenized, parsed, and displayed
as an Abstract Syntax Tree (AST).

## Overview:
1. **Lexical Analysis (Lexer)**:
   - Converts the input text into a sequence of tokens.
   - Identifies numbers, operators, and parentheses.
   - Returns a list of tokens or an error if invalid characters are found.

2. **Parsing (Parser)**:
   - Converts the tokenized input into a structured AST.
   - Follows defined grammar rules for mathematical expressions.
   - Returns a valid AST or a syntax error.

3. **Interactive Execution (REPL)**:
   - Repeatedly asks for user input.
   - Displays either the parsed AST or an error message.

"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sards import *

global_symbol_table = SymbolTable()
global_symbol_table.set("None", Number(0))
global_symbol_table.set("True", Number(1))
global_symbol_table.set("False", Number(0))

global_symbol_table.set("show", BuiltInFunction.show)
global_symbol_table.set("listen", BuiltInFunction.listen)
global_symbol_table.set("Integer", BuiltInFunction.Integer)
global_symbol_table.set("String", BuiltInFunction.String)
global_symbol_table.set("type", BuiltInFunction.type)
global_symbol_table.set("super", BuiltInFunction.super)
global_symbol_table.set("is_a", BuiltInFunction.is_a)


def run(filename, input_text):
    """
    Executes the lexer and parser on the given input expression.

    This function first tokenizes the input text using the Lexer. If successful,
    the token list is passed to the Parser, which constructs an Abstract Syntax Tree (AST).
    Any errors encountered during tokenization or parsing are returned.

    Parameters:
    - filename (str): The name of the source file (used for error reporting).
    - text (str): The mathematical expression to be analyzed.

    Returns:
    - tuple:
        - AST (Abstract Syntax Tree): The parsed representation of the expression.
        - Error (if any): Provides details of any encountered errors.

    Example Usage:
    --------------
    ast, error = run('<stdin>', '3 + 4 * (2 - 1)')
    if error:
        print(error.to_string())
    else:
        print(ast)
    """
    lexer = Lexer(filename, input_text)  # Initialize the Lexer with the input text
    tokens, error = lexer.enumerate_tokens()

    # If lexical analysis encounters an error, return it
    if error:
        return None, error

    # For debugging lexer's output
    # print(tokens)

    # Pass the tokens to the parser
    parser = Parser(tokens)
    syntax_tree = parser.parse()# Generate AST

    # Return the parsed AST and any errors encountered
    if syntax_tree.error:
        return None, syntax_tree.error


    # For debugging parser's output
    # print(syntax_tree.node)

    interpreter = Interpreter()
    context = Context('<program>')
    context.symbol_table = global_symbol_table
    # Store the directory of the source file so 'summon' can find sibling modules
    context.source_dir = os.path.dirname(os.path.abspath(filename)) if filename != '<stdin>' else os.getcwd()
    res = interpreter.visit(syntax_tree.node, context)

    return res.value, res.error

def run_file(filepath):
    """
    Reads and executes code from a file.
    
    Parameters:
    - filepath (str): Path to the code file to execute.
    
    Returns:
    - None: Prints results or errors directly.
    """
        # Check if file exists
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return

    # Read the file content
    with open(filepath, 'r', encoding='utf-8') as file:
        file_content = file.read()

    # Execute the file content
    result, errors = run(filepath, file_content)

    # Print errors if encountered, otherwise display the result
    if errors:
        relative_path = os.path.relpath(filepath, start=os.curdir).replace('\\', '/')
        print(f"Error in {relative_path}:")
        print(errors.to_string())
    # else:
    #     if result is not None:
    #         print(result)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        choice = input('Enter 0 for REPL mode and 1 for file input: ')
        if choice == '0':
            # REPL (Read-Eval-Print Loop) for continuous user interaction
            while True:
                try:
                    text = input('code > ') # Prompt user for an expression
                    if text.lower() in ['exit', 'quit']:
                        print("Goodbye!")
                        break
                    result, errors = run('<stdin>', text)

                    # Print errors if encountered, otherwise display the AST
                    if errors:
                        print(errors.to_string())
                    else:
                        print(result)
                except KeyboardInterrupt:
                    print("\nGoodbye!")
                    break
                except EOFError:
                    print("\nGoodbye!")
                    break
        else:
            run_file('sards/samples/main.sad')
