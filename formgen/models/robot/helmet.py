"""Kopfvarianten (0.14 Kitbash): Helmgruppen, Verformung je Gruppe und Aufsatzteile für RA01 (Helm H 80) und RA02 (gemessener Kopf).

Schnittstelle: PARAMS['helmet'] beider Typen ist eine Kopie von NEUTRAL; ra01/ra02 bekommen die fertigen Kopfteile in Weltmaßen (mm, f/u/x)
und geben sie verformt und ergänzt zurück. Mit NEUTRAL kommt dieselbe Liste unverändert zurück (RA01/RA02 bytegleich).
"""
from __future__ import annotations

NEUTRAL: dict = {}


def ra01(parts, params, frames):
    """Helmteile von RA01 (aus helmet_h80.json, schon in Weltmaßen) → verformt und ergänzt; frames wie roboterbasic_01.rig_of."""
    if params['helmet'] == NEUTRAL:
        return parts
    raise NotImplementedError('Kopfvarianten RA01: folgt in 0.14')


def ra02(parts, params, frames):
    """Alle Teile von RA02 (Weltmaßen); verformt und ergänzt nur die Teile mit assembly == 'head'. frames wie roboterbasic_02._frames."""
    if params['helmet'] == NEUTRAL:
        return parts
    raise NotImplementedError('Kopfvarianten RA02: folgt in 0.14')
