from copy import deepcopy

from .defs import SemanticToken


def combine_tokens(
    primary: list[SemanticToken],
    secondary: list[SemanticToken],
) -> list[SemanticToken]:
    """Merge two lists of tokens.

    The implementation gives preference to the primary list if tokens overlap and
    assumes that either list does not contain overlapping tokens.

    Args:
        primary: The primary tokens.
        secondary: The secondary tokens.
    """

    # Merge the two lists and sort the tokens lexicographically according to
    # (line, starting column, ending column).
    # Each token is paired with a Boolean denoting whether it is from the primary list,
    # later called its “kind”.
    comb = sorted(
        [(tok, True) for tok in deepcopy(primary)]
        + [(tok, False) for tok in deepcopy(secondary)],
        key=lambda v: (v[0].line, v[0].start, v[0].end),
    )
    out = [comb.pop(0)]
    for tok, tokkind in comb:
        # Get the preceding token and its kind.
        lasttok, lastkind = out[-1]

        if tok == lasttok:
            # Skip duplicate tokens.
            continue
        if tok.line != lasttok.line or tok.start >= lasttok.end:
            # If the token is on a new line or starts after the preceding token, keep it.
            out.append((tok, tokkind))
            continue

        # If two tokens overlap, they are assumed to be from different lists.
        # This does not seem to work with basedpyright, so this check is skipped
        # assert tokkind != lastkind
        if (
            tok.token_type == lasttok.token_type
            and tok.token_modifiers == lasttok.token_modifiers
        ):
            # If the overlapping tokens are of the same type, extend the existing token.
            lasttok.end = max(tok.end, lasttok.end)
            continue

        if tokkind:
            # If the new token is from the primary list, cut off the tail
            # of the preceding token and remove it if nothing remains.
            lasttok.end = tok.start
            if lasttok.length == 0:
                out.pop()
        else:
            # If the new token is from the secondary list, cut off its head
            # and ignore it if nothing remains.
            end = tok.end
            tok.start = lasttok.end
            tok.end = end
            if tok.length == 0:
                continue
        # Add the new token.
        out.append((tok, tokkind))

    # Drop the token kinds for the output.
    return [t for t, _ in out]
