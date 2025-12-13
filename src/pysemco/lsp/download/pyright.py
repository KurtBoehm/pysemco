from pathlib import Path
import subprocess
import sys
from shutil import rmtree

from pysemco.lsp.download.defs import data_path, update_version, version_check


def _get_version(python: Path):
    version_prog = "import importlib.metadata as m; print(m.version('basedpyright'))"
    version = subprocess.run(
        [python, "-c", version_prog],
        check=True,
        stdout=subprocess.PIPE,
    )
    return version.stdout.decode().strip()


def _get_dir(log: bool):
    """Determine the path to store pyright at, optionally logging the LSP state."""

    pyr_path = data_path / "basedpyright"

    verch = version_check("basedpyright")
    if verch is not None and not verch.check:
        if log:
            print("basedpyright is up to date!")
        return pyr_path

    python = pyr_path / "bin" / "python3"
    if not python.exists():
        if pyr_path.exists():
            rmtree(pyr_path)
        subprocess.run([sys.executable, "-m", "venv", pyr_path], check=True)
        subprocess.run([python, "-m", "pip", "install", "basedpyright"], check=True)
        update_version("basedpyright", _get_version(python))
        return pyr_path

    if verch is not None and verch.version == _get_version(python):
        if log:
            print("basedpyright version checked and up to date!")
        return pyr_path

    subprocess.run(
        [python, "-m", "pip", "install", "--upgrade", "basedpyright"], check=True
    )
    update_version("basedpyright", _get_version(python))
    return pyr_path


def get_pyright_path(log: bool):
    """Get the path of the pyright executable, optionally logging the LSP state."""
    lsp = _get_dir(log) / "bin" / "basedpyright-langserver"
    assert lsp.exists()
    return lsp
