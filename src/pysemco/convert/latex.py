from ..tokens import SemanticToken, SemanticTokens


def _texify(txt: str, space: bool) -> str:
    """Convert single-line text into a LaTeX-friendly variant.

    Args:
        txt:
            The text to convert into a LaTeX-friendly form.
        space:
            Whether to replace spaces with a SemCo-specific macro.
            Keeping spaces (`False`) allows for line wrapping.
    """

    mapping = {
        "\\": "\\SemCoBackSlash{}",
        "{": "\\{",
        "}": "\\}",
        "#": "\\#",
        "_": "\\_",
        "&": "\\&",
        "%": "\\%",
        '"': "\\textquotedbl{}",
        "'": "\\textquotesingle{}",
        "~": "\\textasciitilde{}",
        "(": "(\\allowbreak{}",
        "<": "\\textless{}",
        ">": "\\textgreater{}",
    }
    if space:
        mapping[" "] = "\\SemCoSpace{}"
    output = ""
    for i, c in enumerate(txt):
        if c == "(" and i + 1 < len(txt) and txt[i + 1] == ")":
            output += c
        else:
            output += mapping.get(c, c)
    return output


def latex_token(txt: str, token_type: str, space: bool = True) -> str:
    """Convert the given token into the LaTeX SemCo token.

    Args:
        txt: The text of the token.
        token_type: The type of the token as used by SemCo.
        space: Whether to replace spaces with a SemCo-specific macro.
    """

    return f"\\SemCoFormat{{{token_type}}}{{{_texify(txt, space)}}}"


def to_latex(tokens: SemanticTokens, space: bool = True) -> list[str]:
    """Convert the given code with corresponding tokens into LaTeX SemCo macros.

    Args:
        tokens: The tokens used for formatting the code.
        space: Whether to replace spaces with a SemCo-specific macro.
    """

    lines = tokens.txt.splitlines()
    latex_lines: list[str] = []
    for i, line in enumerate(lines):
        ts = [x for x in tokens.toks if x.line == i]
        if len(ts) == 0:
            # If there are no tokens in this line, add it without formatting.
            latex_line = f"{_texify(line, space)}"
        else:
            latex_line = ""
            prev: SemanticToken | None = None
            for t in ts:
                prefix = line[prev.end if prev is not None else 0 : t.start]
                latex_line += _texify(prefix, space)
                latex_line += latex_token(line[t.start : t.end], t.token_type)
                prev = t
            assert prev is not None
            latex_line += _texify(line[prev.end :], space)
        if len(latex_line) == 0:
            latex_line = "\\ "
        latex_lines.append(latex_line)
    return latex_lines


def latex_line_merge(lines: list[str]) -> str:
    r"""Merge LaTeX lines using \\\\."""
    return "\n".join(
        f"{l}\\\\" if i + 1 < len(lines) else f"{l}%" for i, l in enumerate(lines)
    )
