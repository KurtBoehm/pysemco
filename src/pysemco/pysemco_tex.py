import json
from argparse import ArgumentParser, Namespace
from dataclasses import replace
from pathlib import Path
from typing import Any, NamedTuple

import yaml

from .convert import latex_line_merge, to_latex
from .serialization import deserialize, serialize
from .tokens import (
    SemanticToken,
    SemanticTokens,
    compute_minimal_tokens,
    compute_tokens_sync,
)


def convert_params(pstr: str):
    return yaml.safe_load(f"{{{pstr}}}")


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

        tokens = compute_tokens_sync(args.language, root, src, txt, log_lsp=True)
        with open(dst, "w") as f:
            json.dump(serialize(tokens), f)

    if dst.exists():
        with open(src, "r") as f:
            txt = f.read()
        with open(dst, "r") as f:
            tokens = deserialize(json.load(f), SemanticTokens)
        if txt != tokens.txt:
            save_tokens(txt)
    else:
        save_tokens()


def run_texify(args: Namespace):
    with open(args.in_path, "r") as f:
        tokens = deserialize(json.load(f), SemanticTokens)

    params = convert_params(args.params)
    assert isinstance(params, dict)
    latex_lines = to_latex(SemanticTokens(tokens.txt, tokens.toks))

    def apply_line_range(line_range: list[Any]):
        if len(line_range) == 2:
            begin, end = line_range
            if isinstance(begin, int) and isinstance(end, int):
                return latex_lines[begin:end]
        lines: list[str] = []
        for r in line_range:
            assert isinstance(r, list) and len(r) == 2
            begin, end = r
            assert isinstance(begin, int) and isinstance(end, int)
            lines.extend(latex_lines[begin:end])
        return lines

    if (end := params.get("LineEnd")) is not None:
        assert isinstance(end, int)
        latex_lines = latex_lines[:end]
    if (begin := params.get("LineBegin")) is not None:
        assert isinstance(begin, int)
        latex_lines = latex_lines[begin:]
    if (line_range := params.get("LineRange")) is not None:
        assert "LineBegin" not in params and "LineEnd" not in params
        assert isinstance(line_range, list)
        latex_lines = apply_line_range(line_range)

    with open(args.out_path, "w") as f:
        print(latex_line_merge(latex_lines), file=f)


def run_texify_partial(args: Namespace):
    with open(args.in_path, "r") as f:
        tokens = deserialize(json.load(f), SemanticTokens)
    lines = tokens.txt.splitlines()

    txt: str = args.txt
    txt = txt.strip()
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
        full_toks: list[SemanticToken]
        # the tokens that are partially within the given character range
        all_toks: list[SemanticToken]

    tokens = [
        TokTup(
            line,
            start,
            end,
            [
                t
                for t in tokens.toks
                if t.line == line
                and t.start >= start
                and t.end <= end
                and t.token_type not in ("unknown",)
            ],
            [
                t.limited(start, end)
                for t in tokens.toks
                if t.line == line
                and t.start < end
                and t.end > start
                and t.token_type not in ("unknown",)
            ],
        )
        for line, start, end in occs
    ]
    if len(singles := [t for t in tokens if len(t.full_toks) == 1]) > 0:
        tokens = singles

    def latex(start: int, toks: list[SemanticToken]):
        toks = [replace(t, line=0, start=t.start - start) for t in toks]
        (out,) = to_latex(SemanticTokens(txt, toks), space=False)
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
    (out,) = to_latex(
        SemanticTokens(args.txt, compute_minimal_tokens(args.language, args.txt))
    )
    with open(args.out_path, "w") as f:
        print(f"{out}%", file=f)


def run_texify_minimal_file(args: Namespace):
    with open(args.in_path, "r") as f:
        txt = f.read()
    params = convert_params(args.params)
    name_map = params.get("NameMap")
    if name_map is None and (m := params.get("TokenNames")) is not None:
        name_map = {t: k for k, l in m.items() for t in l}
    latex_lines = to_latex(
        SemanticTokens(
            txt,
            compute_minimal_tokens(args.language, txt, name_map=name_map),
        )
    )
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
        "params",
        help="Additional parameters.",
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
