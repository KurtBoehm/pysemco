from dataclasses import asdict, fields, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, get_args, get_origin


def list_type(typ: Any) -> Any | None:
    """The element type of the given list type or None. E.g. `list[int]` → `int`."""
    if get_origin(typ) is list:
        [t] = get_args(typ)
        return t


def dict_types(typ: Any) -> tuple[Any, Any] | None:
    """The key and value type of the given dict type or None."""
    if get_origin(typ) is dict:
        [k, v] = get_args(typ)
        return k, v


def serialize(obj: Any) -> Any:
    """Convert the argument to a JSON representation.

    The result can be converted back using `deserialize`."""
    if is_dataclass(obj):
        assert not isinstance(obj, type)
        data = asdict(obj)
        return {k: serialize(v) for k, v in data.items()}
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    return obj


def deserialize[T](obj: Any, typ: type[T]) -> T:
    """Convert a JSON representation back into the given type.

    This function is designed as the inverse operation to `serialize`.
    """
    if is_dataclass(typ):
        assert isinstance(obj, dict)
        data: dict[str, Any] = {}
        for f in fields(typ):
            data[f.name] = deserialize(obj[f.name], f.type)  # type: ignore
        return typ(**data)
    if (elem := list_type(typ)) is not None:
        assert isinstance(obj, list)
        return [deserialize(v, elem) for v in obj]  # type: ignore
    if (kv := dict_types(typ)) is not None:
        assert isinstance(obj, dict)
        kt, vt = kv
        assert kt is str
        return {k: deserialize(v, vt) for k, v in obj.items()}  # type: ignore
    if typ is datetime:
        assert isinstance(obj, str)
        return datetime.fromisoformat(obj)  # type: ignore
    if typ is Path:
        assert isinstance(obj, str)
        return Path(obj)  # type: ignore
    assert isinstance(obj, typ)
    return obj  # type: ignore
