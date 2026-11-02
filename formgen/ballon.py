"""BALLON als gepinnte, nur gelesene Grundlage der 17 BASIC-Waffentypen.

Die Quelle ist ein Commit aus `config.toml › [ballon]`. `snapshot()` entpackt nur die benötigten Pfade per
`git archive` in einen inhaltsadressierten Ordner (atomar, über Worktrees geteilt). Der Quellhash eines Typs
hängt nur vom Inhalt seiner Import-Closure ab (nie von Pfaden, Dateizeiten oder der Commit-ID): ein BALLON-Commit,
der den Typ nicht berührt, behält alle Cache-Treffer.

BALLON-Module sind reines Python ohne bpy (`basic/common.py`, `basic/weapons/wNN_*.py`); geladen werden nur
Datensätze (META, PARTS, ASSEMBLIES, ANCHORS, ACTIONS), die der Generator als Grundform nutzt.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib

from .cache import canonical

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = Path.home() / "Library/Caches/CubeEscapeFormgen2/ballon"
PATHS = ("basic/__init__.py", "basic/common.py", "basic/weapons", "data/specs")
TYPES = tuple(f"{n:02d}" for n in range(1, 18))


class BallonError(RuntimeError):
    pass


def config(path: Path = ROOT / "config.toml") -> dict:
    with Path(path).open("rb") as stream:
        data = tomllib.load(stream)["ballon"]
    repo = Path(os.environ.get("FORMGEN_BALLON_REPO", data["repo"])).expanduser()
    return {"repo": repo, "commit": data["commit"]}


def snapshot(commit: str | None = None, repo: Path | None = None, root: Path = SNAPSHOTS) -> Path:
    """Return a verified read-only extraction of the pinned commit (extracts once, atomically)."""
    cfg = config()
    commit, repo = commit or cfg["commit"], Path(repo or cfg["repo"])
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise BallonError("BALLON-Commit muss eine volle SHA-1 sein")
    target = Path(root) / commit
    if (target / ".complete").is_file():
        return target
    if not (repo / ".git").exists():
        raise BallonError(f"BALLON-Repo fehlt: {repo} (FORMGEN_BALLON_REPO setzen)")
    if subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{commit}^{{commit}}"],
                      capture_output=True).returncode:
        raise BallonError(f"BALLON-Commit {commit[:12]} unbekannt; in {repo} `git fetch origin` ausführen")
    Path(root).mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{commit[:12]}-", dir=root))
    try:
        archive = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", commit, *PATHS],
                                 capture_output=True, check=True).stdout
        subprocess.run(["tar", "-x", "-C", str(tmp)], input=archive, check=True)
        (tmp / ".complete").write_text(commit + "\n")
        try:
            os.replace(tmp, target)
        except OSError:
            if not (target / ".complete").is_file():
                raise
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    return target


def module_file(snap: Path, num: str) -> Path:
    found = sorted((Path(snap) / "basic/weapons").glob(f"w{num}_*.py"))
    if len(found) != 1:
        raise BallonError(f"BASIC-{num}: genau ein Modul basic/weapons/w{num}_*.py erwartet, gefunden {len(found)}")
    return found[0]


def closure(snap: Path, num: str) -> dict[str, str]:
    """Relative path → SHA256 of the type module and all statically imported `basic` modules."""
    snap = Path(snap)
    found: dict[str, str] = {}

    def visit(path: Path):
        rel = path.relative_to(snap).as_posix()
        if rel in found:
            return
        data = path.read_bytes()
        found[rel] = hashlib.sha256(data).hexdigest()
        for node in ast.walk(ast.parse(data, filename=rel)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
            for name in names:
                if name.split(".")[0] != "basic":
                    continue
                parts = name.split(".")
                for candidate in (snap.joinpath(*parts).with_suffix(".py"), snap.joinpath(*parts) / "__init__.py"):
                    if candidate.is_file():
                        visit(candidate)
                for i in range(1, len(parts)):
                    package = snap.joinpath(*parts[:i]) / "__init__.py"
                    if package.is_file():
                        visit(package)

    visit(module_file(snap, num))
    for package in ("basic/__init__.py", "basic/weapons/__init__.py"):   # beim Import ausgeführt
        if (snap / package).is_file():
            visit(snap / package)
    return dict(sorted(found.items()))


def spec_path(snap: Path, num: str) -> Path:
    return Path(snap) / f"data/specs/BASIC-{num}.spec.json"


def source(snap: Path, num: str) -> dict:
    """Content identity of one BASIC type: closure hash plus hash of BALLON's exported spec."""
    files = closure(snap, num)
    spec = spec_path(snap, num)
    return {"basic_id": f"BASIC-{num}", "files": files,
            "source_sha256": hashlib.sha256(canonical(files)).hexdigest(),
            "spec_sha256": hashlib.sha256(spec.read_bytes()).hexdigest() if spec.is_file() else "missing"}


def load_spec(snap: Path, num: str) -> dict | None:
    path = spec_path(snap, num)
    return json.loads(path.read_bytes()) if path.is_file() else None


def _purge():
    for name in [n for n in sys.modules if n == "basic" or n.startswith("basic.")]:
        del sys.modules[name]


def load(snap: Path, num: str) -> dict:
    """Import one BALLON weapon module from the snapshot and return deep-copied data only."""
    snap = Path(snap)
    path = module_file(snap, num)
    _purge()
    sys.path.insert(0, str(snap))
    try:
        module = importlib.import_module(f"basic.weapons.{path.stem}")
        data = {key: copy.deepcopy(getattr(module, key, default)) for key, default in
                (("META", None), ("PARTS", None), ("ASSEMBLIES", None), ("ANCHORS", {}), ("ACTIONS", {}))}
    finally:
        sys.path.remove(str(snap))
        _purge()
    if not data["META"] or not data["PARTS"] or not data["ASSEMBLIES"]:
        raise BallonError(f"{path.name}: META/PARTS/ASSEMBLIES fehlen")
    if data["META"].get("id") != f"BASIC-{num}":
        raise BallonError(f"{path.name}: META.id {data['META'].get('id')} ≠ BASIC-{num}")
    return data
