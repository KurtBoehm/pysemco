from pysemco.convert.colors import StyleDict, colorful

from ..tokens import SemanticToken, SemanticTokens


def _code_to_chars(code: int):
    return f"\033[{code}m"


# Approximates the “colorful” color scheme using basic ANSI colors
# See http://en.wikipedia.org/wiki/ANSI_escape_code for the codes
ansi_style_colorful = colorful(
    StyleDict(
        red=_code_to_chars(31),  # red
        green=_code_to_chars(32),  # green
        light_blue=_code_to_chars(36),  # cyan
        dark_blue=_code_to_chars(34),  # blue
        grey=_code_to_chars(90),  # bright black
        indigo=_code_to_chars(94),  # bright blue
        orange=_code_to_chars(33),  # yellow
        pink=_code_to_chars(95),  # bright magenta
        purple=_code_to_chars(35),  # magenta
        italic=_code_to_chars(3),
        bold=_code_to_chars(1),
    )
)
_reset_all = _code_to_chars(0)


def to_ansi(
    tokens: SemanticTokens,
    token_style: dict[str, str],
) -> str:
    """Convert the tokenized code into an ANSI-styled string.

    Args:
        tokens: The semantic tokens.
        token_style: A style to highlight the tokens with.
    """

    lines = tokens.txt.splitlines()
    ansi_lines: list[str] = []
    for i, line in enumerate(lines):
        ts = [x for x in tokens.toks if x.line == i]
        if len(ts) == 0:
            # If there are no tokens in this line, add it without formatting.
            ansi_line = line
        else:
            ansi_line = ""
            prev: SemanticToken | None = None
            for t in ts:
                prefix = line[prev.end if prev is not None else 0 : t.start]
                ansi_line += prefix

                style = token_style.get(t.token_type)
                tok = line[t.start : t.end]
                ansi_line += f"{style}{tok}{_reset_all}" if style is not None else tok

                prev = t
            assert prev is not None
            ansi_line += line[prev.end :]
        ansi_lines.append(ansi_line)
    return "\n".join(ansi_lines)
