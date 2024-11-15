from pathlib import Path

from .combine import combine_tokens
from .defs import SemanticTokens, StrPath
from .semantic import semantic_tokens


async def compute_tokens_cpp(
    root: StrPath,
    file: StrPath,
    txt: str | None = None,
    log_lsp: bool = False,
) -> SemanticTokens:
    """Compute C++ tokens by combining clangd’s and pygments’ tokens.

    Args:
        root: The root directory of the workspace of the project.
        file: The path of the C++ file relative to root (or absolute).
        txt: The contents of `file`, which can be provided to avoid file I/O.
    """
    from multilspy.language_server import MultilspyLogger

    from ..lsp.clangd import ClangdServer
    from .pygments import pygments_tokens

    root = Path(root).resolve()
    file = (root / file).resolve()

    if txt is None:
        with open(file, "r") as f:
            txt = f.read()

    tokens_clangd = await semantic_tokens(
        ClangdServer(MultilspyLogger(), root, log_lsp=log_lsp),
        file,
        txt,
    )

    # Special case: clangd represents non-type template parameters
    # as `typeParameter` with the `readonly` modifier
    tokens_clangd = [
        (
            t.with_token_type("parameter")
            if t.token_type == "typeParameter" and "readonly" in t.token_modifiers
            else t
        )
        for t in tokens_clangd
    ]

    tokens_pygments = pygments_tokens("cpp", txt)
    return SemanticTokens(txt, combine_tokens(tokens_clangd, tokens_pygments))


async def compute_tokens_python(
    root: StrPath,
    file: StrPath,
    txt: str | None = None,
    log_lsp: bool = False,
) -> SemanticTokens:
    """Compute Python tokens by combining my pyright fork’s and pygments’ tokens.

    Args:
        root: The root directory of the workspace of the project.
        file: The path of the Python file relative to root (or absolute).
        txt: The contents of `file`, which can be provided to avoid file I/O.
    """
    from multilspy.language_server import MultilspyLogger

    from ..lsp.pyright import PyrightServer
    from .pygments import pygments_tokens

    root = Path(root).resolve()
    file = (root / file).resolve()

    if txt is None:
        with open(file, "r") as f:
            txt = f.read()

    tokens_pyright = await semantic_tokens(
        PyrightServer(MultilspyLogger(), root, log_lsp=log_lsp), file, txt
    )
    tokens_pygments = pygments_tokens("python", txt)
    return SemanticTokens(txt, combine_tokens(tokens_pyright, tokens_pygments))


async def compute_tokens(
    lang: str,
    root: StrPath,
    file: StrPath,
    txt: str | None = None,
    log_lsp: bool = False,
) -> SemanticTokens:
    """Compute tokens for the given language using appropriate methods.

    Args:
        lang: The language used.
        root: The root directory of the workspace of the project.
        file: The path of the source file relative to root (or absolute).
        txt: The contents of `file`, which can be provided to avoid file I/O.
    """
    from .pygments import pygments_tokens

    match lang:
        case "cpp":
            return await compute_tokens_cpp(root, file, txt, log_lsp=log_lsp)
        case "python":
            return await compute_tokens_python(root, file, txt, log_lsp=log_lsp)
        case "nasm":
            if txt is None:
                with open(Path(root) / file, "r") as f:
                    txt = f.read()
            return SemanticTokens(txt, pygments_tokens(lang, txt))
        case _:
            raise Exception(f"Unsupported language {lang!r}!")


def compute_tokens_sync(
    lang: str,
    root: StrPath,
    file: StrPath,
    txt: str | None = None,
    log_lsp: bool = False,
) -> SemanticTokens:
    import asyncio

    return asyncio.run(compute_tokens(lang, root, file, txt, log_lsp=log_lsp))


def compute_minimal_tokens(lang: str, txt: str):
    """Compute minimal tokens using pygments.

    Args:
        lang: The language used.
        txt: The code to be analyzed.
    """
    from .pygments import pygments_tokens

    return pygments_tokens(lang, txt)
