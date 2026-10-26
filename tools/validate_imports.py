#!/usr/bin/env python3
"""Prüft archivierte v1-Geo-Exporte ohne Import irgendeines v1-Modells."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from formgen.geo import load
base=Path(sys.argv[1]) if len(sys.argv)>1 else Path.home()/'Library/Caches/CubeEscapeFormgen/imports/v1'
paths=sorted(base.glob('*.geo.json'))
if not paths: raise SystemExit('Keine Geo-Dateien')
counts={};fail=[]
for p in paths:
 try:
  d=load(p);kind=d['info']['kind'];counts[kind]=counts.get(kind,0)+1
 except Exception as e:fail.append(f'{p.name}: {e}')
print(json.dumps({'geprüft':len(paths),'arten':counts,'fehler':fail},ensure_ascii=False))
sys.exit(bool(fail))
