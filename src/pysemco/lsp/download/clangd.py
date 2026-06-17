import platform
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from shutil import rmtree

import requests

from pysemco.lsp.download.defs import data_path, github, update_version, version_check


def _system_prefix() -> str:
    system = platform.system()
    if system == "Linux":
        prefix = "clangd-linux-"
    elif system == "Darwin":
        prefix = "clangd-mac-"
    elif system == "Windows":
        prefix = "clangd-windows-"
    else:
        raise RuntimeError(f"Unsupported OS: {system}")
    return prefix


def _get_dir(log: bool) -> Path:
    """Determine the path to store clangd at, optionally logging the LSP state."""
    verch = version_check("clangd")
    if verch is not None and not verch.check:
        if log:
            print("clangd is up to date!", file=sys.stderr)
        return data_path / f"clangd-{verch.version}"

    clangd = github().get_repo("clangd/clangd")
    release = clangd.get_latest_release()
    version = release.name
    if verch is not None and verch.version == version:
        if log:
            print("clangd version checked and up to date!", file=sys.stderr)
        update_version("clangd", version)
        return data_path / f"clangd-{version}"

    dir = data_path / f"clangd-{version}"
    if log:
        print(f"Download clangd to {dir}…", file=sys.stderr)

    if verch is not None:
        rmtree(data_path / f"clangd-{verch.version}")
    if dir.exists():
        rmtree(dir)

    assets = release.assets
    system_prefix = _system_prefix()
    [asset] = [asset for asset in assets if asset.name.startswith(system_prefix)]
    data = requests.get(asset.browser_download_url).content

    zip = zipfile.ZipFile(BytesIO(data))
    zip.extractall(dir)
    [subdir] = list(dir.iterdir())
    for p in subdir.iterdir():
        p.rename(dir / p.relative_to(subdir))
    subdir.rmdir()

    update_version("clangd", version)

    return dir


def get_clangd_path(log: bool) -> Path:
    """Get the path of the clangd executable, optionally logging the LSP state."""
    lsp = _get_dir(log=log) / "bin" / "clangd"
    assert lsp.exists()
    lsp.chmod(0o755)
    return lsp
