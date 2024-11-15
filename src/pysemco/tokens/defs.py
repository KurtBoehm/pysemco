from dataclasses import dataclass, replace
from os import PathLike

StrPath = str | PathLike[str]


@dataclass
class SemanticToken:
    """The information contained in an LSP semantic token.

    Here, the information is stored directly without fancy encoding.
    Note: Changing `start` also changes `end` because `length` remains unchanged.
    """

    line: int
    start: int
    length: int
    token_type: str
    token_modifiers: list[str]

    @property
    def end(self):
        return self.start + self.length

    @end.setter
    def end(self, value: int):
        self.length = value - self.start

    def from_lines(self, lines: list[str]) -> str:
        return lines[self.line][self.start : self.start + self.length]

    def limited(self, start: int, end: int) -> "SemanticToken":
        start = max(self.start, start)
        length = min(self.end, end) - start
        assert length >= 0
        return SemanticToken(
            self.line,
            start,
            length,
            self.token_type,
            self.token_modifiers,
        )

    def with_token_type(self, t: str):
        return replace(self, token_type=t)


@dataclass
class SemanticTokens:
    txt: str
    toks: list[SemanticToken]


def combine_tokens(toks: list[SemanticToken]) -> list[SemanticToken]:
    """Merge adjacent tokens with the same type and modifiers."""
    out: list[SemanticToken] = []
    for tok in toks:
        if (
            len(out) > 0
            and out[-1].token_type == tok.token_type
            and out[-1].token_modifiers == tok.token_modifiers
            and out[-1].end == tok.start
        ):
            out[-1].length += tok.length
            continue
        out.append(tok)
    return out
