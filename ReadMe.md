# `pysemco`: Source Code Tokenization using LSPs and Pygments

`pysemco` provides tools to tokenize source code in C++, Python, and x86-64 assembly in Intel syntax using Pygments for basic tokens together with `clangd` (C++) or a patched version of Pyright (Python) for semantic tokens.
The language servers are downloaded and updated automatically upon their use.

For example, the program
```python
from pysemco import compute_tokens

code = """\
def a[T](l: list[T]) -> T: return l[0]
b = a([1, 2.5])
"""
for t in compute_tokens("python", "", "", code):
    print(t)
```

generates the following output if Pyright has already been cached:

```
pyright is up to date!
SemanticToken(line=0, start=0, length=3, token_type='keyword', token_modifiers=[])
SemanticToken(line=0, start=4, length=1, token_type='function', token_modifiers=[])
SemanticToken(line=0, start=6, length=1, token_type='typeParameter', token_modifiers=[])
SemanticToken(line=0, start=9, length=1, token_type='parameter', token_modifiers=[])
SemanticToken(line=0, start=12, length=4, token_type='class', token_modifiers=[])
SemanticToken(line=0, start=17, length=1, token_type='typeParameter', token_modifiers=[])
SemanticToken(line=0, start=24, length=1, token_type='typeParameter', token_modifiers=[])
SemanticToken(line=0, start=27, length=6, token_type='keyword', token_modifiers=[])
SemanticToken(line=0, start=34, length=1, token_type='parameter', token_modifiers=[])
SemanticToken(line=0, start=36, length=1, token_type='literal-int', token_modifiers=[])
SemanticToken(line=1, start=0, length=1, token_type='variable', token_modifiers=[])
SemanticToken(line=1, start=4, length=1, token_type='function', token_modifiers=[])
SemanticToken(line=1, start=7, length=1, token_type='literal-int', token_modifiers=[])
SemanticToken(line=1, start=10, length=3, token_type='literal-float', token_modifiers=[])
```

The only executable provided by `pysemco` is `pysemco_tex`, which can be used to highlight code in LaTeX.
A test file is contained in `demo/demo.tex` with the LaTeX definitions that run `pysemco_tex` in `demo/SemanticCode.sty`.
This code has been tested with `pdflatex` and `lualatex`, but needs to be compiled from the root of the project for the paths to work.
