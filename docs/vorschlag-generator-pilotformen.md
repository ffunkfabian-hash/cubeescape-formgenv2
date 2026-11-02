# Vorschlag an 0.4 „Mosaic“: Generator für die Formen der Spiel-Piloten

Status: Vorschlag aus 0.3 „Forge“ (02.11.2026), **nicht eingecheckt** – `formgen/generator.py` gehört 0.4 (Nutzerentscheid 02.11.2026).
Der Patch unten lief in 0.3 kurz auf allen 51 Blättern mit den v2.1-Piloten als Grundform (reines Python, ohne v2-Geometrie);
die Formstudien-Blätter bleiben damit unverändert (Formstudien haben weder `multi` noch `cuts`, `tests.test_ballon_generator`
und `tests.test_pipeline` blieben grün).

## Antwort auf die Frage aus 0.4: Baut BALLONs Kit `xprof`?

Ja. `tools/kit_pilot_check.py` baut alle 16 v2.1-Piloten (BASIC-01…15, T01) unverändert mit BALLONs `tools/blender_build.py`
am Pin `dcdda60` und vergleicht je Objekt mit BALLONs Unity-Export (`unity/Assets/Ballon/Generated/ego.json`,
`weapons[].mesh_bounds`): **16/16 gebaut, jedes Objekt dreiecksgleich** (z. B. BASIC-01-v2.1 72 Objekte, 33 450 Dreiecke).
14 der 16 Piloten enthalten `xprof` (als Teil, in `multi` oder als Durchbruch), T01 und BASIC-05 nicht. Auch `multi`, `tube`,
`text`, `xbox`, `frame` und `cuts` baut das Kit. Bericht: `~/Library/Caches/CubeEscapeFormgen2/0.3/belege/kit_pilot_check.json`.
Folgerung: Für Piloten-Grundformen ist der Kit-Weg (formgen/asset.py) die Geometrie; v2s eigene Geometrie bräuchte alle diese Formen neu.

## Was der Generator für Piloten zusätzlich braucht

1. `_f_values`/`_map_f` für `multi` (Unterformen, ohne `shape` = Quader), `xprof` (`f0`/`f1`; `pts` sind (x,u)!), `tube` (`path`),
   `text` (`f`) und für Durchbrüche `cuts` (wandern mit dem Teil). Kurze Unterformen/Durchbrüche (< `SHORT_MM`) über dem Schnitt
   werden ganz nach ihrer Mitte verschoben statt verzerrt; beim Spiegeln (`_mirror`) wird jeder Punkt abgebildet (`rigid=False`).
2. `drop` schützt zusätzlich bewegte Teile (`move`): sie tragen Mechanik, `EGO_LIVE`-Teile und Aktionen der Spielwaffe.
3. Wahl der Grundform: neuester Pilot `basic/pilot/wNN_*_vK.py` (K als Ziffernfolge vergleichen: v21 = (2,1) > v2 = (2,), v3 > v21),
   sonst Formstudie (BASIC-16/17) – in 0.3 als `formgen/ballon_kit.pilot_file`. Der Daten-Schnappschuss von `ballon.py`
   (`PATHS`) enthält `basic/pilot` noch nicht.
4. Befund mit Piloten-Grundform: Linie C `drop vent_*` trifft nur noch BASIC-08 (`vent_rib`) – die Piloten führen Lüftung als
   Durchbrüche. Stauchen ist bei 11 der 17 C-Blätter begrenzt (`limited`), weil die dichteren Piloten weniger freie Zone haben.
   Gemessene Deltas (front/rear mm): BB01 +92,4/+17,9 · BC01 −70,2/−26,8 (begrenzt) · BC05 −2,5 (begrenzt) · BC06 −7,0/0 (begrenzt).

## Patch (gegen `0b6a122`, `formgen/generator.py`)

`variant_model` am Ende war der Einstieg der damaligen Asset-Stufe (BALLON-Vokabular ohne v2-Anpassungen); in 0.3 erledigt das jetzt
`formgen/asset.kit_model` aus dem Ergebnis von `generator.generate`.

