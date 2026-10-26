"""Zwei Teile, ein Anker. Sämtliche Maße: Annahme für Schnittstellentest, mm."""
INFO = {"id": "MINI", "kind": "weapon", "name_de": "Schnittstellenprobe", "provenance": {"kind": "Annahme", "source": "Zweiteiliges Testmodell, keine Produktmaße"}}
ASSEMBLIES = [{"id": "body", "de": "Körper"}]
PARTS = [
    {"id": "shell", "assembly": "body", "shape": "box", "role": "shell", "label": "Schale", "f0": 0, "f1": 100, "u0": 0, "u1": 40, "w": 30, "bevel": 0},
    {"id": "grip", "assembly": "body", "shape": "box", "role": "graphite", "label": "Griff", "f0": 10, "f1": 30, "u0": -60, "u1": 0, "w": 20, "bevel": 0},
]
ANCHORS = {"Socket_Hand": {"at": [20, -30, 0], "part": "grip", "source": "Annahme: Mitte des Testgriffs"}}
POSES = {}
