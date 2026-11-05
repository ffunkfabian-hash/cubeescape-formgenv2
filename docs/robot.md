# RoboterBasic-01

Basic-Typ 1 der Roboter, Blatt `RA01`, Grundform wie BA01 bei den Waffen. Heute steht nur er im Register; weitere Typen (`RA02`) und Linien sind im Aufbau vorgesehen.

```sh
.venv/bin/python -m formgen.robot                     # Geometrie, GLB, Spec, Prompts, Ansichten, Blatt, Vorschau (ohne --force nur Fehlendes)
.venv/bin/python -m formgen.viewer                    # Website neu bauen
.venv/bin/python -m formgen.robot.silhouette <referenz.glb> --referenzhaltung [--ohne-helm]
```

Bilder unter `./ce lock blender -- …` (CPU-Rasterizer). Blender wird nicht gebraucht: das GLB schreibt `formgen/robot/glb.py`.

## Quelle

| Datei | Inhalt | Herkunft |
|---|---|---|
| `formgen/models/robot/roboterbasic_01.py` | `INFO`, `PARTS`, `ASSEMBLIES`, `ANCHORS`, `POSES`; Körpermaße in `PARAMS`, Armmaße als Konstanten in `arm.py` (für Linien bisher nur `arm_bulk`) | Vorgabe: BALLON 14bd78d, Studie `a_waechter` |
| `formgen/models/robot/{forms,shapes,body,arm}.py` | Formbaukasten, einmalig übertragen | BALLON 14bd78d, Kopf ohne BALLONs Helmstudien |
| `formgen/models/robot/rig.py` | Skelett, Armhaltung, Fingergelenke | BALLON `tools/robot_build.py`, `tools/ego_build.py`, ohne Blender |
| `formgen/models/robot/kit.py` | Formen → kit-Teile in Weltmaßen (mm, f/u/x) | eigen |
| `formgen/robot/bevel.py` | Fasen auf geschlossenen Netzen, nach den Fugen | Vorgabe: BALLON 14bd78d, `kit.add_bevel` |
| `formgen/models/robot/helmet_h80.json` | Helm H 80, 58 Teile als Flächen im Kopfrahmen | gemessen aus `RoboterBasic-01.glb`, `tools/robot_helmet_transfer.py` |

Abbildung der BALLON-Formen: `loft`, `wrap`, `tube` → `surface`; `cyl` → `loft`; `box`, `plate`, `hull` → `hull`; Fugen (`cuts`) → `hull`-Schnitte. Das Feld `form` hält die Autorenform fest, `model.py` bleibt unverändert. Die Formparameter sind die Quelle, die ausgewerteten Punkte nur ihr Ergebnis; das gilt nicht für den Helm.

Grenzen: Der Helm ist die einzige Mesh-Übernahme und bleibt ungefast (`bevel = 0`, seine Fasen stecken in den gemessenen Flächen); er folgt dem Skelett, lässt sich aber nicht über Parameter formen. Pose `ready` fehlt, Waffenanbindung ist offen (`Socket_Hand`).

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
| Baugruppen und Einzelteile | zwei Ebenen, je Einzelteil beide Körperseiten: Baugruppe `head` Kopf (Einzelteil `head`), `upper_body` Oberkörper (`upper_body` Oberkörper, `pelvis` Becken), `arms` Arme (`shoulders` Schulter, `upper_arms` Oberarm, `forearms` Unterarm, `hands` Hände), `legs` Beine (`thighs` Oberschenkel, `shins` Unterschenkel, `feet` Füße). Im Modell: `ASSEMBLIES` sind die Einzelteile mit den Feldern `group`, `group_de`, jedes der 424 Bauteile trägt `assembly`; GLB-Extras `basic_assembly`, `basic_group` |
| Anker | mindestens `Socket_Neck`, `Socket_Waist`, `Socket_Hip_R/L`, `Socket_Shoulder_R/L`, `Socket_Wrist_R/L`, `Socket_Hand`; weitere erlaubt |
| Rollen | nur Rollen aus `skins.toml` › `[roles]`; Farben nie im Modell. Ein neuer Skin ergänzt `[skins.<id>]`, siehe Cachehinweis in den Lehren |
| Herkunft | jede Zahl: `INFO.provenance` oder je Teil. Flächendaten (`surface`) sind zulässig, tragen `kind = gemessen` mit Quelle, stehen in der Spec unter `measured_parts` und werden im Bericht ausgewiesen |
| Haltung | Grundhaltung A-Position |
| Abnahme | je Typ eigene Referenz über `python -m formgen.robot.silhouette`, in der Haltung der Referenz; IoU ≥ 0,90, Bänder 0,92–1,08 |

