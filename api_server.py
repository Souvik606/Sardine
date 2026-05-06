"""
SARDS Backend API Server

A Flask-based REST API that exposes the Sardine interpreter for remote code execution.
The API provides endpoints to execute Sardine code and retrieve results.

Usage:
    python api_server.py

The server will start on http://localhost:8000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from sards import (
    Lexer,
    Parser,
    Interpreter,
    Context,
    SymbolTable,
    Number,
    BuiltInFunction,
)

app = Flask(__name__)
CORS(app)

# Initialize global symbol table with built-in functions
global_symbol_table = SymbolTable()
global_symbol_table.set("None", Number(0))
global_symbol_table.set("True", Number(1))
global_symbol_table.set("False", Number(0))
global_symbol_table.set("show", BuiltInFunction.show)
global_symbol_table.set("listen", BuiltInFunction.listen)
global_symbol_table.set("Integer", BuiltInFunction.Integer)
global_symbol_table.set("String", BuiltInFunction.String)
global_symbol_table.set("typeof", BuiltInFunction.typeof)


def execute_sardine_code(code: str) -> tuple[str, str | None]:
    """
    Execute Sardine code and capture output.
    
    Args:
        code: The Sardine code to execute
        
    Returns:
        A tuple of (output, error)
        - output: The program output (empty string if no output)
        - error: Error message (None if no error)
    """
    try:
        # Tokenize using enumerate_tokens
        lexer = Lexer("<stdin>", code)
        tokens, error = lexer.enumerate_tokens()
        
        if error:
            return "", str(error)
        
        # Parse
        parser = Parser(tokens)
        syntax_tree = parser.parse()
        
        if syntax_tree.error:
            return "", str(syntax_tree.error)
        
        # Interpret with output capture
        interpreter = Interpreter()
        context = Context('<program>')
        context.symbol_table = global_symbol_table
        
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        with redirect_stdout(output_buffer):
            with redirect_stderr(error_buffer):
                result = interpreter.visit(syntax_tree.node, context)
        
        output = output_buffer.getvalue()
        stderr_output = error_buffer.getvalue()
        
        # Check if result has an error
        if hasattr(result, 'error') and result.error:
            error_msg = str(result.error)
            if stderr_output:
                error_msg += f"\n{stderr_output}"
            return output, error_msg
        
        # Get the actual value from result
        result_value = result.value if hasattr(result, 'value') else result
        
        # If result is not None, add it to output
        if result_value is not None:
            if output:
                output += f"\n{result_value}"
            else:
                output = str(result_value)
        
        return output, None
        
    except Exception as e:
        return "", f"Internal Error: {str(e)}"


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify API is running."""
    return jsonify({"status": "ok", "message": "SARDS API is running"}), 200


@app.route("/api/execute", methods=["POST"])
def execute():
    """
    Execute Sardine code and return the result.
    
    Request JSON:
    {
        "code": "sardine code to execute"
    }
    
    Response JSON:
    {
        "output": "execution output",
        "error": null or "error message"
    }
    
    Status Codes:
    - 200: Successful execution (with or without errors in the result)
    - 400: Bad request (missing code field)
    - 500: Internal server error
    """
    try:
        data = request.get_json()
        
        if not data or "code" not in data:
            return (
                jsonify({"output": "", "error": "Missing 'code' field in request"}),
                400,
            )
        
        code = data["code"]
        
        if not isinstance(code, str):
            return (
                jsonify({"output": "", "error": "'code' must be a string"}),
                400,
            )
        
        if not code.strip():
            return jsonify({"output": "", "error": "Code cannot be empty"}), 400
        
        # Execute the code
        output, error = execute_sardine_code(code)
        
        return (
            jsonify({"output": output, "error": error}),
            200,
        )
        
    except Exception as e:
        return (
            jsonify({"output": "", "error": f"Server error: {str(e)}"}),
            500,
        )


@app.route("/", methods=["GET"])
def root():
    """Root endpoint with API information."""
    return jsonify(
        {
            "name": "SARDS Backend API",
            "version": "1.0.0",
            "description": "REST API for executing Sardine code",
            "endpoints": {
                "POST /api/execute": "Execute Sardine code",
                "GET /health": "Health check",
                "GET /": "API information",
            },
            "docs": "See BACKEND_API.md in project folder",
        }
    ), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    print("Starting SARDS Backend API Server...")
    print("Server running on http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print("\nEndpoints:")
    print("  GET  /              - API information")
    print("  GET  /health        - Health check")
    print("  POST /api/execute   - Execute Sardine code")
    print("\nExample:")
    print('  curl -X POST http://localhost:8000/api/execute \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"code": "show 1 + 2"}\'')
    print()
    
    app.run(host="0.0.0.0", port=8000, debug=False)
