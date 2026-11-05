# RoboterBasic-01

Basic-Typ 1 der Roboter, Blatt `RA01`, Grundform wie BA01 bei den Waffen. Heute steht nur er im Register; weitere Typen (`RA02`) und Linien sind im Aufbau vorgesehen.

```sh
.venv/bin/python -m formgen.robot                     # Geometrie, GLB, Spec, Prompts, Ansichten, Blatt, Vorschau (ohne --force nur Fehlendes)
.venv/bin/python -m formgen.viewer                    # Website neu bauen
.venv/bin/python -m formgen.robot.silhouette <referenz.glb> out/assets/RA01.glb
```

Bilder unter `./ce lock blender -- …` (CPU-Rasterizer). Blender wird nicht gebraucht: das GLB schreibt `formgen/robot/glb.py`.

## Quelle

| Datei | Inhalt | Herkunft |
|---|---|---|
| `formgen/models/robot/roboterbasic_01.py` | `INFO`, `PARTS`, `ASSEMBLIES`, `ANCHORS`, `POSES`, alle Maße in `PARAMS` | Vorgabe: BALLON 14bd78d, Studie `a_waechter` |
| `formgen/models/robot/{forms,shapes,body,arm}.py` | Formbaukasten, einmalig übertragen | BALLON 14bd78d, Kopf ohne BALLONs Helmstudien |
| `formgen/models/robot/rig.py` | Skelett, Armhaltung, Fingergelenke | BALLON `tools/robot_build.py`, `tools/ego_build.py`, ohne Blender |
| `formgen/models/robot/kit.py` | Formen → kit-Teile in Weltmaßen (mm, f/u/x) | eigen |
| `formgen/models/robot/helmet_h80.json` | Helm H 80, 58 Teile als Flächen im Kopfrahmen | gemessen aus `RoboterBasic-01.glb`, `tools/robot_helmet_transfer.py` |

Abbildung der BALLON-Formen: `loft`, `wrap`, `tube` → `surface`; `cyl` → `loft`; `box`, `plate`, `hull` → `hull`; Fugen (`cuts`) → `hull`-Schnitte. Das Feld `form` hält die Autorenform fest, `model.py` bleibt unverändert. Die Formparameter sind die Quelle, die ausgewerteten Punkte nur ihr Ergebnis; das gilt nicht für den Helm.

Grenzen: Fasen sind aus (`bevel = 0`), BALLON fast in Blender 1–2 mm. Der Helm ist die einzige Mesh-Übernahme; er folgt dem Skelett, lässt sich aber nicht über Parameter formen. Pose `ready` fehlt, Waffenanbindung ist offen (`Socket_Hand`).

## Register

`data/robots.toml`: Blatt = Linie × Basic-Typ, Blatt-ID `R<Linie><NN>`, ewig, wie `BA01`/`BA02` bei den Waffen. R01 und R02 bleiben reserviert.

- `[[types]]`: `num`, `name_de`, `module`, `since`.
- `[[lines]]`: Kennbuchstabe A–Z ohne I/O, englischer Name 1–3 Wörter ≤ 16 Zeichen, `skin`, `types`, optional `params.<num>`. `lines.merge` überschreibt nur vorhandene Schlüssel von `PARAMS`, Teile-IDs bleiben gleich.

## Schnittstelle eines Basic-Typs

Für einen weiteren Typ: Modul anlegen, unter `[[types]]` eintragen, Nummer in `types` der Linie ergänzen. Pipeline, GLB, Spec und Website bleiben unverändert; die Schlüssel der übrigen Typen auch. `lines.check_document` prüft den Vertrag bei jedem Bau.

| Punkt | Vorgabe |
|---|---|
| Modulort | `formgen/models/robot/roboterbasic_<NN>.py`, Daten daneben; keine Pfade außerhalb des Repos |
| Modul liefert | `PARAMS` (dict), `DATA_FILES` (Pfade, gehen in den Cache-Schlüssel), `document(params, *, sheet_id, line, name)` sowie `INFO`, `PARTS`, `ASSEMBLIES`, `ANCHORS`, `POSES` nach [Modellsprache](modellsprache.md); `INFO.kind = figure`, Maße mm (f,u,x), Boden u = 0, vorn f+, links x+ |
| Baugruppen | genau `head`, `arms`, `upper_body`, `lower_body`, `legs` |
| Anker | mindestens `Socket_Neck`, `Socket_Waist`, `Socket_Hip_R/L`, `Socket_Shoulder_R/L`, `Socket_Wrist_R/L`, `Socket_Hand`; weitere erlaubt |
| Rollen | nur Rollen aus `skins.toml` › `[roles]`; Farben nie im Modell. Ein neuer Skin ergänzt `[skins.<id>]`, siehe Cachehinweis in den Lehren |
| Herkunft | jede Zahl: `INFO.provenance` oder je Teil. Flächendaten (`surface`) sind zulässig, tragen `kind = gemessen` mit Quelle und werden im Bericht ausgewiesen |
| Abnahme | je Typ eigene Referenz über `python -m formgen.robot.silhouette`; IoU ≥ 0,90, Bänder 0,92–1,08 |

## Skin

Standard ist `weiss_graphit` in `skins.toml`, Farben aus den Materialien des Referenz-GLB. Weitere Skins kommen später. `[skins.weiss_graphit.finish]` hält Metall/Rauheit je Rolle für das GLB; das Raster-Blatt nutzt nur die Farben.

## Abnahme

Für RA01 ist die Referenz `RoboterBasic-01.glb` der Sicherung vom 05.11.2026 (SHA256 im Versionsbericht), gleiche Registrierung, kein Strecken: Front, Rücken, beide Seiten IoU ≥ 0,90; zehn Höhenbänder, äußere Spannweite Modell/Referenz 0,92–1,08. Die Referenz liegt nicht im Repo.
