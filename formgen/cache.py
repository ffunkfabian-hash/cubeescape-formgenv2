"""Content-addressed artefacts, verified restoration and process-safe publication."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Iterable

from .versions import CACHE as VERSION


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class Artifact:
    model_id: str
    kind: str
    source: str
    params: dict
    versions: dict
    output: str
    builder: str
    inputs: dict

    @property
    def key(self) -> str:
        return hashlib.sha256(canonical({"cache": VERSION, "model": self.model_id, "source": self.source,
                                        "kind": self.kind, "params": self.params,
                                        "versions": self.versions})).hexdigest()


@dataclass(frozen=True)
class Result:
    output: str
    key: str
    built: bool
    reason: str


def _relative(output: str) -> Path:
    path = Path(output)
    if (path.is_absolute() or not path.parts or str(path) != output or
            any(p in ("..", ".") for p in path.parts)):
        raise ValueError(f"Artefaktpfad muss relativ und sicher sein: {output!r}")
    if path.parts[0] in ("manifest.json", ".locks"):
        raise ValueError(f"Reservierter Artefaktpfad: {output}")
    return path


@contextmanager
def _lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def atomic_write(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _entry(entry: Path, key: str) -> dict | None:
    try:
        if entry.is_symlink():
            return None
        meta = json.loads((entry / "entry.json").read_text(encoding="utf-8"))
        payload = entry / "artifact"
        if (not isinstance(meta, dict) or meta.get("key") != key or
                meta.get("format") != VERSION or payload.is_symlink() or
                payload.stat().st_size != meta.get("size") or
                file_hash(payload) != meta.get("sha256")):
            return None
        return meta
    except (OSError, ValueError, TypeError):
        return None


def valid_entry(entry: Path, key: str) -> bool:
    return _entry(Path(entry), key) is not None


def _record(out: Path, artifact: Artifact, result: Result, meta: dict) -> None:
    with _lock(out / ".locks" / "manifest.lock"):
        path = out / "manifest.json"
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict) or not isinstance(manifest.get("artifacts"), dict):
                raise ValueError("Ungültiges Manifest")
        except (OSError, ValueError):
            manifest = {"format": VERSION, "artifacts": {}}
        manifest["artifacts"][artifact.output] = {
            "model": artifact.model_id, "kind": artifact.kind, "key": result.key,
            "source": artifact.source, "params": artifact.params, "versions": artifact.versions,
            "sha256": meta["sha256"], "size": meta["size"],
            "status": "built" if result.built else "cached", "reason": result.reason,
        }
        atomic_write(path, canonical(manifest) + b"\n")


def build_one(artifact: Artifact, out: Path, cache: Path, force: bool = False) -> Result:
    """Build one byte artefact or restore it; a failure never publishes partial data."""
    out, cache = Path(out).resolve(), Path(cache).resolve()
    relative = _relative(artifact.output)
    destination = out / relative
    if not destination.resolve().is_relative_to(out):
        raise ValueError(f"Artefaktpfad verlässt Ausgabeordner: {artifact.output}")
    key = artifact.key
    entry = cache / key
    output_lock = hashlib.sha256(artifact.output.encode()).hexdigest()
    with _lock(out / ".locks" / f"{output_lock}.lock"), _lock(cache / ".locks" / f"{key}.lock"):
        meta = _entry(entry, key)
        built = force or meta is None
        if built:
            reason = "force" if force else ("corrupt_cache" if entry.exists() else "missing_cache")
            module, separator, function = artifact.builder.partition(":")
            if not separator:
                raise ValueError("Builder muss 'modul:funktion' sein")
            data = getattr(importlib.import_module(module), function)(artifact)
            if isinstance(data, str):
                data = data.encode("utf-8")
            if not isinstance(data, bytes):
                raise TypeError("Artefakt-Builder muss bytes oder str liefern")
            meta = {"format": VERSION, "key": key, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            staging = Path(tempfile.mkdtemp(prefix=f".{key}.", dir=cache))
            try:
                atomic_write(staging / "artifact", data)
                atomic_write(staging / "entry.json", canonical(meta) + b"\n")
                if entry.is_symlink() or (entry.exists() and not entry.is_dir()):
                    entry.unlink()
                elif entry.exists():
                    shutil.rmtree(entry)
                os.replace(staging, entry)
            finally:
                if staging.exists():
                    shutil.rmtree(staging)
        else:
            reason = "cache_hit"
        try:
            output_valid = destination.is_file() and file_hash(destination) == meta["sha256"]
        except OSError:
            output_valid = False
        if not output_valid:
            if not built:
                reason = "restored_corrupt_output" if destination.exists() else "restored_missing_output"
            atomic_write(destination, (entry / "artifact").read_bytes())
        result = Result(artifact.output, key, built, reason)
        _record(out, artifact, result, meta)
        return result


def _worker(args):
    return build_one(*args)


def run_artifacts(artifacts: Iterable[Artifact], out: Path, cache: Path, *, jobs: int = 1,
                  force: bool = False, force_kinds: Iterable[str] = ()) -> list[Result]:
    """Run independent artefacts; callers schedule dependent stages in separate calls."""
    if jobs < 1:
        raise ValueError("jobs muss mindestens 1 sein")
    artifacts = list(artifacts)
    outputs = [artifact.output for artifact in artifacts]
    if len(set(outputs)) != len(outputs):
        raise ValueError("Mehrere Artefakte besitzen denselben Ausgabepfad")
    for output in outputs:
        _relative(output)
    selected = set(force_kinds)
    args = [(artifact, out, cache, force or artifact.kind in selected) for artifact in artifacts]
    if jobs == 1:
        return [_worker(arg) for arg in args]
    with ProcessPoolExecutor(max_workers=jobs) as executor:
        return list(executor.map(_worker, args))
