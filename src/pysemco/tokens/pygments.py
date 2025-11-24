import re
from typing import Callable, Final, final, override

import pygments.token as token
from pygments import lex
from pygments.lexer import LexerMeta, RegexLexer, bygroups, include, inherit, words
from pygments.lexers import find_lexer_class_by_name
from pygments.lexers.c_cpp import CppLexer as _CppLexer
from pygments.lexers.python import PythonLexer as _PythonLexer

from .defs import SemanticToken, combine_tokens


TokenType = token._TokenType  # pyright: ignore[reportPrivateUsage]
_is_token_subtype: Callable[[TokenType, TokenType], bool] = token.is_token_subtype


@final
class NasmLexer(RegexLexer):
    """A nasm lexer based on pygments.lexers.asm.NasmLexer."""

    identifier = r"[a-z$._?][\w$.?#@~]*"
    hexn = r"(?:0x[0-9a-f]+|$0[0-9a-f]*|[0-9]+[0-9a-f]*h)"
    octn = r"[0-7]+q"
    binn = r"[01]+b"
    decn = r"[0-9]+"
    floatn = decn + r"\.e?" + decn
    string = r'"(\\"|[^"\n])*"|' + r"'(\\'|[^'\n])*'|" + r"`(\\`|[^`\n])*`"
    declkw = r"(?:res|d)[bwdqt]|times"
    register = (
        r"(r[0-9][0-5]?[bwd]?|"
        r"[a-d][lh]|[er]?[a-d]x|[er]?[sb]p|[er]?[sd]i|[c-gs]s|st[0-7]|"
        r"mm[0-7]|cr[0-4]|dr[0-367]|tr[3-7]|k[0-7]|"
        r"[xyz]mm(?:[12][0-9]?|3[01]?|[04-9]))\b"
    )
    wordop = r"seg|wrt|strict|rel|abs"
    # Support SIMD addresses, too
    type = r"(([xyz]mmword|[dq]?word|byte) ptr)|byte|[dq]?word"
    # Directives must be followed by whitespace, otherwise CPU will match
    # cpuid for instance.
    directives = (
        r"(?:BITS|USE16|USE32|SECTION|SEGMENT|ABSOLUTE|EXTERN|GLOBAL|"
        r"ORG|ALIGN|STRUC|ENDSTRUC|COMMON|CPU|GROUP|UPPERCASE|IMPORT|"
        r"EXPORT|LIBRARY|MODULE)(?=\s)"
    )
    # Add broadcasts
    broadcasts = r"(?<=\{)1to(2|4|8|16)(?=\})"

    flags = re.IGNORECASE | re.MULTILINE
    tokens = {
        "root": [
            (r"^\s*%", token.Comment.Preproc, "preproc"),
            include("whitespace"),
            # Allow anything before a colon to be a label
            (r".*:", token.Name.Label),
            (
                rf"({identifier})(\s+)(equ)",
                bygroups(
                    token.Name.Constant, token.Whitespace, token.Keyword.Declaration
                ),
                "instruction-args",
            ),
            (directives, token.Keyword, "instruction-args"),
            (declkw, token.Keyword.Declaration, "instruction-args"),
            (identifier, token.Name.Function, "instruction-args"),
            (r"[\r\n]+", token.Whitespace),
        ],
        "instruction-args": [
            (broadcasts, token.Name.Attribute),
            (string, token.String),
            (hexn, token.Number.Hex),
            (octn, token.Number.Oct),
            (binn, token.Number.Bin),
            (floatn, token.Number.Float),
            (decn, token.Number.Integer),
            include("punctuation"),
            # Name.Builtin → Name.Variable
            (register, token.Name.Variable),
            (identifier, token.Name.Variable),
            (r"[\r\n]+", token.Whitespace, "#pop"),
            include("whitespace"),
        ],
        "preproc": [
            (r"[^;\n]+", token.Comment.Preproc),
            (r";.*?\n", token.Comment.Single, "#pop"),
            (r"\n", token.Comment.Preproc, "#pop"),
        ],
        "whitespace": [
            (r"\n", token.Whitespace),
            (r"[ \t]+", token.Whitespace),
            (r";.*", token.Comment.Single),
            (r"#.*", token.Comment.Single),
        ],
        "punctuation": [
            (r"[,{}():\[\]]+", token.Punctuation),
            (r"[&|^<>+*/%~-]+", token.Operator),
            (r"[$]+", token.Keyword.Constant),
            (wordop, token.Operator.Word),
            (type, token.Keyword.Type),
        ],
    }

    @override
    def get_tokens(self, text: str, unfiltered: bool = False):
        """Fix up labels in the existing tokens."""
        # Store all labels without the terminating colon
        labels: set[str] = set()
        for tkind, tstr in super().get_tokens(text, unfiltered):
            if tkind is token.Name.Label:
                labels.add(tstr.rstrip(":"))
        for tkind, tstr in super().get_tokens(text, unfiltered):
            # Remove the colon from labels
            if tkind is token.Name.Label:
                yield token.Name.Label, tstr[:-1]
                yield token.Punctuation, ":"
                continue
            # Mark any use of a label as a Name.Label.
            if tstr in labels:
                tkind = token.Name.Label
            yield tkind, tstr


