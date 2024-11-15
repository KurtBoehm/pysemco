import subprocess
import tarfile
from importlib.resources import files
from io import BytesIO
from pathlib import Path
from shutil import rmtree
from tempfile import TemporaryDirectory

import requests

from pysemco.lsp.download.defs import data_path, github, update_version, version_check


def _get_dir(log: bool):
    """Determine the path to store pyright at."""

    verch = version_check("pyright")
    if verch is not None and not verch.check:
        if log:
            print("pyright is up to date!")
        return data_path / f"pyright-{verch.version}"

    repo = github().get_repo("microsoft/pyright")
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
        rmtree(data_path / f"pyright-{verch.version}")
    if dir.exists():
        rmtree(dir)

    data = requests.get(tarball).content
    tarfile.open(fileobj=BytesIO(data), mode="r").extractall(dir)
    [subdir] = list(dir.iterdir())
    for p in subdir.iterdir():
        p.rename(dir / p.relative_to(subdir))
    subdir.rmdir()

    with TemporaryDirectory() as tmp:
        patch = files() / "pyright.patch"
        tmp_patch = Path(tmp) / "pyright.patch"
        with patch.open("r") as inf, open(tmp_patch, "w") as outf:
            outf.write(inf.read())
        subprocess.run(["git", "apply", tmp_patch], cwd=dir, check=True)
    subprocess.run(["npm", "ci"], cwd=dir, check=True)
    subprocess.run(
        ["npm", "run", "build"],
        cwd=dir / "packages" / "pyright",
        check=True,
    )

    update_version("pyright", version)

    return dir


def get_pyright_path(log: bool):
    """Get the path of the pyright executable."""
    lsp = _get_dir(log) / "packages" / "pyright" / "langserver.index.js"
    assert lsp.exists()
    return lsp
