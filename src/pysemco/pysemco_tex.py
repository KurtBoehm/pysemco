import json
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, replace
from pathlib import Path
from typing import NamedTuple

from .serialization import deserialize, serialize
from .tokens import (
    SemanticTokens,
    compute_minimal_tokens,
    compute_tokens,
    latex_line_merge,
    to_latex,
)


@dataclass
class TokenInfo:
    """The output of the analysis together with the source code that was analyzed.

    `txt` can be used to check whether the analysis is applicable to a given file.

    Attributes:
        txt:
            The source code to which the `tokens` correspond to.
        tokens:
            The tokens corresponding to `txt`.
    """

    txt: str
    tokens: SemanticTokens


def convert_params(params_str: str) -> dict[str, int | str]:
    def convert_value(v: str):
        try:
            return int(v)
        except ValueError:
            return v

    if params_str == "":
        return {}
    params = {k: v for k, v in (p.split("=") for p in params_str.split(","))}
    return {k: convert_value(v) for k, v in params.items()}


def run_analyze(args: Namespace):
    root: Path = args.root_path.resolve()
    src: Path = args.in_path.resolve()
    dst: Path = args.out_path.resolve()

    def save_tokens(txt: str | None = None):
        if args.clear_cache:
            for p in dst.parent.iterdir():
                if p.suffix == ".tex" or p.name == ".cache":
                    p.unlink()

        if txt is None:
            with open(src, "r") as f:
                txt = f.read()

        tokens = compute_tokens(args.language, root, src, txt)
        info = TokenInfo(txt, tokens)
        with open(dst, "w") as f:
            json.dump(serialize(info), f)

    if dst.exists():
        with open(src, "r") as f:
            txt = f.read()
        with open(dst, "r") as f:
            info = deserialize(json.load(f), TokenInfo)
        if txt != info.txt:
            save_tokens(txt)
    else:
        save_tokens()


def run_texify(args: Namespace):
    with open(args.in_path, "r") as f:
        info = deserialize(json.load(f), TokenInfo)

    params = convert_params(args.params)

    latex_lines = to_latex(info.txt, info.tokens)
    if (end := params.get("LineEnd")) is not None:
        assert isinstance(end, int)
        latex_lines = latex_lines[:end]
    if (begin := params.get("LineBegin")) is not None:
        assert isinstance(begin, int)
        latex_lines = latex_lines[begin:]

    with open(args.out_path, "w") as f:
        print(latex_line_merge(latex_lines), file=f)


def run_texify_partial(args: Namespace):
    with open(args.in_path, "r") as f:
        info = deserialize(json.load(f), TokenInfo)
    lines = info.txt.splitlines()

    txt: str = args.txt
    occs = [
        (i, j, j + len(txt))
        for i, l in enumerate(lines)
        for j in range(len(l))
        if l[j:].startswith(txt)
    ]

    class TokTup(NamedTuple):
        line: int
        start: int
        end: int
        # the tokens that are fully within the given character range
        full_toks: SemanticTokens
        # the tokens that are partially within the given character range
        all_toks: SemanticTokens

    tokens = [
        TokTup(
            line,
            start,
            end,
            [
                t
                for t in info.tokens
                if t.line == line and t.start >= start and t.end <= end
            ],
            [
                t.limited(start, end)
                for t in info.tokens
                if t.line == line and t.start < end and t.end > start
            ],
        )
        for line, start, end in occs
    ]
    if len(singles := [t for t in tokens if len(t.full_toks) == 1]) > 0:
        tokens = singles

    def latex(start: int, toks: SemanticTokens):
        toks = [replace(t, line=0, start=t.start - start) for t in toks]
        (out,) = to_latex(txt, toks, space=False)
        return out

    index: int | None = args.index
    if index is not None:
        toktup = tokens[index]
        out = latex(toktup.start, toktup.all_toks)
    else:
        outset: set[str] = set()
        for toktup in tokens:
            outset.add(latex(toktup.start, toktup.all_toks))
        assert len(outset) == 1, f"Invalid number of variants for {txt}: {outset}"
        (out,) = outset

    with open(args.out_path, "w") as f:
        print(f"{out}%", file=f)


