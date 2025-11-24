# `pysemco`: Source Code Tokenization using LSPs and Pygments

`pysemco` provides tools to tokenize source code in C++, Python, and x86-64 assembly in Intel syntax using Pygments for basic tokens together with `clangd` (C++) or `basedpyright` (Python) for semantic tokens.
The language servers are downloaded and updated automatically upon their use.

Currently, there are three converters into different formats, each with a demo in the `demo` subfolder:
- LaTeX: The demo in `demo.tex` and the definitions in `SemanticCode.sty` (a variant of the file found in [`latex-packages`](https://github.com/KurtBoehm/latex-packages)) are based on `pysemco_tex`, `pysemco`’s only executable.
  This code has been tested with `pdflatex` and `lualatex`, but needs to be compiled from the root of the project for the paths to work.
- HTML: Used for `display` output in the Jupyter notebook `demo.ipynb`.
- ANSI escape codes: Used in `demo_ansi.py`.
