"""Three.js für file:// packen: aus dem npm-Tarball eine klassische Skriptdatei ohne node und ohne fremdes Werkzeug.

Nur beim Wechsel der Three.js-Version von Hand aufrufen; der Website-Bau liest allein das Ergebnis:
    curl -O https://registry.npmjs.org/three/-/three-<Version>.tgz
    python -m formgen.web.vendor.pack_three three-<Version>.tgz formgen/web/vendor --integrity sha512-…

Chrome und Safari laden ES-Module unter file:// nicht, und das npm-Paket liefert seit r18x keine .min.js mehr. Darum wird
jedes Modul in eine eigene Funktion gesetzt (Import = Destrukturierung, Export = Rückgabeobjekt). Kommentare und Füllzeichen
fallen weg, Zeilenumbrüche bleiben (kein ASI-Risiko); Zeichenketten, Vorlagen und Regex bleiben bytegleich.
Bewusst ohne Umbenennen und Tree-Shaking: das wäre ein eigener Minifier, die Datei ist auch so nur eine Zeile im Repo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tarfile
from pathlib import Path

GLOBAL = 'FormgenThree'
# Reihenfolge = Abhängigkeiten; je Modul Dateipfad im Paket und Schlüssel, unter dem es importiert wird.
MODULES = (('build/three.core.js', './three.core.js'),
           ('build/three.module.js', 'three'),
           ('examples/jsm/utils/BufferGeometryUtils.js', '../utils/BufferGeometryUtils.js'),
           ('examples/jsm/utils/SkeletonUtils.js', '../utils/SkeletonUtils.js'),
           ('examples/jsm/loaders/GLTFLoader.js', 'GLTFLoader'),
           ('examples/jsm/controls/OrbitControls.js', 'OrbitControls'),
           ('examples/jsm/environments/RoomEnvironment.js', 'RoomEnvironment'))
_REGEX_BEFORE = set('(,=:[!&|?{};+-*%<>~^\n')
_REGEX_WORDS = {'return', 'typeof', 'case', 'in', 'of', 'delete', 'void', 'throw', 'new', 'do', 'else', 'yield', 'await'}


def _regex_end(src: str, start: int) -> int:
    """Index hinter einem Regex-Literal ab `/` (Zeichenklassen dürfen `/` enthalten)."""
    i, in_class = start + 1, False
    while True:
        c = src[i]
        if c == '\\':
            i += 2
            continue
        if c == '\n':
            raise ValueError(f'Regex-Literal ohne Ende bei {start}')
        if c == '[':
            in_class = True
        elif c == ']':
            in_class = False
        elif c == '/' and not in_class:
            i += 1
            while src[i].isalpha():
                i += 1
            return i
        i += 1


def _string_end(src: str, start: int) -> int:
    i, quote = start + 1, src[start]
    while src[i] != quote:
        i += 2 if src[i] == '\\' else 1
    return i + 1


def _template_end(src: str, start: int) -> int:
    """Index hinter einer Vorlage; `${…}`-Ausdrücke dürfen Klammern, Zeichenketten und Vorlagen enthalten."""
    i = start + 1
    while src[i] != '`':
        if src[i] == '\\':
            i += 2
        elif src.startswith('${', i):
            i, depth = i + 2, 1
            while depth:
                c = src[i]
                if c in '\'"':
                    i = _string_end(src, i)
                elif c == '`':
                    i = _template_end(src, i)
                else:
                    depth += (c == '{') - (c == '}')
                    i += 1
        else:
            i += 1
    return i + 1


def _tidy(code: str) -> str:
    """Nur Code, nie Literale: Einrückung, Leerzeilen und Leerzeichen an Klammern, Komma und Semikolon entfernen."""
    code = re.sub(r'\s*\n\s*', '\n', code)
    code = re.sub(r'[ \t]+', ' ', code)
    return re.sub(r' ?([()\[\]{},;]) ?', r'\1', code)


def strip(src: str) -> str:
    """Kommentare und Füllzeichen entfernen; Literale bleiben bytegleich, jede Anweisung behält ihre Zeile."""
    out, code, i, n = [], [], 0, len(src)
    tail = ''                                   # letzte bedeutsame Zeichen, entscheidet Regex gegen Division

    def literal(end):
        nonlocal i, tail
        out.extend((_tidy(''.join(code)), src[i:end]))
        code.clear()
        i, tail = end, 'x'

    while i < n:
        c = src[i]
        if src.startswith('//', i):
            i = src.find('\n', i)
            i = n if i < 0 else i
        elif src.startswith('/*', i):
            i = src.index('*/', i) + 2
            code.append(' ')
        elif c in '\'"':
            literal(_string_end(src, i))
        elif c == '`':
            literal(_template_end(src, i))
        elif c == '/':
            word = re.search(r'[A-Za-z_$][\w$]*$', tail)
            if (tail[-1:] in _REGEX_BEFORE or not tail) if not word else word.group() in _REGEX_WORDS:
                literal(_regex_end(src, i))
            else:
                code.append(c); i += 1; tail = '/'
        else:
            code.append(c); i += 1
            if not c.isspace():
                tail = (tail + c)[-16:]
    out.append(_tidy(''.join(code)))
    return ''.join(out).strip() + '\n'


def _names(block: str):
    for item in filter(None, (x.strip() for x in block.split(','))):
        a, _, b = item.partition(' as ')
        yield a.strip(), (b or a).strip()


def wrap(source: str, key: str) -> str:
    """Modul in eine Funktion setzen; nur Import/Export auf Spalte 0 sind hier vorhanden (Test im Pack)."""
    body = strip(source)
    head, exports = [], []

    def imported(m):
        head.append('const{' + ','.join(a if a == b else f'{a}:{b}' for a, b in _names(m[1])) + f'}}=M[{json.dumps(m[2])}];')
        return ''

    def reexported(m):
        exports.extend(f'{b}:M[{json.dumps(m[2])}].{a}' for a, b in _names(m[1]))
        return ''

    def exported(m):
        exports.extend(a if a == b else f'{b}:{a}' for a, b in _names(m[1]))
        return ''

    body = re.sub(r"^import\s*\{([^}]*)\}\s*from\s*'([^']+)';?\n?", imported, body, flags=re.M)
    body = re.sub(r"^export\s*\{([^}]*)\}\s*from\s*'([^']+)';?\n?", reexported, body, flags=re.M)
    body = re.sub(r"^export\s*\{([^}]*)\};?\n?", exported, body, flags=re.M)
    if re.search(r'^(import|export)\b', body, flags=re.M):
        raise ValueError(f'Unbekannte Modulsyntax in {key}')
    return '(()=>{' + ''.join(head) + '\n' + body + f'M[{json.dumps(key)}]={{' + ','.join(exports) + '};})();\n'


def pack(tarball: Path, target: Path, integrity: str | None = None) -> dict:
    raw = tarball.read_bytes()
    with tarfile.open(tarball) as archive:
        read = lambda name: archive.extractfile('package/' + name).read()
        version = json.loads(read('package.json'))['version']
        license_text = read('LICENSE')
        sources = {name: read(name) for name, _ in MODULES}
    revision = re.search(rb"const REVISION = '(\d+)'", sources['build/three.core.js'])[1].decode()
    banner = (f'/*! three.js r{revision} ({version}) · MIT · Copyright 2010-2026 Three.js Authors · Lizenz: three-LICENSE.txt\n'
              ' * Aus dem npm-Paket gepackt mit formgen/web/vendor/pack_three.py; Herkunft und Hashes: three.json */\n')
    body = ''.join(wrap(sources[name].decode('utf-8'), key) for name, key in MODULES)
    text = (banner + '(()=>{"use strict";const M={};\n' + body +
            f'window.{GLOBAL}={{THREE:M.three,GLTFLoader:M.GLTFLoader.GLTFLoader,OrbitControls:M.OrbitControls.OrbitControls,'
            'RoomEnvironment:M.RoomEnvironment.RoomEnvironment};})();\n')
    name = f'three-{version}.pack.js'
    target.mkdir(parents=True, exist_ok=True)
    (target/name).write_text(text, encoding='utf-8')
    (target/'three-LICENSE.txt').write_bytes(license_text)
    record = {'package': 'three', 'version': version, 'revision': revision, 'license': 'MIT',
              'source': f'https://registry.npmjs.org/three/-/three-{version}.tgz', 'npm_integrity': integrity,
              'tarball_sha256': hashlib.sha256(raw).hexdigest(),
              'sources_sha256': {k: hashlib.sha256(v).hexdigest() for k, v in sources.items()},
              'file': name, 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'bytes': len(text.encode('utf-8')),
              'license_file': 'three-LICENSE.txt', 'license_sha256': hashlib.sha256(license_text).hexdigest()}
    (target/'three.json').write_text(json.dumps(record, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('tarball', type=Path)
    parser.add_argument('target', type=Path)
    parser.add_argument('--integrity', help='npm-Integrität aus der Lockdatei (sha512-…), wird mitgeschrieben und geprüft')
    args = parser.parse_args()
    if args.integrity:
        import base64
        digest = 'sha512-' + base64.b64encode(hashlib.sha512(args.tarball.read_bytes()).digest()).decode()
        if digest != args.integrity:
            raise SystemExit('Integrität des Tarballs stimmt nicht')
    print(json.dumps(pack(args.tarball, args.target, args.integrity), ensure_ascii=False, indent=1))
