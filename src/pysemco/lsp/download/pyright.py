import subprocess
import sys
import tarfile
from io import BytesIO
from shutil import rmtree

import requests

from pysemco.lsp.download.defs import data_path, github, update_version, version_check


def _get_dir(log: bool):
    """Determine the path to store pyright at, optionally logging the LSP state."""

    verch = version_check("pyright")
    if verch is not None and not verch.check:
        if log:
            print("pyright is up to date!")
        return data_path / f"pyright-{verch.version}"

    repo = github().get_repo("DetachHead/basedpyright")
    tarball = repo.get_latest_release().tarball_url
    version = tarball.rsplit("/", 1)[-1]
    if verch is not None and verch.version == version:
        if log:
            print("pyright version checked and up to date!")
        update_version("pyright", version)
        return data_path / f"pyright-{version}"

    dir = data_path / f"pyright-{version}"
    if log:
        print(f"Download pyright to {dir}…")

    if verch is not None:
        p = data_path / f"pyright-{verch.version}"
        if p.exists():
            rmtree(p)
    if dir.exists():
        rmtree(dir)

    data = requests.get(tarball).content
    tarfile.open(fileobj=BytesIO(data), mode="r").extractall(dir)
    [subdir] = list(dir.iterdir())
    for p in subdir.iterdir():
        p.rename(dir / p.relative_to(subdir))
    subdir.rmdir()

    subprocess.run([sys.executable, "-m", "pip", "install", "docify"], check=True)
    subprocess.run(
        [sys.executable, "build/py3_8/generate_docstubs.py"],
        cwd=dir,
        check=True,
    )

    print("!" * 100 + "npm ci")
    subprocess.run(["npm", "ci"], cwd=dir, check=True)
    print("!" * 100 + "npm run")
    subprocess.run(
        ["npm", "run", "build"],
        cwd=dir / "packages" / "pyright",
        check=True,
    )
    print("!" * 100 + "npm post")

    update_version("pyright", version)

    return dir


def get_pyright_path(log: bool):
    """Get the path of the pyright executable, optionally logging the LSP state."""
    lsp = _get_dir(log) / "packages" / "pyright" / "langserver.index.js"
    assert lsp.exists()
    return lsp