def run_texify_minimal(args: Namespace):
    (out,) = to_latex(args.txt, compute_minimal_tokens(args.language, args.txt))
    with open(args.out_path, "w") as f:
        print(f"{out}%", file=f)


def run_texify_minimal_file(args: Namespace):
    with open(args.in_path, "r") as f:
        txt = f.read()
    latex_lines = to_latex(txt, compute_minimal_tokens(args.language, txt))
    with open(args.out_path, "w") as f:
        print(latex_line_merge(latex_lines), file=f)


def run():
    parser = ArgumentParser(
        description="Run the pysemco tools, which can analyze source code "
        "and convert it to LaTeX SemCo code."
    )
    subparsers = parser.add_subparsers(dest="cmd")

    # The “analyze” arguments

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze source code and save the resulting tokens for later use.",
    )
    analyze_parser.add_argument(
        "--clear-cache",
        "-c",
        action="store_true",
        help="If there is no stored analysis or the analysis is no longer applicable "
        "because the source code has changed, remove all cached “.tex” files "
        "as well as the “.cache” file in the parent folder of “out_path”.",
    )
    analyze_parser.add_argument(
        "language",
        help="The programming language used in the source file.",
    )
    analyze_parser.add_argument(
        "root_path",
        type=Path,
        help="The root path of the source file’s project.",
    )
    analyze_parser.add_argument(
        "in_path",
        type=Path,
        help="The source file’s path.",
    )
    analyze_parser.add_argument(
        "out_path",
        type=Path,
        help="The path to store the analysis at. "
        "If there is already a file at this path, it is treated as the result of"
        "an earlier analysis and, if the stored source code is the same as "
        "the contents of the source file, the existing analysis is re-used.",
    )

    texify_parser = subparsers.add_parser(
        "texify",
        help="Convert the result of “analyze” to LaTeX SemCo code.",
    )
    texify_parser.add_argument(
        "params",
        help="Additional parameters.",
    )
    texify_parser.add_argument(
        "in_path",
        type=Path,
        help="The path to the analysis produced by “analyze”.",
    )
    texify_parser.add_argument(
        "out_path",
        type=Path,
        help="The path to store the LaTeX SemCo code at.",
    )

    texify_part_parser = subparsers.add_parser(
        "texify_partial",
        help="Convert an occurrence of a given code segment in the result of “analyze” "
        "to LaTeX SemCo code.",
    )
    texify_part_parser.add_argument(
        "--index",
        type=int,
        help="The index of the occurrence to use. If no index is given, "
        "the program fails if there are multiple occurrences.",
    )
    texify_part_parser.add_argument(
        "in_path",
        type=Path,
        help="The path to the analysis produced by “analyze”.",
    )
    texify_part_parser.add_argument(
        "txt",
        help="The code segment to convert.",
    )
    texify_part_parser.add_argument(
        "out_path",
        type=Path,
        help="The path to store the LaTeX SemCo code at.",
    )

    texify_mini_parser = subparsers.add_parser(
        "texify_minimal",
        help="Convert source code to LaTeX SemCo code with minimal analysis.",
    )
    texify_mini_parser.add_argument(
        "language",
        help="The programming language used in the source code.",
    )
    texify_mini_parser.add_argument(
        "txt",
        help="The source code to convert.",
    )
    texify_mini_parser.add_argument(
        "out_path",
        type=Path,
        help="The path to store the LaTeX SemCo code at.",
    )

    texify_mini_file_parser = subparsers.add_parser(
        "texify_minimal_file",
        help="Convert a source file to LaTeX SemCo code with minimal analysis.",
    )
    texify_mini_file_parser.add_argument(
        "language",
        help="The programming language used in the source code.",
    )
    texify_mini_file_parser.add_argument(
        "in_path",
        type=Path,
        help="The path to the source code.",
    )
    texify_mini_file_parser.add_argument(
        "out_path",
        type=Path,
        help="The path to store the LaTeX SemCo code at.",
    )

    args = parser.parse_args()
    match args.cmd:
        case "analyze":
            run_analyze(args)
        case "texify":
            run_texify(args)
        case "texify_partial":
            run_texify_partial(args)
        case "texify_minimal":
            run_texify_minimal(args)
        case "texify_minimal_file":
            run_texify_minimal_file(args)
        case _:
            parser.print_help()


if __name__ == "__main__":
    run()