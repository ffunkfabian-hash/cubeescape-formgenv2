"""Stufe `viewer`: baut die Website unter out/ (formgen/web/site.py); keine Rasteraufrufe, Blätter bleiben unberührt."""
from __future__ import annotations
import argparse
from pathlib import Path
from .web import site


def items(out):
    return site.collect(out)


def build(out, cache, force=False):
    return site.build(out, cache, force=force)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'out');p.add_argument('--cache',type=Path,default=Path.home()/'Library/Caches/CubeEscapeFormgen/artifacts');p.add_argument('--force',action='store_true');a=p.parse_args()
    results=build(a.out,a.cache,force=a.force);print(f'{sum(r.built for r in results)} Website-Dateien gebaut, {sum(not r.built for r in results)} aus dem Cache')
