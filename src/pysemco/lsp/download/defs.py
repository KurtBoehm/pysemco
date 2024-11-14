import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from github import Github
from platformdirs import user_data_path

from pysemco.serialization import deserialize, serialize


@dataclass
class LspInfo:
    """The version of an LSP and the last time it was checked."""

    version: str
    last_check: datetime


LspInfos = dict[str, LspInfo]


@dataclass
class VersionCheck:
    """The version of an LSP and whether it should be checked."""

    version: str
    check: bool


# The path at which pysemco’s LSPs and other data is stored
data_path = user_data_path() / "pysemco"
data_path.mkdir(exist_ok=True)

# The path of the state file
_state_path = data_path / "state.json"


def _get_state() -> LspInfos | None:
    """The currently stored LSP state, or None if none has been stored yet."""
    if _state_path.exists():
        with open(_state_path, "r") as f:
            return deserialize(json.load(f), LspInfos)


def version_check(name: str) -> VersionCheck | None:
    """Determine the version of a stored LSP and whether to check if it is up to date.

    Args:
        name: The name of the language server.

    Returns:
        The stored version and whether to check it, or None if none is stored.
    """
    state = _get_state()
    if state is not None and (info := state.get(name)) is not None:
        return VersionCheck(
            version=info.version,
            check=(datetime.now() - info.last_check) > timedelta(days=1),
        )


def update_version(name: str, version: str) -> None:
    """Update the stored version of a given LSP.

    Args:
        name: The name of the LSP.
        version: The new version of the LSP.
    """
    state = _get_state()
    if state is None:
        state = {}
    state[name] = LspInfo(version, datetime.now())
    with open(_state_path, "w") as f:
        json.dump(serialize(state), f, indent=2)


def github() -> Github:
    """Create a new GitHub instance."""
    return Github()
