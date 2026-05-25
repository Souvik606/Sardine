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
multiline: NEWLINE* (singleline)* (NEWLINE* (singleline))* NEWLINE*

singleline: call | statements | if-expression | for-expression | while-expression | switch-statement | function-definition | exception-handling | class-definition | foreach-expression

class-definition: KEYWORD:model IDENTIFIER (COLON IDENTIFIER (COMMA IDENTIFIER)*)? LPAREN2 NEWLINE* (class-member NEWLINE*)* RPAREN2

class-member: attr-declaration | constructor-definition | method-definition

attr-declaration: (KEYWORD:open | KEYWORD:guarded | KEYWORD:secret)? KEYWORD:attr LT attr-list GT

attr-list: attr-item (COMMA attr-item)*

attr-item: IDENTIFIER (EQUAL expression)?

method-definition: (KEYWORD:open | KEYWORD:guarded | KEYWORD:secret)? KEYWORD:method IDENTIFIER? LPAREN (param-list)? RPAREN LPAREN2 (multiline |jump-statements)* RPAREN2

constructor-definition: KEYWORD:init LPAREN (param-list)? RPAREN LPAREN2 NEWLINE* (initializer-list)? (multiline | jump-statements)* NEWLINE* RPAREN2

initializer-list: initializer-item ((COMMA NEWLINE* | NEWLINE+) initializer-item)*

initializer-item: IDENTIFIER COLON expression

jump-statements: KEYWORD:proceed | KEYWORD:escape | KEYWORD:yield (expression NEWLINE* (COMMA NEWLINE* expression NEWLINE*)*)?

statements: call (COMMA call)* (EQUAL | PLUSEQUAL | MINUSEQUAL | MULEQUAL | DIVEQUAL | MODEQUAL | FLOOREQUAL | EXPEQUAL) expression (COMMA expression)*

switch-statement: KEYWORD:menu ternary-expression LPAREN2 NEWLINE* (case-statement* NEWLINE*)* default-statement? NEWLINE* (case-statement* NEWLINE*)* RPAREN2

case-statement: KEYWORD:choice ternary-expression LPAREN2 NEWLINE* (multiline | jump-statements)* RPAREN2

KEYWORD:fallback LPAREN2 NEWLINE* (multiline | jump-statements)* RPAREN2

param-list: param-item (COMMA param-item)*

param-item: IDENTIFIER (EQUAL expression)?

expression: ternary-expression

ternary-expression: (logical-expression | statements) (QUESTION ternary-expression COLON ternary-expression)*

logical-expression: bitwise-expression ((KEYWORD:AND | KEYWORD:OR) bitwise-expression)*

bitwise-expression: bitwise-xor (BITOR bitwise-xor)*

bitwise-xor: bitwise-and (BITXOR bitwise-and)*

bitwise-and: comp-expression (BITAND comp-expression)*

comp-expression: KEYWORD:NOT comp-expression | shift-expression ((EE | NEQ | LT | GT | LTE | GTE) shift-expression)*

shift-expression: arith-expression ((LSHIFT | RSHIFT) arith-expression)*

arith-expression: term ((PLUS | MINUS) term)*

term: unary ((MUL | DIV | MOD | FLOOR) unary)*

unary: (PLUS | MINUS | BITNOT) unary | exponent

exponent: call (EXP unary)*

argument-list: positional-list (COMMA keyword-list)? | keyword-list

positional-list: expression (COMMA expression)*

keyword-list: keyword-item (COMMA keyword-item)*

keyword-item: IDENTIFIER EQUAL expression

call: factor ( (LPAREN (argument-list)? RPAREN) | (DOT IDENTIFIER) | (LPAREN3 expression RPAREN3) )*

factor: INT | FLOAT | STRING | IDENTIFIER (LPAREN3 expression RPAREN3)* | LPAREN expression RPAREN | list-expression | dict-expression | anonymous-func-expr

dict-expression: LPAREN2 NEWLINE* (dict-entry (NEWLINE* COMMA NEWLINE* dict-entry)*)? NEWLINE* RPAREN2

dict-entry: expression NEWLINE* COLON NEWLINE* expression

list-expression: LPAREN3 NEWLINE* (expression(NEWLINE* COMMA NEWLINE* expression)*)? RPAREN3

exception-handling: try-expression NEWLINE* ( catch-expression NEWLINE* (catch-expression)* NEWLINE* finally-expression? | finally-expression)

try-expression: KEYWORD:risk LPAREN2 (multiline | jump-statements)* RPAREN2

catch-expression: KEYWORD:trap (ERROR (IDENTIFIER)?)? LPAREN2 (multiline | jump-statements)* RPAREN2

finally-expression: KEYWORD:clean LPAREN2 (multiline | jump-statements)* RPAREN2