```diff
diff --git a/formgen/generator.py b/formgen/generator.py
index 391c4b8..e180be6 100644
--- a/formgen/generator.py
+++ b/formgen/generator.py
@@ -7,6 +7,9 @@ Keine eigene Grundgeometrie. Erlaubte Eingriffe (docs/generator.md):
 Ein Schnitt `at` trennt: Teile ganz jenseits werden verschoben, lange Teile über dem Schnitt (Gehäuse, Lauf,
 Schiene) gedehnt bzw. gestaucht, kurze Teile werden nie verzerrt. Gestaucht wird höchstens bis zur freien Zone
 hinter dem Schnitt; Begrenzungen stehen im Bericht. Alle Zahlen in mm im BALLON-Rahmen (f vorn, u oben, x links).
+Formen der Spiel-Piloten (0.3): `multi`, `xprof`, `tube`, `text` und Durchbrüche `cuts` folgen dem Schnitt; ihre kurzen
+Unterformen (< SHORT_MM) werden ganz verschoben, nie verzerrt. `variant_model` liefert das Ergebnis im BALLON-Vokabular für die
+Asset-Stufe, `generate` das v2-Autorenmodell für die Blätter.
 """
 from __future__ import annotations
 
@@ -25,26 +28,57 @@ STOCK_MARGIN = 0.2            # Annahme: Schnitt nicht in den äußeren 20 % des
 # ------------------------------------------------------------------ f-Koordinaten je Form
 
 def _f_values(p):
-    s = p["shape"]
+    s = p.get("shape", "box")       # Teile in `multi` und `cuts` ohne Form sind Quader (BALLON kit.build_shape)
     if s in ("prof", "plan"):
         return [q[0] for q in p["pts"]]
-    if s in ("box", "frame", "xbox"):
+    if s in ("box", "frame", "xbox", "xprof"):
         return [p["f0"], p["f1"]]
     if s == "cyl":
         return [p["a0"], p["a1"]] if p["axis"] == "f" else [p["c"][0]]
-    raise ValueError(f"{p['id']}: Form {s} im Generator nicht unterstützt")
+    if s == "multi":
+        return [f for q in p["items"] for f in _f_values(q)]
+    if s == "tube":
+        return [q[0] for q in p["path"]]
+    if s == "text":
+        return [p["f"]]
+    raise ValueError(f"{p.get('id', '?')}: Form {s} im Generator nicht unterstützt")
 
 
-def _map_f(p, fn):
-    s = p["shape"]
+def _map_shape(p, fn, rigid=True):
+    s = p.get("shape", "box")
     if s in ("prof", "plan"):
         p["pts"] = [(fn(q[0]), *q[1:]) for q in p["pts"]]
-    elif s in ("box", "frame", "xbox"):
+    elif s in ("box", "frame", "xbox", "xprof"):
         p["f0"], p["f1"] = fn(p["f0"]), fn(p["f1"])
-    elif p["axis"] == "f":
-        p["a0"], p["a1"] = fn(p["a0"]), fn(p["a1"])
+    elif s == "cyl":
+        if p["axis"] == "f":
+            p["a0"], p["a1"] = fn(p["a0"]), fn(p["a1"])
+        else:
+            p["c"] = (fn(p["c"][0]), *p["c"][1:])
+    elif s == "multi":
+        for q in p["items"]:
+            _map_unit(q, fn, rigid)
+    elif s == "tube":
+        p["path"] = [(fn(q[0]), *q[1:]) for q in p["path"]]
+    elif s == "text":
+        p["f"] = fn(p["f"])
+    for q in p.get("cuts") or ():
+        _map_unit(q, fn, rigid)
+
+
+def _map_unit(q, fn, rigid):
+    """Unterform (Teil von `multi`, Durchbruch). Beim Dehnen (`rigid`) werden kurze Unterformen über dem Schnitt ganz nach ihrer
+    Mitte verschoben, nie verzerrt (wie kurze Teile); Spiegeln bildet jeden Punkt ab."""
+    lo, hi = min(_f_values(q)), max(_f_values(q))
+    if rigid and hi - lo < SHORT_MM and (fn(lo) - lo) != (fn(hi) - hi):
+        d = fn((lo + hi) / 2) - (lo + hi) / 2
+        _map_shape(q, lambda f: f + d)
     else:
-        p["c"] = (fn(p["c"][0]), *p["c"][1:])
+        _map_shape(q, fn, rigid)
+
+
+def _map_f(p, fn, rigid=True):
+    _map_shape(p, fn, rigid)
     move = p.get("move")
     if move:
         for key in POINT_KEYS:
@@ -62,7 +96,7 @@ def _extent(p):
 
 def _mirror(model):
     for p in model["PARTS"]:
-        _map_f(p, lambda f: -f)
+        _map_f(p, lambda f: -f, rigid=False)
     for a in model["ANCHORS"].values():
         a["at"] = (-a["at"][0], *a["at"][1:])
 
@@ -167,7 +201,9 @@ def stretch_rear(model, factor):
 
 
 def drop(model, patterns):
-    keep_ids = {a["part"] for a in model["ANCHORS"].values()} | {p.get("parent_part") for p in model["PARTS"]}
+    # Anker-, Eltern- und bewegte Teile bleiben (bewegte Teile tragen Mechanik, Ego-Live-Teile und Aktionen der Spielwaffe)
+    keep_ids = ({a["part"] for a in model["ANCHORS"].values()} | {p.get("parent_part") for p in model["PARTS"]} |
+                {p["id"] for p in model["PARTS"] if p.get("move")})
     dropped, protected = [], []
     for p in list(model["PARTS"]):
         if any(fnmatch.fnmatchcase(p["id"], pat) for pat in patterns):
@@ -245,6 +281,31 @@ def generate(data, variant, num, source):
     return author, report
 
 
+def variant_model(data, variant):
+    """Asset-Stufe (0.3): BALLON-Datensätze nach den Variantenparametern, im BALLON-Vokabular für `basic/kit.py`.
+
+    Anders als `generate` ohne v2-Anpassungen (Hohlkegel, leere Baugruppen): Baseline ist bit für bit BALLONs Modell, wie es
+    BALLON selbst in Blender baut. ACTIONS verlieren nur Schlüssel entfernter Teile."""
+    model = {k: copy.deepcopy(data[k]) for k in ("META", "PARTS", "ASSEMBLIES", "ANCHORS")}
+    model["ACTIONS"] = copy.deepcopy(data.get("ACTIONS") or {})
+    params = variant.get("params", {})
+    ops = []
+    if "drop" in params:
+        ops.append(drop(model, params["drop"]))
+    if "front" in params:
+        ops.append(stretch_front(model, params["front"]))
+    if "rear" in params:
+        ops.append(stretch_rear(model, params["rear"]))
+    ids = {p["id"] for p in model["PARTS"]}
+    missing = sorted(n for n, a in model["ANCHORS"].items() if a["part"] not in ids)
+    if missing:
+        raise ValueError(f"Anker verweisen auf entfernte Teile: {missing}")
+    for action in model["ACTIONS"].values():
+        if isinstance(action.get("keys"), dict):
+            action["keys"] = {k: v for k, v in action["keys"].items() if k in ids}
+    return model, ops
+
+
 def build(variant, num, snap=None, source=None):
     snap = snap or ballon.snapshot()
     source = source or ballon.source(snap, num)
```
