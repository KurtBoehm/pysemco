from colorama import Fore
from colorama.ansi import Style, code_to_chars

from pysemco.convert.colors import StyleDict, colorful

from ..tokens import SemanticToken, SemanticTokens

# Approximates the “colorful” color scheme using basic ANSI colors
ansi_style_colorful = colorful(
    StyleDict(
        red=Fore.RED,
        green=Fore.GREEN,
        light_blue=Fore.CYAN,
        dark_blue=Fore.BLUE,
        grey=Fore.LIGHTBLACK_EX,
        indigo=Fore.LIGHTBLUE_EX,
        orange=Fore.YELLOW,
        pink=Fore.LIGHTMAGENTA_EX,
        purple=Fore.MAGENTA,
        italic=code_to_chars(3),
        bold=code_to_chars(1),
    )
)


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
                ansi_line += (
                    f"{style}{tok}{Style.RESET_ALL}" if style is not None else tok
                )

                prev = t
            assert prev is not None
            ansi_line += line[prev.end :]
        ansi_lines.append(ansi_line)
    return "\n".join(ansi_lines)