while-expression: KEYWORD:whenever expression LPAREN2 (multiline | jump-statements)* RPAREN2

for-expression: KEYWORD:Cycle IDENTIFIER EQUAL expression COLON expression (COLON expression)? LPAREN2 (multiline | jump-statements)* RPAREN2

foreach-expression:KEYWORD:trace IDENTIFIER (COMMA IDENTIFIER)* LARROW expression NEWLINE* LPAREN2 (multiline | jump-statements)* RPAREN2

function-definition: KEYWORD:method IDENTIFIER LPAREN (param-list)? RPAREN LPAREN2 (multiline |jump-statements)* RPAREN2

anonymous-func-expr: KEYWORD:method LPAREN (param-list)? RPAREN LPAREN2 (multiline |jump-statements)* RPAREN2

if-expression: KEYWORD:when expression LPAREN2 (multiline | jump-statements)* RPAREN2 NEWLINE* (elif-expression | else-expression)?

elif-expression: KEYWORD:orwhen expression LPAREN2 (multiline | jump-statements)* RPAREN2 NEWLINE* (elif-expression |else-expression)?

else-expression: KEYWORD:otherwise LPAREN2 (multiline | jump-statements)* RPAREN2
```

## Operator Precedence

The grammar enforces standard operator precedence:

1. **Parentheses (`()`):**  
   Expressions within parentheses are evaluated first.
2. **Exponentiation (`**`):\*\*  
   Evaluated before multiplication and division, with right-to-left associativity.
3. **Unary Operators (`+`, `-`):**  
   Applied directly to the following factor.
4. **Multiplication, Division, Modulus and Floor Division (`*`, `/`, `%`, `//`):**  
   Processed in the `term` rule.
5. **Addition and Subtraction (`+`, `-`):**  
   Evaluated in the `arith-expression` rule, with left-to-right associativity.
6. **Bitwise AND** (`&`)
7. **Bitwise XOR** (`^`)
8. **Bitwise OR** (`|`)

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

---

## Operator Overloading

```grammar
operator-method: KEYWORD:method IDENTIFIER LPAREN (param-list)? RPAREN LPAREN2 (multiline | jump-statements)* RPAREN2

# IDENTIFIER must be one of the reserved operator method names listed below.
```

> **Note:** Operator methods follow the same method-definition rules as ordinary methods.
> Access modifiers (`open`, `guarded`, `secret`) are allowed but `open` is recommended.

### Special Method Names

#### Binary Operators (take one parameter `other`)

| Operator | Method name    | Example use |
| -------- | -------------- | ----------- |
| `+`      | `__add__`      | `a + b`     |
| `-`      | `__sub__`      | `a - b`     |
| `*`      | `__mul__`      | `a * b`     |
| `/`      | `__div__`      | `a / b`     |
| `%`      | `__mod__`      | `a % b`     |
| `//`     | `__floordiv__` | `a // b`    |
| `**`     | `__pow__`      | `a ** b`    |
| `&`      | `__and__`      | `a & b`     |
| `\|`     | `__or__`       | `a \| b`    |
| `^`      | `__xor__`      | `a ^ b`     |
| `<<`     | `__lshift__`   | `a << b`    |
| `>>`     | `__rshift__`   | `a >> b`    |
| `==`     | `__eq__`       | `a == b`    |
| `!=`     | `__neq__`      | `a != b`    |
| `<`      | `__lt__`       | `a < b`     |
| `<=`     | `__lte__`      | `a <= b`    |
| `>`      | `__gt__`       | `a > b`     |
| `>=`     | `__gte__`      | `a >= b`    |
| `and`    | `__land__`     | `a and b`   |
| `or`     | `__lor__`      | `a or b`    |

#### Unary Operators (take no parameters)

| Operator | Method name  | Example use |
| -------- | ------------ | ----------- |
| `-`      | `__neg__`    | `-a`        |
| `not`    | `__not__`    | `not a`     |
| `~`      | `__bitnot__` | `~a`        |

### Error Messages

If an operator method is **not** defined, Sardine raises an `IllegalOperationError` with a
helpful hint:

```
IllegalOperationError: Operator '+' is not defined for 'MyModel'.
Define 'method __add__(other) {...}' inside the model to enable it.
```

### Rules and Caveats

1. Operator methods **must use `yield`** to return a value, just like regular methods.
2. The returned value can be **any Sardine type** — a new instance, a `Number`, a `String`, etc.
3. Augmented assignment (`+=`, `-=`, …) reuses the same binary operator method:  
   `a += b` is equivalent to `a = a + b`, so `__add__` is called.
4. Unary minus (`-a`) internally calls `__neg__` if defined; otherwise it falls back to `__mul__`
   with `Number(-1)` (which would require `__mul__`).
5. Operator methods **do not need to be `open`**; any access level is respected.
