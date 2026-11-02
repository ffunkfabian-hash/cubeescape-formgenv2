"""Variantenregister (data/variants.toml): Linien mit Kennbuchstabe und englischem Namen über alle 17 BALLON-Typen.

Regel (übernommen aus Formgen v1, Nutzer 17.10.2026): jede neue Variante bekommt zum Kennbuchstaben einen kurzen,
markanten englischen Namen (1–3 Wörter, je Wort Großbuchstabe + Kleinbuchstaben, höchstens 16 Zeichen). Namen und
Buchstaben nicht doppelt, I und O nie. Blatt-ID = "B" + Buchstabe + BASIC-Nummer; vergebene IDs sind ewig.

Gesteuerter Zufall (0.4): ein Parameter ist fest (Zahl/Wort) oder ein Bereich – Zahlen als [von, bis], Bausteine als Liste
zur Auswahl. Gezogen wird je Blatt aus einem festen Seed (SHA256 über Blatt-ID und Linie) und je Parameter getrennt
(SHA256 über Seed und Parametername): ein neuer Parameter verschiebt keine andere Ziehung, PYTHONHASHSEED wirkt nicht.

  python -m formgen.variants list
  python -m formgen.variants new J "Glass Fang" "Idee in einem Satz" --skin kobalt --param front=[1.0,1.1] --param sight='["zinken"]'
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/variants.toml"
NAME = re.compile(r"^[A-Z][a-z]+(?: [A-Z][a-z]+){0,2}$")
SKIP = "IO"
# Zahlenparameter: Grenzen sind Vorgaben dieses Registers (Annahme: darüber zerfallen BALLON-Proportionen sichtbar)
PARAMS = {"front": (0.7, 1.4), "rear": (0.7, 1.4), "limbs": (0.8, 1.3), "mag": (0.7, 1.4), "muzzle": (0.6, 2.0),
          "muzzle_r": (0.8, 1.3), "stock_scale": (0.8, 1.25)}
INTS = {"glow": (0, 2)}
# Bausteine aus BALLON basic/common.py (Visier-Baukasten v3, Schaft S1/S2, Griff v2.1)
HOLO = ("reflex_sight_v21", "holo_kasten", "holo_pille", "zinken", "boegen", "achteck", "d_linse", "entfernung")
SCOPES = ("scope_tropfen", "gabel", "lang")
PRECISION = ("03", "09", "11")   # Vorgabe Auftrag 0.4: Zielfernrohr nur an Scout, Scharfschütze, lineare Fusion
CHOICES = {"sight": HOLO + SCOPES, "stock": ("S1", "S2"), "grip": ("v21",)}
BASES = ("standard", "v21")
SCHEMA = 2
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
        if v.get("base", "standard") not in BASES:
            raise VariantError(f"{letter}: base nur {'/'.join(BASES)}")
        for key, value in v.get("params", {}).items():
            _check_param(letter, key, value)
        types = v.get("types", list(TYPES))
        if not types or any(t not in TYPES for t in types):
            raise VariantError(f"{letter}: types nur aus 01–17")


def _number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _check_param(letter, key, value):
    if key == "drop":
        if not (isinstance(value, list) and value and all(isinstance(x, str) and x for x in value)):
            raise VariantError(f"{letter}: drop muss eine Liste von Teil-ID-Mustern sein")
    elif key in PARAMS or key in INTS:
        lo, hi = PARAMS.get(key) or INTS[key]
        values = value if isinstance(value, list) else [value]
        if isinstance(value, list) and not (len(value) == 2 and all(map(_number, value)) and value[0] <= value[1]):
            raise VariantError(f"{letter}: {key} als Bereich [von, bis] mit von ≤ bis")
        if not all(_number(x) and lo <= x <= hi for x in values) or (key in INTS and not all(isinstance(x, int) for x in values)):
            raise VariantError(f"{letter}: {key}={value} außerhalb {lo}–{hi}")
    elif key in CHOICES:
        values = value if isinstance(value, list) else [value]
        if not values or any(x not in CHOICES[key] for x in values) or len(set(values)) != len(values):
            raise VariantError(f"{letter}: {key} nur aus {', '.join(CHOICES[key])} (ohne Doppelte)")
    else:
        raise VariantError(f"{letter}: unbekannter Parameter {key}")


def seed(sid: str) -> str:
    """Fester Seed eines Blatts: SHA256 über Blatt-ID und Linie (16 Hexziffern; Linie = Kennbuchstabe der ID)."""
    letter, _ = parse_sheet(sid)
    return hashlib.sha256(f"formgenv2-variant|{sid}|{letter}".encode()).hexdigest()[:16]


def _uniform(seed_hex: str, key: str) -> float:
    return int(hashlib.sha256(f"{seed_hex}|{key}".encode()).hexdigest()[:16], 16) / 2.0 ** 64


def allowed(key: str, values, num: str) -> list:
    """Bausteinauswahl, die für den Typ zulässig ist (Präzisionsregel: Zielfernrohr nur 03/09/11, dort nur Zielfernrohre)."""
    if key != "sight":
        return list(values)
    keep = SCOPES if num in PRECISION else HOLO
    return [v for v in values if v in keep]


def resolve(params: dict, sid: str) -> tuple[dict, dict]:
    """Registerparameter eines Blatts → (feste Werte, Ziehungen). Bereiche werden aus dem Seed gezogen und gerundet
    (Zahlen auf 0,001); eine Auswahlliste ohne zulässigen Baustein für den Typ ergibt None (Schritt entfällt)."""
    s, (_, num) = seed(sid), parse_sheet(sid)
    values, draws = {}, {}
    for key, value in params.items():
        if key == "drop":
            values[key] = list(value)
        elif key in PARAMS or key in INTS:
            if isinstance(value, list):
                lo, hi = value
                u = _uniform(s, key)
                value = lo + int(u * (hi - lo + 1)) if key in INTS else round(lo + u * (hi - lo), 3)
                draws[key] = value
            values[key] = value
        else:
            pool = allowed(key, value if isinstance(value, list) else [value], num)
            pick = pool[int(_uniform(s, key) * len(pool))] if pool else None
            if isinstance(value, list) and len(value) > 1:
                draws[key] = pick
            values[key] = pick
    return values, draws


def _skins() -> set[str]:
    with (ROOT / "skins.toml").open("rb") as stream:
        return set(tomllib.load(stream)["skins"])


def load(path: Path = REGISTRY) -> list[dict]:
    with Path(path).open("rb") as stream:
        data = tomllib.load(stream)
    if data.get("schema") != SCHEMA:
        raise VariantError(f"Variantenregister: schema {SCHEMA} erwartet")
    entries = data.get("variants", [])
    check(entries, _skins())
    for v in entries:
        v.setdefault("skin", "standard"); v.setdefault("params", {}); v.setdefault("types", list(TYPES))
        v.setdefault("base", "standard")
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
        return json.dumps(value, ensure_ascii=False)   # JSON-Escapes (\n, \", \uXXXX) sind gültige TOML-Basic-Strings
    if isinstance(value, list):
        return "[" + ", ".join(_toml(x) for x in value) + "]"
    return repr(value)


def new(letter, name, idea, since, skin="standard", params=None, path: Path = REGISTRY, base="standard") -> dict:
    entries = load(path)
    entry = {"letter": letter, "name": name, "idea": idea, "since": since, "skin": skin, "base": base, "params": params or {}}
    check(entries + [entry], _skins())
    text = Path(path).read_text()
    block = (f'\n[[variants]]\nletter = {_toml(letter)}\nname = {_toml(name)}\nidea = {_toml(idea)}\n'
             f'since = {_toml(since)}\nskin = {_toml(skin)}\n' + (f'base = {_toml(base)}\n' if base != "standard" else "")
             + '[variants.params]\n'
             + "".join(f"{k} = {_toml(v)}\n" for k, v in (params or {}).items()))
    candidate = text.rstrip("\n") + "\n" + block
    parsed = tomllib.loads(candidate)   # erst prüfen, dann schreiben: ein Fehler lässt das Register unverändert
    check(parsed.get("variants", []), _skins())
    Path(path).write_text(candidate)
    return entry


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    n = sub.add_parser("new")
    n.add_argument("letter"); n.add_argument("name"); n.add_argument("idea")
    n.add_argument("--since", default=None); n.add_argument("--skin", default="standard")
    n.add_argument("--base", default="standard", choices=BASES)
    n.add_argument("--param", action="append", default=[], metavar="KEY=JSON", help="z. B. front=1.1, mag=[0.8,0.9], sight='[\"zinken\"]'")
    a = p.parse_args(argv)
    if a.cmd == "list":
        for v in load():
            print(f'{v["letter"]} · {v["name"]:16} {v["skin"]:9} {v["base"]:8} {v["params"]}  {v["idea"]}')
        return 0
    from . import __version__
    try:
        params = {k: json.loads(v) for k, v in (item.split("=", 1) for item in a.param)}
        e = new(a.letter, a.name, a.idea, a.since or ".".join(__version__.split(".")[:2]), a.skin, params, base=a.base)
    except (VariantError, ValueError) as error:
        print(f"abgelehnt: {error}", file=sys.stderr)
        return 1
    print(f"eingetragen: {e['letter']} · {e['name']} → Blätter B{e['letter']}01 … B{e['letter']}17")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
