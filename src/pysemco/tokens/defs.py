from os import PathLike
from typing import Any, final

StrPath = str | PathLike[str]


@final
class SemanticToken:
    """The information contained in an LSP semantic token.

    Here, the information is stored directly without fancy encoding.
    Note: Changing `start` also changes `end` because `length` remains unchanged.
    """

    def __init__(
        self,
        line: int,
        start: int,
        length: int,
        token_type: str,
        token_modifiers: list[str],
    ):
        self.line = line
        self.start = start
        self.length = length
        self.token_type = token_type
        self.token_modifiers = token_modifiers

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
        return SemanticToken(
            line=self.line,
            start=self.start,
            length=self.length,
            token_type=t,
            token_modifiers=self.token_modifiers,
        )

    @staticmethod
    def from_json(json: dict[str, Any]) -> "SemanticToken":
        return SemanticToken(**json)

    @property
    def json(self):
        return self.__dict__


@final
class SemanticTokens:
    """A list of semantic tokens together with the corresponding code."""

    def __init__(self, txt: str, toks: list[SemanticToken]):
        self.txt = txt
        self.toks = toks

    @staticmethod
    def from_json(json: dict[str, Any]) -> "SemanticTokens":
        return SemanticTokens(
            txt=json["txt"],
            toks=[SemanticToken.from_json(t) for t in json["toks"]],
        )

    @property
    def json(self):
        return {"txt": self.txt, "toks": [t.json for t in self.toks]}


def combine_tokens(toks: list[SemanticToken]) -> list[SemanticToken]:
    """Merge adjacent tokens with the same type and modifiers."""
    out: list[SemanticToken] = [toks[0]]
    for tok in toks[1:]:
        last = out[-1]
        if (
            last.token_type == tok.token_type
            and last.token_modifiers == tok.token_modifiers
            and last.line == tok.line
            and last.end == tok.start
        ):
            out[-1].length += tok.length
            continue
        out.append(tok)
    return out
