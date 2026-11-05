"""Deterministic offline release dry run; validate the actual packaged references."""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

from . import __version__, geo, spec, wspec
from .cache import canonical
from .web import site


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value is not None and key in ('src', 'href', 'poster'):
                self.links.append(value)
            if value is not None and key == 'srcset':
                self.links.extend(v.strip().split()[0] for v in value.split(',') if v.strip())


def _html_links(raw):
    text = raw.decode('utf-8')
    parser = _Links();parser.feed(text)
    return parser.links + re.findall(r'url\(\s*[\'"]?([^\'"\)\s]+)', text)


def _resolve(owner, link):
    parsed = urlsplit(link)
    if parsed.scheme == 'data': return None
    if parsed.scheme or parsed.netloc:
        raise ValueError(f'Offline-Release mit externer Referenz: {owner}: {link}')
    path = unquote(parsed.path)
    if not path: return None
    if path.startswith('/') or '\\' in path:
        raise ValueError(f'Absolute/ungültige Paketreferenz: {owner}: {link}')
    target = posixpath.normpath(posixpath.join(posixpath.dirname(owner), path))
    if target == '..' or target.startswith('../'):
        raise ValueError(f'Paketreferenz verlässt Release: {owner}: {link}')
    return target


def _safe_json_paths(value, owner):
    """Provenance may reference repo files, but must never leak machine paths."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('path', 'file') and isinstance(item, str):
                if item.startswith(('/', '~')) or '\\' in item or re.match(r'^[A-Za-z]:',item):
                    raise ValueError(f'Absoluter Herkunfts-/Referenzpfad: {owner}: {item}')
                if '..' in PurePosixPath(item).parts:
                    raise ValueError(f'Unsicherer Herkunfts-/Referenzpfad: {owner}: {item}')
            _safe_json_paths(item,owner)
    elif isinstance(value, list):
        for item in value: _safe_json_paths(item,owner)


def _dependencies(name, raw):
    """Return executable/deliverable references; catalog source paths are provenance."""
    if name.endswith(('.html','.css')):
        return [(target,None) for link in _html_links(raw) if (target := _resolve(name,link))]
    if not name.endswith('.json'): return []
    data = json.loads(raw)
    json.dumps(data,allow_nan=False)
    _safe_json_paths(data,name)
    refs = []
    if name.startswith('geo/'):
        geo.validate(data)
        refs += [('specs/'+geo._local_name(r['file']),r['sha256']) for r in geo._references(data)]
    elif name.startswith('specs/'):
        if data.get('format') in ('cubeescape-design/weapon-spec','cubeescape-design/sight-spec'):
            spec.validate(data)
        elif data.get('format') == wspec.FORMAT:
            wspec.migrate(data)
            return refs
        elif data.get('format') == site.ROBOT_FORMAT:
            site.robot_spec(data)
            return refs
        elif data.get('format') != 'cubeescape-formgen/figure-spec':
            raise ValueError(f'Unbekannter Spec-Vertrag: {name}')
        sheet_file = data.get('sheet',{}).get('file')
        if sheet_file: refs.append(('sheets/'+geo._local_name(sheet_file),None))
        sight = data.get('sight',{}).get('sight_spec')
        if sight: refs.append(('specs/'+geo._local_name(sight['file']),sight.get('sha256')))
    return refs


def _verify(files, ids):
    for name, raw in files.items():
        for target, digest in _dependencies(name,raw):
            if target not in files:
                raise ValueError(f'Release-Referenz fehlt: {name} → {target}')
            if digest and hashlib.sha256(files[target]).hexdigest() != digest:
                raise ValueError(f'Release-Referenz SHA stimmt nicht: {name} → {target}')
    links = {_resolve('index.html',link) for link in _html_links(files['index.html'])}
    for page in sorted(l for l in links if l and '/' not in l and l.endswith('.html') and l != 'index.html'):
        links |= {_resolve(page,link) for link in _html_links(files[page])}   # Waffen- und Roboterseite hängen an der Navigation
    viewer_models = {m.group(1) for link in links if link and (m := re.fullmatch(r'sheets/([A-Za-z][A-Za-z0-9_-]*)\.dc\.html',link))}
    if viewer_models != set(ids):
        raise ValueError('Viewer-Modellauswahl stimmt nicht mit Release überein')
    for sid in ids:
        if f'geo/{sid}.geo.json' not in files:   # Waffen- und Roboterblatt: Blatt-Spec statt Geo-Vertrag
            specification = json.loads(files[f'specs/{sid}.spec.json'])
            if specification.get('format') not in (wspec.FORMAT,site.ROBOT_FORMAT) or specification.get('id') != sid:
                raise ValueError(f'Waffenblatt-Spec widerspricht Modell-ID: {sid}')
            if f'sheets/{sid}.dc.html' not in links or f'previews/{sid}.webp' not in links:
                raise ValueError(f'Viewer enthält Modell nicht vollständig: {sid}')
            continue
        geometry = json.loads(files[f'geo/{sid}.geo.json'])
        model_info = geometry.get('sheet',geometry.get('figure',{}))
        if model_info.get('id') != sid: raise ValueError(f'Geo-Modell-ID widerspricht Dateiname: {sid}')
        source_field = {'weapon':'weapon_spec','sight':'sight_spec','figure':'figure_spec'}[model_info['kind']]
        if geometry['source'][source_field]['file'] != f'{sid}.spec.json':
            raise ValueError(f'Geo-Hauptspec widerspricht Modell-ID: {sid}')
        specification = json.loads(files[f'specs/{sid}.spec.json'])
        spec_info = specification.get('sheet',specification.get('figure',{}))
        if spec_info.get('id') != sid: raise ValueError(f'Spec-Modell-ID widerspricht Dateiname: {sid}')
        if f'sheets/{sid}.dc.html' not in links or f'previews/{sid}.webp' not in links:
            raise ValueError(f'Viewer enthält Modell nicht vollständig: {sid}')


def _default_ids(out):
    """Alle Specs; liegen Blätter der Website vor, nur diese: alte Formate (R01, KG02 …) stehen nicht mehr im Viewer."""
    specs = {p.name.removesuffix('.spec.json'):json.loads(p.read_bytes()).get('format') for p in (out/'specs').glob('*.spec.json')}
    current = [sid for sid,kind in specs.items() if kind in (wspec.FORMAT,site.ROBOT_FORMAT)]
    return sorted(current or specs)


def _write_zip(target, contents):
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name, raw in sorted(contents.items()):
            info = zipfile.ZipInfo(name,(2026,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info,raw,compresslevel=6)


def package(out, destination, ids=None):
    out, destination = Path(out).resolve(), Path(destination)
    ids = sorted(set(ids)) if ids else _default_ids(out)
    if not ids: raise ValueError('Keine Modelle für Release-Probelauf')
    pending = ['index.html']
    for sid in ids:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',sid): raise ValueError('Ungültige Modell-ID')
        pending += [f'specs/{sid}.spec.json',f'sheets/{sid}.dc.html',f'previews/{sid}.webp']
        robot = re.fullmatch(r'R[A-Z]\d\d',sid)   # Roboterblätter führen keine Prompts
        if not robot or (out/f'prompts/{sid}.prompts.json').is_file():
            pending.append(f'prompts/{sid}.prompts.json')
        if not robot and not re.fullmatch(r'B[A-Z]\d\d',sid):   # Waffen- und Roboterblätter liefern Spec statt Geo
            pending.append(f'geo/{sid}.geo.json')
        pending += [p.relative_to(out).as_posix() for p in sorted((out/'views'/sid).glob('*.png'))]
    files = {}
    while pending:
        name = pending.pop()
        if name in files: continue
        path = out/name
        if not path.resolve().is_relative_to(out): raise ValueError(f'Release-Datei verlässt out: {name}')
        if not path.is_file(): raise ValueError(f'Release unvollständig: {name}')
        raw = path.read_bytes()
        files[name] = raw
        pending += [target for target,_ in _dependencies(name,raw)]
    _verify(files,ids)
    records = {name:hashlib.sha256(raw).hexdigest() for name,raw in sorted(files.items())}
    manifest = dict(format='formgen/release-manifest',version=__version__,status='local_dry_run',models=ids,sha256=records)
    destination.mkdir(parents=True,exist_ok=True)
    target = destination/f'formgen-v{__version__}-dry-run.zip'
    contents = dict(files,**{'release-manifest.json':canonical(manifest)+b'\n'})
    _write_zip(target,contents)
    with zipfile.ZipFile(target) as archive:
        if archive.testzip(): raise ValueError('ZIP-Prüfung fehlgeschlagen')
        if set(archive.namelist()) != set(contents) or len(archive.namelist()) != len(contents):
            raise ValueError('ZIP-Dateiliste weicht ab')
        packed = {name:archive.read(name) for name in records}
        for name, digest in records.items():
            if hashlib.sha256(packed[name]).hexdigest() != digest: raise ValueError(f'ZIP-Inhalt weicht ab: {name}')
        if archive.read('release-manifest.json') != contents['release-manifest.json']:
            raise ValueError('ZIP-Manifest weicht ab')
        _verify(packed,ids)
    return dict(path=str(target),models=ids,files=len(files),bytes=target.stat().st_size,
                sha256=hashlib.sha256(target.read_bytes()).hexdigest(),status='local_dry_run')


def package_3d(out, destination, ids=None):
    """3D-Daten als eigenes Zip neben dem Hauptzip (etwa 280 MB): in denselben Ordner auspacken, die 3D-Seite findet sie dort."""
    out, destination = Path(out).resolve(), Path(destination)
    ids = sorted(set(ids)) if ids else sorted(p.stem for p in (out/'models3d').glob('*.js'))
    if not ids: raise ValueError('Keine 3D-Daten für Release-Probelauf')
    files = {}
    for sid in ids:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',sid): raise ValueError('Ungültige Modell-ID')
        path = out/'models3d'/f'{sid}.js'
        if not path.is_file() or not path.resolve().is_relative_to(out): raise ValueError(f'3D-Daten fehlen: {sid}')
        raw = path.read_bytes()
        if not raw.startswith(f'window.formgenModel={{"id": "{sid}",'.encode()):
            raise ValueError(f'3D-Daten widersprechen Modell-ID: {sid}')
        files[f'models3d/{sid}.js'] = raw
    records = {name:hashlib.sha256(raw).hexdigest() for name,raw in sorted(files.items())}
    manifest = dict(format='formgen/release-manifest',version=__version__,status='local_dry_run',models=ids,sha256=records)
    destination.mkdir(parents=True,exist_ok=True)
    target = destination/f'formgen-v{__version__}-3d-dry-run.zip'
    _write_zip(target,dict(files,**{'release-manifest-3d.json':canonical(manifest)+b'\n'}))
    with zipfile.ZipFile(target) as archive:
        if archive.testzip(): raise ValueError('ZIP-Prüfung fehlgeschlagen')
        for name, digest in records.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest: raise ValueError(f'ZIP-Inhalt weicht ab: {name}')
    return dict(path=str(target),models=ids,files=len(files),bytes=target.stat().st_size,
                sha256=hashlib.sha256(target.read_bytes()).hexdigest(),status='local_dry_run')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ids',nargs='*')
    parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'out')
    parser.add_argument('--destination',type=Path,default=Path.home()/'Library/Caches/CubeEscapeFormgen/releases')
    parser.add_argument('--models3d',action='store_true',help='3D-Daten als eigenes Zip statt des Hauptzips')
    args = parser.parse_args()
    print(json.dumps((package_3d if args.models3d else package)(args.out,args.destination,args.ids),ensure_ascii=False))