class CppLexer(_CppLexer):
    _keyword_kinds: Final = {
        "auto": token.Keyword.Type,
        "bool": token.Keyword.Type,
        "char": token.Keyword.Type,
        "char8_t": token.Keyword.Type,
        "char16_t": token.Keyword.Type,
        "char32_t": token.Keyword.Type,
        "double": token.Keyword.Type,
        "float": token.Keyword.Type,
        "int": token.Keyword.Type,
        "long": token.Keyword.Type,
        "short": token.Keyword.Type,
        "signed": token.Keyword.Type,
        "unsigned": token.Keyword.Type,
        "void": token.Keyword.Type,
        "wchar_t": token.Keyword.Type,
        "false": token.Keyword.Constant,
        "true": token.Keyword.Constant,
        "nullptr": token.Keyword.Constant,
        "this": token.Keyword.Constant,
        "operator": token.Keyword.Operator,
    }
    _builtin_kinds: Final = {
        "false": token.Keyword.Constant,
        "true": token.Keyword.Constant,
        "NULL": token.Name.Macro,
    }

    @override
    def get_tokens(self, text: str, unfiltered: bool = False):
        """Replace the `Keyword` token kind with a more specific sub-kind."""
        for ttype, tstr in super().get_tokens(text, unfiltered):
            if ttype is token.Keyword:
                yield CppLexer._keyword_kinds.get(tstr, ttype), tstr
            elif ttype is token.Name.Builtin:
                yield CppLexer._builtin_kinds.get(tstr, ttype), tstr
            else:
                yield ttype, tstr


class CppAlgLexer(CppLexer):
    tokens: Final = {
        "keywords": [
            inherit,
            (words(("parallel", "process"), suffix=r"\b"), token.Keyword),
        ],
    }

    @override
    def get_tokens(self, text: str, unfiltered: bool = False):
        """Replace the `Keyword` token kind with a more specific sub-kind."""
        for ttype, tstr in super().get_tokens(text, unfiltered):
            if ttype is token.Keyword:
                yield CppLexer._keyword_kinds.get(tstr, ttype), tstr
            elif ttype is token.Name.Builtin:
                yield CppLexer._builtin_kinds.get(tstr, ttype), tstr
            else:
                yield ttype, tstr


class PythonLexer(_PythonLexer):
    @override
    def get_tokens(self, text: str, unfiltered: bool = False):
        """Replace the `Keyword` token kind with a more specific sub-kind."""
        for ttype, tstr in super().get_tokens(text, unfiltered):
            if ttype is token.Operator.Word:
                yield token.Keyword, tstr
            else:
                yield ttype, tstr


def _get_lexer(lang: str) -> LexerMeta:
    """Get the lexer for the given language using the custom ones for C++ and nasm."""
    if lang == "cpp":
        return CppLexer
    if lang == "cppalg":
        return CppAlgLexer
    if lang == "nasm":
        return NasmLexer
    if lang == "python":
        return PythonLexer
    return find_lexer_class_by_name(lang)


def pygments_tokens(
    lang: str,
    txt: str,
    name_map: dict[str, str] | None = None,
) -> list[SemanticToken]:
    """Determine the tokens for the given code in the given language using pygments."""

    if name_map is None:
        name_map = {}

    def addtok(kind: str):
        toks.append(SemanticToken(line, col, len(tokstr), kind, []))

    lexer = _get_lexer(lang)

    toks: list[SemanticToken] = []
    curtxt = ""
    for tok, tokstr in lex(txt, lexer()):
        lines = curtxt.split("\n")
        line, col = max(len(lines) - 1, 0), len(lines[-1])
        curtxt += tokstr

        if (
            _is_token_subtype(tok, token.Name)
            and (t := name_map.get(tokstr)) is not None
        ):
            addtok(t)
            continue
        if _is_token_subtype(tok, token.Name.Attribute):
            addtok("attribute")
            continue
        if _is_token_subtype(tok, token.Name.Function):
            addtok("function")
            continue
        if _is_token_subtype(tok, token.Name.Variable):
            addtok("variable")
            continue
        if _is_token_subtype(tok, token.Name.Label):
            addtok("label")
            continue
        if _is_token_subtype(tok, token.Name.Macro):
            addtok("macro")
            continue
        if _is_token_subtype(tok, token.Comment.Preproc):
            addtok("preprocessor")
            continue
        if _is_token_subtype(tok, token.Comment.PreprocFile):
            addtok("literal-include")
            continue
        if _is_token_subtype(tok, token.Comment):
            addtok("comment")
            continue
        if _is_token_subtype(tok, token.Keyword.Type):
            addtok("keyword-type")
            continue
        if _is_token_subtype(tok, token.Keyword.Constant):
            addtok("keyword-value")
            continue
        if _is_token_subtype(tok, token.Keyword.Operator):
            addtok("keyword-fun")
            continue
        if _is_token_subtype(tok, token.Keyword):
            addtok("keyword")
            continue
        if _is_token_subtype(tok, token.Name.Namespace):
            addtok("namespace")
            continue
        if _is_token_subtype(tok, token.Name.Decorator):
            addtok("decorator")
            continue
        if any(
            _is_token_subtype(tok, k)
            for k in (
                token.Literal.Number.Bin,
                token.Literal.Number.Hex,
                token.Literal.Number.Integer,
            )
        ):
            addtok("literal-int")
            continue
        if _is_token_subtype(tok, token.Literal.Number.Float):
            addtok("literal-float")
            continue
        if _is_token_subtype(tok, token.Literal.String.Affix):
            addtok("literal-affix")
            continue
        if _is_token_subtype(tok, token.Literal.String.Interpol):
            continue
        if _is_token_subtype(tok, token.Literal.String):
            addtok("literal-string")
            continue
        if any(
            _is_token_subtype(tok, k)
            for k in (
                token.Text,
                token.Punctuation,
                token.Other,
                token.Operator,
                token.Name,
            )
        ):
            continue

        raise Exception(f"{tok} {tokstr!r}")
    return combine_tokens(toks)
