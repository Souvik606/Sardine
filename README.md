<div align="center">
  <img src="media/v0.3d-cropped.png" alt="Sardine Logo" style="padding:10px" width="200">
  <br>
</div>

# Sardine: A Custom Language Made with Python

> [!IMPORTANT]
> **Active Development has Migrated to C++**
> This repository contains the **Python prototype** of the Sardine programming language. While this implementation is fully functional for study and local experimentation, the production-grade, high-performance execution engine has transitioned to a native C++23 backend.
>
> **Visit the main repository here: [github.com/sadsardines/sardine](https://github.com/sadsardines/sardine)**

[![Sardine Tests](https://github.com/sadsardines/sardine-py/actions/workflows/tests.yml/badge.svg)](https://github.com/sadsardines/sardine-py/actions/workflows/tests.yml)

Sardine is a custom programming language built with Python. It combines a powerful **Lexer**,
**Parser**, and **Interpreter** to process and execute code written in our bespoke language. In
addition, Sardine offers an **Interactive Shell** for real-time coding.

---

## Features

- **Interactive Shell**: A REPL to write, inspect, and execute Sardine code interactively.
- **File Input Programs**: Currently can run code in `sards/samples/main.sad`. Multiple file executability planned.
- **Full Language Parser/Interpreter**: Includes a tokenizer, parser, AST builder, and interpreter for language elements such as **if/else**, **while**, **for**, **switch-case**, **functions**, **classes**, and **exceptions**.
- **Python-native Architecture**: Built in pure Python for easy learning, maintenance, and extensibility.
- **Stable Testable Core**: Modular separation of lexer, parser, AST, and interpreter makes unit testing and feature expansion straightforward.
- **Pluggable Extensions**: Designed for future language features, custom data types, and more complex control flow via clear node and token abstractions.
- **Developer-Friendly**: Includes meaningful error messaging and a concise shell workflow for experimentation.

## Prerequisites

- [Python](https://www.python.org/) (v3.10 or higher)
- [Git](https://git-scm.com/)

---

## Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/sadsardines/sardine-py.git
   cd sardine-py
   ```

2. **Run the Interactive Shell:**

   ```bash
   python -m sards.shell
   ```

3. **Run the Shell in REPL Mode:**

   Enter `0` when prompted by the Shell and explore the Sardine language on the fly.

4. **Run a Sardine program:**

   Edit `sards/samples/main.sad` to your intended Sardine language program, run the Shell, and enter `1` to run File Input mode when prompted.

---

## Language Details

- Dynamically typed variables
- Default data types of Integer, Float, String, List, Dictionary
- Arithmetic, Bitwise and Logical operators
- Nestable, heterogeneous Lists and Dictionaries with List and Dictionary functions
- User-defined functions with recursion
- Object-oriented Programming (`model` structure)
- Error Handling (`risk-trap-clean` structure)
- For Loops (`Cycle`)
- While Loops (`whenever`)
- Switch-Case (`menu`)
- If-Else-Elif (`when-orwhen-otherwise`)

Please view [docs/grammar_rules.md](docs/grammar_rules.md) for details on all grammar rules. User manual for more friendly explanation of syntax is under construction.

---

## Evolution to C++ (Main Repository)

As this prototype matured, the project transitioned to a native C++23 implementation to achieve robust performance and native speed. The C++ version is the active development main branch and introduces:
*   **Performance Improvements**: Compiles and executes directly on a C++ native backend or inside web browsers via WebAssembly.
*   **Pratt Parsing**: Leverages top-down operator precedence (Pratt parsing) for robust grammatical handling.
*   **Rich Control Flows**: Enhanced loop iterations (`cycle`, `during`, `trace`) and pattern-matching `menu` blocks.
*   **Self-Hosted Standard Library**: Custom modules like `math.sad`, `linalg.sad`, and `csv.sad` written in Sardine itself.

If you are looking for the main production-ready project, please head over to the [sadsardines/sardine C++ repository](https://github.com/sadsardines/sardine).

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) to get started.