## Fasen

`bevel.evaluate(document)` ist der Auswertungsweg des Roboters: `geom.evaluate` baut Formen und Fugen, danach fast `bevel.py` jedes Teil. `geom._bevel` kann nur Konvexes, und `geom.py` steht in allen Waffenschlüsseln.

| Zahl | Wert | Herkunft |
|---|---|---|
| Breite je Form (`kit.BEVEL`), mm | `cyl` 0,8 · `hull` 2,0 · `box` 1,0 · `plate` 1,0 · `loft` 1,6 · `wrap` 1,2 · `tube` 0 | Vorgabe: BALLON 14bd78d, `tools/robot_build.py` `_piece` |
| Breite je Teil | `bevel=` in `body.py`, `arm.py` geht vor; `0` heißt dort „nicht gesetzt“ | Vorgabe: ebenda |
| Winkelgrenze, Segmente | 30°, 2 | Vorgabe: BALLON `kit.add_bevel` |
| Überlappungsschutz | gemeinsam je Teil, Fläche kippt nie (`KEEP`) | Vorgabe in der Art (`use_clamp_overlap`), Schwelle Annahme |
| Gehrung `MITER`, Kurzzug `SHORT_RUN`, `SLIVER_M`, `LOCAL_PASSES` | 1,5 · 4 · 0,02 mm · 60 | Annahme, am Bild und an der Referenz geprüft |

Teile mit Fugen klemmen örtlich je Ecke: Der Boolean hinterlässt Kleinstkanten, die gemeinsam geklemmt die Fase des ganzen Teils auslöschen würden (`chest` 0,04 statt 1,2 mm); Blender arbeitet dort auf N-Ecken und behält die volle Breite, gemessen an der Referenz. Dazu fallen Kantenzüge unter vierfacher Breite weg: Reste einer flach streifenden Fuge. Vierecke teilt `kit.py` an der kürzeren Diagonale, sonst wählt die 30°-Grenze links andere Kanten als rechts. Fasenflächen stehen in `mesh.soft` und sind in den Normalen untereinander glatt (BALLON: `harden_normals`, `WEIGHTED_NORMAL`). Keine Blender-Parität an Ecken.

## Skin

Standard ist `weiss_graphit` in `skins.toml`, Farben aus den Materialien des Referenz-GLB. Weitere Skins kommen später. `[skins.weiss_graphit.finish]` hält Metall/Rauheit je Rolle für GLB und Cycles, optional `spec` nur für Cycles; das Raster-Blatt nutzt nur die Farben. `[skins.weiss_graphit.aaa]` hält die Eingangsfarben für Cycles (wie `aaa_color` der Rollen): `roles` bleibt die Wirkung, GLB und Blatt zeigen sie unverändert.

Abnahme am AAA-Licht, kein Teil der Pipeline; das GLB bleibt die Lieferung:

```sh
./ce lock gpu -- "$PWD/.venv/bin/python" tools/robot_cycles.py RA01 --samples 128 --res 1200
```

Das Werkzeug lädt das fertige GLB, nimmt Materialien und AAA-Licht aus BALLONs gepinntem Kit und Lichtsetzung und Kamera aus `tools/robot_build.py` (14bd78d). Neben `<ID>_{hero,nah}.png` schreibt es `<ID>_rollen.json`: je Rolle der Median im Inneren einer Rollenmaske neben dem Hex aus `roles`. Eine Skin-Änderung macht alle Waffenstufen veraltet (Lehren).

## Abnahme

Grundhaltung von RA01 ist die A-Position (`PARAMS`: Rumpf und Kopf gerade, Arme 40° vom Körper, Winkel `A_ANGLE`). Symmetrisch sind alle Bauteile bis auf den Helm (gemessene Daten) und die Bruststreifen `chest_stripe_a/b`, die schon in BALLON und im Referenz-GLB nur auf einer Seite liegen. Das Referenz-GLB steht im Kontrapost, darum misst die Abnahme nicht das ausgelieferte GLB, sondern dieselbe Quelle in `REFERENCE_PARAMS` (`--referenzhaltung`). Die Schulterteile öffnen je Seite gespiegelt um das Schultergelenk (`pose.shoulder_open`), in der Referenzhaltung ist der Winkel 0.

Für RA01 ist die Referenz `RoboterBasic-01.glb` der Sicherung vom 05.11.2026 (SHA256 im Versionsbericht), gleiche Registrierung, kein Strecken: Front, Rücken, beide Seiten IoU ≥ 0,90; zehn Höhenbänder, äußere Spannweite Modell/Referenz 0,92–1,08. Die Referenz liegt nicht im Repo.
