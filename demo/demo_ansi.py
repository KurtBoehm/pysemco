from pathlib import Path

from pysemco import ansi_style_colorful, compute_tokens_sync, to_ansi

snippets = Path(__file__).parent / "snippets"

code = """\
def a[T](l: list[T]) -> T: return l[0]
b = a([1, 2.5])
"""

toks = compute_tokens_sync("python", "", "", code)
print(to_ansi(toks, ansi_style_colorful))
print("-" * 45)

toks = compute_tokens_sync("python", snippets, "demo.py")
print(to_ansi(toks, ansi_style_colorful))
print("-" * 45)

toks = compute_tokens_sync("cpp", snippets, "demo.cpp")
print(to_ansi(toks, ansi_style_colorful))
