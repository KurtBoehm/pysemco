from os import PathLike
from pathlib import Path

from .combine import combine_tokens
from .defs import SemanticTokens, StrPath
from .semantic import semantic_tokens


def compute_tokens_cpp(
    root: StrPath,
    file: StrPath,
    txt: str | None = None,
) -> SemanticTokens:
    """Compute C++ tokens by combining clangd’s and pygments’ tokens.

    Args:
        root: The root directory of the workspace of the project.
        file: The path of the C++ file.
        txt: The contents of `file`, which can be provided to avoid file I/O.
    """
    import asyncio

    from multilspy.language_server import MultilspyLogger

    from ..lsp.clangd import ClangdServer
    from .pygments import pygments_tokens

    if txt is None:
        with open(file, "r") as f:
            txt = f.read()

    root = Path(root).resolve()
    file = Path(file).resolve()

    tokens_clangd = asyncio.run(
        semantic_tokens(ClangdServer(MultilspyLogger(), root), file, txt)
    )
    tokens_pygments = pygments_tokens("cpp", txt)
    return combine_tokens(tokens_clangd, tokens_pygments)


def compute_tokens_python(
    root: StrPath,
    file: StrPath,
    txt: str | None = None,
) -> SemanticTokens:
    """Compute Python tokens by combining my pyright fork’s and pygments’ tokens.

    Args:
        root: The root directory of the workspace of the project.
        file: The path of the C++ file.
        txt: The contents of `file`, which can be provided to avoid file I/O.
    """
    import asyncio

    from multilspy.language_server import MultilspyLogger

    from ..lsp.pyright import PyrightServer
    from .pygments import pygments_tokens

    if txt is None:
        with open(file, "r") as f:
            txt = f.read()

    root = Path(root).resolve()
    file = Path(file).resolve()

    tokens_pyright = asyncio.run(
        semantic_tokens(PyrightServer(MultilspyLogger(), root), file, txt)
    )
    tokens_pygments = pygments_tokens("python", txt)
    return combine_tokens(tokens_pyright, tokens_pygments)


def compute_tokens(
    lang: str,
    root: StrPath,
    file: StrPath,
    txt: str | None = None,
) -> SemanticTokens:
    """Compute tokens for the given language using appropriate methods.

    Args:
        lang: The language used.
        root: The root directory of the workspace of the project.
        file: The path of the C++ file.
        txt: The contents of `file`, which can be provided to avoid file I/O.
    """
    from .pygments import pygments_tokens

    match lang:
        case "cpp":
            return compute_tokens_cpp(root, file, txt)
        case "python":
            return compute_tokens_python(root, file, txt)
        case "nasm":
            if txt is None:
                with open(file, "r") as f:
                    txt = f.read()
            return pygments_tokens(lang, txt)
        case _:
            raise Exception(f"Unsupported language {lang!r}!")


def compute_minimal_tokens(lang: str, txt: str):
    """Compute minimal tokens using pygments.

    Args:
        lang: The language used.
        txt: The code to be analyzed.
    """
    from .pygments import pygments_tokens

    return pygments_tokens(lang, txt)
