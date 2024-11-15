from html import escape

from .defs import SemanticToken, SemanticTokens

_red = "color:#EA4335;"  # GoogleRed
_green = "color:#319243;"  # GoogleGreen!50!MaterialGreen800
_light_blue = "color:#1976D2;"  # MaterialBlue700
_dark_blue = "color:#0D47A1;"  # MaterialBlue900
_grey = "color:#757575;"  # MaterialGrey600
_indigo = "color:#3F51B5;"  # MaterialIndigo
_orange = "color:#EF6C00;"  # MaterialOrange800
_pink = "color:#E91E63;"  # MaterialPink
_purple = "color:#673AB7;"  # MaterialDeepPurple

_italic = "font-style:italic;"
_bold = "font-weight:bold;"

html_style_google = {
    "attribute": _light_blue,
    "builtin-variable": _orange,
    "class": _purple,
    "comment": _grey,
    "concept": _indigo,
    "decorator": _light_blue,
    "enum": _purple,
    "enumMember": _dark_blue,
    "function": _green,
    "keyword": _red,
    "keyword-fun": _green,
    "keyword-type": _purple,
    "keyword-value": _dark_blue,
    "label": _light_blue,
    "literal-affix": _red,
    "literal-character": _dark_blue,
    "literal-float": _dark_blue,
    "literal-include": _dark_blue,
    "literal-int": _dark_blue,
    "literal-string": _dark_blue,
    "macro": _light_blue,
    "method": _italic + _green,
    "namespace": _pink,
    "parameter": _bold + _orange,
    "preprocessor": _red,
    "property": _italic + _orange,
    "type": _purple,
    "typeParameter": _bold + _purple,
    "variable": _orange,
}


def to_html(
    tokens: SemanticTokens,
    token_style: dict[str, str],
) -> list[str]:
    """Convert the given code with corresponding tokens into HTML.

    Args:
        txt:
            The code to be converted.
        tokens:
            The tokens used for formatting the code.
    """

    lines = tokens.txt.splitlines()
    latex_lines: list[str] = []
    for i, line in enumerate(lines):
        ts = [x for x in tokens.toks if x.line == i]
        if len(ts) == 0:
            # If there are no tokens in this line, add it without formatting.
            latex_line = escape(line, quote=False)
        else:
            latex_line = ""
            prev: SemanticToken | None = None
            for t in ts:
                prefix = line[prev.end if prev is not None else 0 : t.start]
                latex_line += escape(prefix, quote=False)

                style = token_style.get(t.token_type)
                tok = escape(line[t.start : t.end], quote=False)
                latex_line += (
                    f'<span style="{style}">{tok}</span>' if style is not None else tok
                )

                prev = t
            assert prev is not None
            latex_line += escape(line[prev.end :], quote=False)
        latex_lines.append(latex_line)
    return latex_lines


def html_div(lines: list[str]) -> str:
    return f'<div style="font-family:monospace;white-space: pre;">{"<br/>".join(lines)}</div>'


class HtmlDisplay:
    def __init__(
        self,
        tokens: SemanticTokens,
        token_style: dict[str, str],
    ) -> None:
        self.content = html_div(to_html(tokens, token_style))

    def _repr_html_(self) -> str:
        return self.content
