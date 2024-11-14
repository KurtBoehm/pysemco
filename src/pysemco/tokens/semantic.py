from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..lsp import LanguageServer
    from multilspy.lsp_protocol_handler.lsp_types import (
        SemanticTokens as LspSemanticTokens,
    )

from .defs import SemanticToken


def parse_semantic_tokens(
    semantic_tokens: "LspSemanticTokens",
    token_types: list[str],
    token_modifiers: list[str],
):
    """Convert the semantic tokens provided by an LSP to pysemco’s tokens."""

    tokens = semantic_tokens["data"]
    assert len(tokens) % 5 == 0
    prev: SemanticToken | None = None
    trans = []
    for i in range(0, len(tokens), 5):
        delta_line, delta_start, length, token_type, token_mods_bf = tokens[i : i + 5]
        token_type = token_types[token_type]
        token_mods: list[str] = [
            token_modifiers[bit]
            for bit in range(token_mods_bf.bit_length())
            if token_mods_bf & (1 << bit)
        ]

        if prev is None:
            val = SemanticToken(
                delta_line,
                delta_start,
                length,
                token_type,
                token_mods,
            )
        elif delta_line == 0:
            val = SemanticToken(
                prev.line,
                prev.start + delta_start,
                length,
                token_type,
                token_mods,
            )
        else:
            val = SemanticToken(
                prev.line + delta_line,
                delta_start,
                length,
                token_type,
                token_mods,
            )
        prev = val
        trans.append(val)

    return trans


async def semantic_tokens(
    lsp: "LanguageServer",
    file: Path,
    contents: str | None = None,
):
    """Compute and convert semantic tokens for the given file using the given LSP."""

    async with lsp.start_server():
        raw_tokens = await lsp.semantic_tokens(file, contents)
        assert raw_tokens is not None

        resp = getattr(lsp, "init_response", None)
        assert resp is not None
        legend = resp["capabilities"]["semanticTokensProvider"]["legend"]  # type: ignore

        return parse_semantic_tokens(
            raw_tokens,
            legend["tokenTypes"],
            legend["tokenModifiers"],
        )
