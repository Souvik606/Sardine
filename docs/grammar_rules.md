# Grammar Documentation

This document describes the grammar for the programming language **SARDS**, outlining its syntax rules, operator
precedence, and usage examples.

## Table of Contents

- [Grammar Documentation](#grammar-documentation)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Grammar Rules](#grammar-rules)
  - [Operator Precedence](#operator-precedence)
  - [Usage Examples](#usage-examples)

## Overview

This grammar defines a language that supports:

- **Expressions:** Including arithmetic and logical operations.
- **Statements:** Such as assignments, optionally prefixed with a declaration keyword.
- **Control Flow Constructs:** Like conditionals (`if`/`elif`/`else`), loops (`while`/`for`), branch instructions (`switch`) and function definitions.
- **Compound Constructs:** Including function calls, list expressions, and jump statements for control flow.

## Grammar Rules

Below is the complete grammar definition:

```grammar
multiline: NEWLINE* (singleline) (NEWLINE* (singleline))* NEWLINE*

singleline: expression |statements|if-expression | for-expression | while-expression |switch-statement| function-definition

jump-statements:KEYWORD:yield expression|KEYWORD:proceed | KEYWORD:escape

statements: IDENTIFIER (LPAREN3 expression RPAREN3)* (COMMA IDENTIFIER (LPAREN3 expression RPAREN3)*)* (EQUAL | PLUSEQUAL | MINUSEQUAL | MULEQUAL | DIVEQUAL | MODEQUAL | FLOOREQUAL) expression (COMMA expression)*

switch-statement: KEYWORD:menu ternary-expression LPAREN2 NEWLINE* (case-statement* NEWLINE*)* default-statement? NEWLINE* (case_statement* NEWLINE*)* RPAREN2

case-statement: KEYWORD:choice ternary-expression LPAREN2 ((expression|statements) RPAREN2)| (NEWLINE multiline RPAREN2)

default-statement: KEYWORD:fallback LPAREN2 ((expression|statements) RPAREN2)| (NEWLINE multiline RPAREN2)

expression: jump_statements | ternary-expression 

ternary-expression: (logical-expression|statements) (QUESTION ternary-expression COLON ternary-expression)*

logical-expression: comp-expression ((KEYWORD:AND | KEYWORD:OR) comp-expression)*

comp-expression: KEYWORD:NOT comp-expression | arith-expression ((EE | NEQ | LT | GT | LTE | GTE) arith-expression)*

arith-expression: term ((PLUS | MINUS) term)*

term: unary ((MUL | DIV | MOD | FLOOR) unary)*

unary: (PLUS | MINUS) unary | exponent

exponent: factor (EXP unary)*

factor: INT | FLOAT | STRING | IDENTIFIER (ARROW expression)* | LPAREN expression RPAREN |index| list-expression| function-call

function-call: IDENTIFIER LPAREN (expression(COMMA expression)*)? RPAREN

list-expression: LPAREN3 (expression(COMMA expression)*)? RPAREN3

while-expression: KEYWORD:whenever expression LPAREN2 ((expression|statements) RPAREN2)| (NEWLINE multiline RPAREN2)

for-expression: KEYWORD:Cycle IDENTIFIER EQUAL expression COLON expression (COLON:expression)?LPAREN2 ((expression|statements)RPAREN2)| (NEWLINE multiline RPAREN2)

function-definition: KEYWORD:method IDENTIFIER?LPAREN (IDENTIFIER (COMMA IDENTIFIER)*)? RPAREN LPAREN2 ((expression|statements)RPAREN2)| (NEWLINE multiline RPAREN2)

if-expression: KEYWORD:when expression LPAREN2 ((expression|statements) RPAREN2 (elif-expression|else-expression)?) | (NEWLINE multiline RPAREN2 NEWLINE*(elif-expression|else-expression))

elif-expression: KEYWORD:orwhen expression LPAREN2 ((expression|statements) RPAREN2 (elif-expression|else-expression)?) | (NEWLINE multiline RPAREN2 NEWLINE*(elif-expression|else-expression))

else-expression: KEYWORD:otherwise LPAREN2 (((expression|statements)RPAREN2)|NEWLINE multiline RPAREN2)
```

## Operator Precedence

The grammar enforces standard operator precedence:

1. **Parentheses (`()`):**  
   Expressions within parentheses are evaluated first.
2. **Exponentiation (`**`):**  
   Evaluated before multiplication and division, with right-to-left associativity.
3. **Unary Operators (`+`, `-`):**  
   Applied directly to the following factor.
4. **Multiplication, Division, Modulus and Floor Division (`*`, `/`, `%`, `//`):**  
   Processed in the `term` rule.
5. **Addition and Subtraction (`+`, `-`):**  
   Evaluated in the `arith-expression` rule, with left-to-right associativity.

**Examples:**

- `3 + 4 * 2` is parsed as `3 + (4 * 2)`.
- `-5 + (6 / 2) * 3` applies the unary operator to `5`, then computes `(6 / 2)`, multiplies the result by `3`, and
  finally adds `-5`.
- `(3 + 4) * 2` forces the addition to occur before the multiplication.

## Usage Examples

Here are some valid expressions and statements according to this grammar:

- **Arithmetic Expression:**
  ```plaintext
  3 + 5 - 2
  ```
- **Multiplication/Division:**
  ```plaintext
  3 * 4 / 2
  ```
- **Combined Expression:**
  ```plaintext
  -5 + (6 / 2) * 3
  ```
- **Function Call:**
  ```plaintext
  myFunction(3, 4 + 2)
  ```
- **Conditional Expression (Simplified):**
  ```plaintext
  when condition ( doSomething() )
  multiline block...
  ```
