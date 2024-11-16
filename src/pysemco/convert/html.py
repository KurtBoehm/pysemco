from html import escape

from pysemco.convert.colors import StyleDict, colorful

from ..tokens import SemanticToken, SemanticTokens

# The “colorful” color scheme as used in SemanticCode.
html_style_google = colorful(
    StyleDict(
        red="color:#EA4335;",  # GoogleRed
        green="color:#319243;",  # GoogleGreen!50!MaterialGreen800
        light_blue="color:#1976D2;",  # MaterialBlue700
        dark_blue="color:#0D47A1;",  # MaterialBlue900
        grey="color:#757575;",  # MaterialGrey600
        indigo="color:#3F51B5;",  # MaterialIndigo
        orange="color:#EF6C00;",  # MaterialOrange800
        pink="color:#E91E63;",  # MaterialPink
        purple="color:#673AB7;",  # MaterialDeepPurple
        italic="font-style:italic;",
        bold="font-weight:bold;",
    )
)


def to_html(
    tokens: SemanticTokens,
    token_style: dict[str, str],
) -> list[str]:
    """Convert the tokenized code into HTML with each line as a separate string.

    Args:
        tokens: The semantic tokens.
        token_style: A style to highlight the tokens with.
    """

    lines = tokens.txt.splitlines()
    html_lines: list[str] = []
    for i, line in enumerate(lines):
        ts = [x for x in tokens.toks if x.line == i]
        if len(ts) == 0:
            # If there are no tokens in this line, add it without formatting.
            html_line = escape(line, quote=False)
        else:
            html_line = ""
            prev: SemanticToken | None = None
            for t in ts:
                prefix = line[prev.end if prev is not None else 0 : t.start]
                html_line += escape(prefix, quote=False)

                style = token_style.get(t.token_type)
                tok = escape(line[t.start : t.end], quote=False)
                html_line += (
                    f'<span style="{style}">{tok}</span>' if style is not None else tok
                )

                prev = t
            assert prev is not None
            html_line += escape(line[prev.end :], quote=False)
        html_lines.append(html_line)
    return html_lines


def html_div(lines: list[str]) -> str:
    """Join HTML lines into a monospaced <div> with <br/> between the lines."""
    return (
        '<div style="font-family:monospace;white-space: pre;">'
        + "<br/>".join(lines)
        + "</div>"
    )


class HtmlDisplay:
    def __init__(
        self,
        tokens: SemanticTokens,
        token_style: dict[str, str],
    ) -> None:
        self.tokens = tokens
        self.token_style = token_style

    def __repr__(self) -> str:
        return f"HtmlDisplay(tokens={self.tokens!r}, token_style={self.token_style!r})"

    def _repr_html_(self) -> str:
        return html_div(to_html(self.tokens, self.token_style))
