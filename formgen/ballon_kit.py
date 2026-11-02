"""BALLONs Blender-Baukasten als gepinnter, nur gelesener Schnappschuss (0.3 „Forge“, Machbarkeitsnachweis).

Ergänzt `formgen/ballon.py` (Datenschnappschuss der Formstudien) um die Teile, die BALLON zum Bauen in Blender braucht:
`basic/` (kit.py, Piloten, Arme für das Ego-Profil), `tools/` (blender_build, bake_unity, export_unity, ego_build) und BALLONs
Unity-Export `ego.json` (Netzgrenzen je Objekt als Referenz). Gleicher Commit wie `config.toml › [ballon]`, eigener Ordner
`<commit>.kit` (atomar entpackt, über Worktrees geteilt). Hashes hängen nur am Inhalt (wie `ballon.closure`).
"""
from __future__ import annotations

import ast
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from . import ballon
from .cache import canonical

PATHS = ("basic", "tools", "data/specs", "unity/Assets/Ballon/Generated/ego.json")
EGO_JSON = "unity/Assets/Ballon/Generated/ego.json"
# BALLON-Code, den ein Blender-Lauf aufruft: Baukasten, Modellbau, Backen, Unity-Export
BACKEND = ("basic/kit.py", "tools/blender_build.py", "tools/bake_unity.py", "tools/export_unity.py")


def snapshot(commit: str | None = None, repo: Path | None = None, root: Path = ballon.SNAPSHOTS) -> Path:
    """Verified read-only extraction of the pinned commit with BALLON's Blender kit (extracts once, atomically)."""
    cfg = ballon.config()
    commit, repo = commit or cfg["commit"], Path(repo or cfg["repo"])
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ballon.BallonError("BALLON-Commit muss eine volle SHA-1 sein")
    target = Path(root) / f"{commit}.kit"
    if (target / ".complete").is_file():
        return target
    if not (repo / ".git").exists():
        raise ballon.BallonError(f"BALLON-Repo fehlt: {repo} (FORMGEN_BALLON_REPO setzen)")
    Path(root).mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{commit[:12]}-kit-", dir=root))
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


def closure_files(snap: Path, roots, packages=("basic", "tools")) -> dict[str, str]:
    """Relative path → SHA256 of `roots` and all statically imported modules of `packages` (plus package `__init__`)."""
    snap = Path(snap)
    found: dict[str, str] = {}

    def visit(path: Path):
        rel = path.relative_to(snap).as_posix()
        if rel in found:
            return
        data = path.read_bytes()
        found[rel] = hashlib.sha256(data).hexdigest()
        for parent in path.relative_to(snap).parents:          # Paket-__init__ laufen beim Import mit
            if parent != Path(".") and (snap / parent / "__init__.py").is_file():
                visit(snap / parent / "__init__.py")
        for node in ast.walk(ast.parse(data, filename=rel)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
            for name in names:
                parts = name.split(".")
                if parts[0] not in packages:
                    continue
                for candidate in (snap.joinpath(*parts).with_suffix(".py"), snap.joinpath(*parts) / "__init__.py"):
                    if candidate.is_file():
                        visit(candidate)

    for root in roots:
        visit(Path(root))
    return dict(sorted(found.items()))


def backend_hash(snap: Path) -> str:
    return hashlib.sha256(canonical(closure_files(snap, [Path(snap) / f for f in BACKEND]))).hexdigest()


def pilot_file(snap: Path, num: str) -> Path | None:
    """Neuester Spiel-Pilot eines Typs: basic/pilot/wNN_*_vK.py mit der höchsten Fassung K (v21 = 2.1 > v2), sonst None."""
    found = []
    for path in (Path(snap) / "basic/pilot").glob(f"w{num}_*_v*.py"):
        m = re.fullmatch(rf"w{num}_[a-z0-9_]+_v(\d+)", path.stem)
        if m:
            found.append((tuple(int(c) for c in m.group(1)), path))
    return max(found)[1] if found else None


def module_name(snap: Path, path: Path) -> str:
    return ".".join(Path(path).relative_to(Path(snap)).with_suffix("").parts)
