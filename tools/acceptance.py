"""Silhouetten-Abnahme: allgemeine Grenzen plus begründete Ausnahmen je Referenz.

Eine Ausnahme greift nur, wenn Figur, Ansicht, Metrik (und Band) und der SHA der
Referenzmaske übereinstimmen. Neue Masken verlieren die Ausnahme automatisch.
"""
import json
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/'docs/acceptance-exceptions.json'


def load(path=DATA):
    return json.loads(Path(path).read_text())


def _exception(doc, figure, view, mask_sha, metric, band=None):
    for e in doc['exceptions']:
        if (e['figure'],e['view'],e['metric'])!=(figure,view,metric):continue
        if e['reference_mask_sha256']!=mask_sha:continue
        if metric=='band' and e['band']!=band:continue
        return e
    return None


def judge(figure, view, iou, bands, mask_sha, doc=None):
    """Return pass flags and the exceptions actually used for one view."""
    doc=doc or load();g=doc['general'];used=[]
    e=_exception(doc,figure,view,mask_sha,'iou')
    iou_min=e['iou_min'] if e else g['iou_min']
    iou_pass=iou>=iou_min
    if e and iou<g['iou_min']:used.append(e)
    band_pass=True
    for b in bands:
        e=_exception(doc,figure,view,mask_sha,'band',b['from_bottom'])
        lo,hi=(e['band_ratio_min'],e['band_ratio_max']) if e else (g['band_ratio_min'],g['band_ratio_max'])
        r=b['ratio'];ok=r is not None and lo<=r<=hi
        band_pass&=ok
        if e and r is not None and not g['band_ratio_min']<=r<=g['band_ratio_max']:used.append(e)
    return {'iou_pass':iou_pass,'bands_pass':band_pass,'iou_min':iou_min,
            'exceptions_used':[{k:x[k] for k in ('metric','reason','source')}|({'band':x['band']} if x['metric']=='band' else {}) for x in used]}
