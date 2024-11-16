from typing import Protocol, Self, TypedDict


class SupportsAdd(Protocol):
    def __add__(self, x: Self, /) -> Self: ...


class StyleDict[T](TypedDict):
    """The style information used in `colorful`."""

    red: T
    green: T
    light_blue: T
    dark_blue: T
    grey: T
    indigo: T
    orange: T
    pink: T
    purple: T
    italic: T
    bold: T


def colorful[T: SupportsAdd](styles: StyleDict[T]) -> dict[str, T]:
    """The colorful token style using the given style dictionary."""
    return {
        "attribute": styles["light_blue"],
        "builtin-variable": styles["orange"],
        "class": styles["purple"],
        "comment": styles["grey"],
        "concept": styles["indigo"],
        "decorator": styles["light_blue"],
        "enum": styles["purple"],
        "enumMember": styles["dark_blue"],
        "function": styles["green"],
        "keyword": styles["red"],
        "keyword-fun": styles["green"],
        "keyword-type": styles["purple"],
        "keyword-value": styles["dark_blue"],
        "label": styles["light_blue"],
        "literal-affix": styles["red"],
        "literal-character": styles["dark_blue"],
        "literal-float": styles["dark_blue"],
        "literal-include": styles["dark_blue"],
        "literal-int": styles["dark_blue"],
        "literal-string": styles["dark_blue"],
        "macro": styles["light_blue"],
        "method": styles["italic"] + styles["green"],
        "namespace": styles["pink"],
        "parameter": styles["bold"] + styles["orange"],
        "preprocessor": styles["red"],
        "property": styles["italic"] + styles["orange"],
        "type": styles["purple"],
        "typeParameter": styles["bold"] + styles["purple"],
        "variable": styles["orange"],
    }
