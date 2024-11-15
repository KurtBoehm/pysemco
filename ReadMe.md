# `pysemco`: Source Code Tokenization using LSPs and Pygments

`pysemco` provides tools to tokenize source code in C++, Python, and x86-64 assembly in Intel syntax using Pygments for basic tokens together with `clangd` (C++) or a patched version of Pyright (Python) for semantic tokens.
The language servers are downloaded and updated automatically upon their use.

An example for using the library to generate tokens, as well as the HTML output functionality, is contained in `demo/demo.ipynb`.

The only executable provided by `pysemco` is `pysemco_tex`, which can be used to highlight code in LaTeX.
A test file is contained in `demo/demo.tex` with the LaTeX definitions that run `pysemco_tex` in `demo/SemanticCode.sty`.
This code has been tested with `pdflatex` and `lualatex`, but needs to be compiled from the root of the project for the paths to work.
