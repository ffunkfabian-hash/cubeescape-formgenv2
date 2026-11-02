"""Variantenregister (data/variants.toml): Linien mit Kennbuchstabe und englischem Namen über alle 17 BALLON-Typen.

Regel (übernommen aus Formgen v1, Nutzer 17.10.2026): jede neue Variante bekommt zum Kennbuchstaben einen kurzen,
markanten englischen Namen (1–3 Wörter, je Wort Großbuchstabe + Kleinbuchstaben, höchstens 16 Zeichen). Namen und
Buchstaben nicht doppelt, I und O nie. Blatt-ID = "B" + Buchstabe + BASIC-Nummer; vergebene IDs sind ewig.

  python -m formgen.variants list
  python -m formgen.variants new D "Glass Fang" "Idee in einem Satz" --skin kobalt --front 1.1 --rear 1.0
"""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/variants.toml"
NAME = re.compile(r"^[A-Z][a-z]+(?: [A-Z][a-z]+){0,2}$")
SKIP = "IO"
PARAMS = {"front": (0.7, 1.4), "rear": (0.7, 1.4)}
TYPES = tuple(f"{n:02d}" for n in range(1, 18))


class VariantError(ValueError):
    pass


def check(entries: list[dict], skins: set[str] | None = None) -> None:
    letters, names = set(), set()
    for v in entries:
        letter, name = v.get("letter", ""), v.get("name", "")
        if not (len(letter) == 1 and "A" <= letter <= "Z") or letter in SKIP:
            raise VariantError(f"Ungültiger Kennbuchstabe {letter!r} (A–Z ohne I/O)")
        if not NAME.match(name) or len(name) > 16:
            raise VariantError(f"Name {name!r}: 1–3 englische Wörter, Großschreibung, höchstens 16 Zeichen")
        if letter in letters or name.lower() in names:
            raise VariantError(f"Buchstabe oder Name doppelt: {letter} {name}")
        letters.add(letter); names.add(name.lower())
        if not v.get("idea") or not v.get("since"):
            raise VariantError(f"{letter}: idea und since sind Pflicht")
        if skins is not None and v.get("skin", "standard") not in skins:
            raise VariantError(f"{letter}: unbekannter Skin {v.get('skin')}")
        params = v.get("params", {})
        for key, value in params.items():
            if key == "drop":
                if not (isinstance(value, list) and all(isinstance(x, str) and x for x in value)):
                    raise VariantError(f"{letter}: drop muss eine Liste von Teil-ID-Mustern sein")
            elif key in PARAMS:
                lo, hi = PARAMS[key]
                if not (isinstance(value, (int, float)) and lo <= value <= hi):
                    raise VariantError(f"{letter}: {key}={value} außerhalb {lo}–{hi}")
            else:
                raise VariantError(f"{letter}: unbekannter Parameter {key}")
        types = v.get("types", list(TYPES))
        if not types or any(t not in TYPES for t in types):
            raise VariantError(f"{letter}: types nur aus 01–17")


def _skins() -> set[str]:
    with (ROOT / "skins.toml").open("rb") as stream:
        return set(tomllib.load(stream)["skins"])


def load(path: Path = REGISTRY) -> list[dict]:
    with Path(path).open("rb") as stream:
        data = tomllib.load(stream)
    if data.get("schema") != 1:
        raise VariantError("Variantenregister: schema 1 erwartet")
    entries = data.get("variants", [])
    check(entries, _skins())
    for v in entries:
        v.setdefault("skin", "standard"); v.setdefault("params", {}); v.setdefault("types", list(TYPES))
    return entries


def sheet_id(letter: str, num: str) -> str:
    return f"B{letter}{num}"


def sheets(entries: list[dict] | None = None) -> dict[str, dict]:
    """Sheet ID → {variant, num} for every registered variant and type, in register order."""
    entries = load() if entries is None else entries
    return {sheet_id(v["letter"], num): {"variant": v, "num": num} for v in entries for num in v.get("types", TYPES)}


def parse_sheet(sid: str) -> tuple[str, str]:
    m = re.fullmatch(r"B([A-HJ-NP-Z])(\d\d)", sid)
    if not m or m.group(2) not in TYPES:
        raise VariantError(f"Ungültige Blatt-ID {sid!r} (Muster BA01 … BZ17)")
    return m.group(1), m.group(2)


def _toml(value):
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(value, list):
        return "[" + ", ".join(_toml(x) for x in value) + "]"
    return repr(value)


def new(letter, name, idea, since, skin="standard", params=None, path: Path = REGISTRY) -> dict:
    entries = load(path)
    entry = {"letter": letter, "name": name, "idea": idea, "since": since, "skin": skin, "params": params or {}}
    check(entries + [entry], _skins())
    text = Path(path).read_text()
    block = (f'\n[[variants]]\nletter = {_toml(letter)}\nname = {_toml(name)}\nidea = {_toml(idea)}\n'
             f'since = {_toml(since)}\nskin = {_toml(skin)}\n[variants.params]\n'
             + "".join(f"{k} = {_toml(v)}\n" for k, v in (params or {}).items()))
    Path(path).write_text(text.rstrip("\n") + "\n" + block)
    load(path)
    return entry


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    n = sub.add_parser("new")
    n.add_argument("letter"); n.add_argument("name"); n.add_argument("idea")
    n.add_argument("--since", default=None); n.add_argument("--skin", default="standard")
    n.add_argument("--front", type=float); n.add_argument("--rear", type=float); n.add_argument("--drop", nargs="*")
    a = p.parse_args(argv)
    if a.cmd == "list":
        for v in load():
            print(f'{v["letter"]} · {v["name"]:16} {v["skin"]:9} {v["params"]}  {v["idea"]}')
        return 0
    from . import __version__
    params = {k: getattr(a, k) for k in ("front", "rear", "drop") if getattr(a, k) is not None}
    try:
        e = new(a.letter, a.name, a.idea, a.since or ".".join(__version__.split(".")[:2]), a.skin, params)
    except VariantError as error:
        print(f"abgelehnt: {error}", file=sys.stderr)
        return 1
    print(f"eingetragen: {e['letter']} · {e['name']} → Blätter B{e['letter']}01 … B{e['letter']}17")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
