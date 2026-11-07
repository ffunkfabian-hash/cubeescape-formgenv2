# Roboter

Zwei Basic-Typen im Register: RoboterBasic-01 (Blatt `RA01`, Grundform wie BA01 bei den Waffen, dieses Dokument) und RoboterBasic-02 (Blatt `RA02`, Abschnitt [RoboterBasic-02](#roboterbasic-02)). Seit 0.12 gibt es fünf Linien (A–E) mit beiden Typen, zusammen zehn Blätter, siehe [Linien](#linien-und-liveries-012); seit 0.14 sind B–E eigene Roboter aus dem [Varianten-Baukasten](#varianten-baukasten-014).

```sh
.venv/bin/python -m formgen.robot                     # Geometrie, GLB, Spec, Prompts, Ansichten, Blatt, Vorschau (ohne --force nur Fehlendes)
.venv/bin/python -m formgen.robot --list              # Register: Blatt, Linie, Typ, Skin, Parameter; baut nichts
.venv/bin/python -m formgen.viewer                    # Website neu bauen
.venv/bin/python -m formgen.robot.silhouette <referenz.glb> --referenzhaltung [--typ 2 | --ohne-helm]
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

Grenzen: Der Helm ist die einzige Mesh-Übernahme und bleibt ungefast (`bevel = 0`, seine Fasen stecken in den gemessenen Flächen); er folgt dem Skelett und lässt sich seit 0.14 über `PARAMS['helmet']` formen (Gruppenfelder und Aufsätze, `formgen/models/robot/helmet.py`, [Baukasten](#varianten-baukasten-014)). Pose `ready` fehlt, Waffenanbindung ist offen (`Socket_Hand`).

## RoboterBasic-02

Eigener Körper, gemessen aus `robot_v2.blend` (SHA256 `67a350c1…d578`), zur Laufzeit ohne Blender. Modul `formgen/models/robot/roboterbasic_02.py`, Profile `roboterbasic_02_parameters.py`, Daten `roboterbasic_02_shapes.json` und `_shapes_2.json` (zwei Hälften der Teile, je unter 5 MB). Zuordnung aller Quellobjekte, Ausnahmen und Herkunft: [Bericht](robot/roboterbasic-02.md); Vorschläge [Parameter](robot/parameter-vorschlag.md), [Originalskin](robot/skin-vorschlag-roboterbasic-02.md).

| Punkt | Stand |
|---|---|
| Umfang | 554 Teile, 264.549 Dreiecke in A-Position, 1849 × 1446 × 507 mm |
| Fasen | `bevel = 0`: Die Fasen stecken in den gemessenen Netzen, `bevel.py` fast hier nichts |
| Mesh-Anteil | 199 Teile enthalten `surface`-Daten; `measured_parts` der Spec nennt alle 554, weil alle Teile gemessen sind |
| Haltung | A-Position wie RA01; `REFERENCE_PARAMS` ist die Quellhaltung, Schultern je 20 mm enger als die Quelle (Nutzerwunsch) |
| Abnahme | Front und Rücken IoU 0,9273, Seiten 0,9995; das Minus von vorn ist die engere Schulter |
| Rollen | `metal` und `glass` hat `weiss_graphit` nicht, sie kommen aus `[roles]` |
| Tausch mit 01 | Armkette geometrisch geprüft, Kopftausch nicht freigegeben |

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
| Baugruppen und Einzelteile | zwei Ebenen, je Einzelteil beide Körperseiten: Baugruppe `head` Kopf (Einzelteil `head`), `upper_body` Oberkörper (`upper_body` Oberkörper, `pelvis` Becken), `arms` Arme (`shoulders` Schulter, `upper_arms` Oberarm, `forearms` Unterarm, `hands` Hände), `legs` Beine (`thighs` Oberschenkel, `shins` Unterschenkel, `feet` Füße). Im Modell: `ASSEMBLIES` sind die Einzelteile mit den Feldern `group`, `group_de`, jedes Bauteil trägt `assembly`; GLB-Extras `basic_assembly`, `basic_group` |
| Anker | mindestens `Socket_Neck`, `Socket_Waist`, `Socket_Hip_R/L`, `Socket_Shoulder_R/L`, `Socket_Wrist_R/L`, `Socket_Hand`; weitere erlaubt |
| Rollen | nur Rollen aus `skins.toml` › `[roles]`; Farben nie im Modell. Ein neuer Skin ergänzt `[skins.<id>]`, siehe Cachehinweis in den Lehren |
| Herkunft | jede Zahl: `INFO.provenance` oder je Teil. Flächendaten (`surface`) sind zulässig, tragen `kind = gemessen` mit Quelle, stehen in der Spec unter `measured_parts` und werden im Bericht ausgewiesen |
| Haltung | Grundhaltung A-Position |
| Abnahme | je Typ eigene Referenz über `python -m formgen.robot.silhouette`, in der Haltung der Referenz; IoU ≥ 0,90, Bänder 0,92–1,08 |

## Linien und Liveries (0.12)

Eine Linie ist seit 0.12 eine Livery (eigener Skin) und seit 0.13 dazu eine Bauform ([Proportionen](#proportionen-013)). Jede Linie gilt für beide Typen, Blatt-ID `R<Linie><NN>`.

| Linie | Name | Skin | `arm_bulk` 01 / 02 | Proportionen (Schulter / Rumpf / Beine / Rücken) | Idee |
|---|---|---|---|---|---|
| A | Basic | `weiss_graphit` | 1,30 / 1,00 | 1,00 / 1,00 / 1,00 / 1,00 | Grundform, unverändert |
| B | Night Watch | `nachtwache` | wie A | 0,88 / 0,92 / 0,90 / 0,80 | dunkle Schale, schmal gebaut |
| C | Signal | `signal` | 1,42 / 1,12 | 1,22 / 1,10 / 1,15 / 1,25 | Warnorange, schwerer Arbeitsroboter |
| D | Field Olive | `feldoliv` | 1,18 / 0,92 | 0,95 / 1,00 / 0,92 / 1,30 | Oliv, schlank mit großem Feldgepäck |
| E | Cobalt Line | `kobaltblau` | wie A | 1,30 / 1,00 / 0,88 / 0,85 | Blau, Panzerschulter über schlanken Beinen |

Herkunft der Zahlen: Farben, `arm_bulk` und Proportionen sind Annahmen am Entwurf, am Vielfaltsmaß und am Bild gesichtet (der Test `test_every_line_is_a_complete_robot_livery…` prüft nur, dass jeder gesetzte Schlüssel in `PARAMS` des Typs existiert). Teile-IDs, Anker, Baugruppen und Abnahme bleiben die der Typen; die Silhouettenabnahme gilt für Linie A in der Referenzhaltung; B–E ändern nur Querschnitte (Arme, Proportionen). Jeder Skin deckt alle neun Rollen von `weiss_graphit` samt `finish` ab, trägt `robot = true` (nie für Waffen wählbar) und hat noch keinen `aaa`-Block: Die Eingangsfarben für Cycles sind nicht gemessen, GLB, Blatt und 3D-Seite zeigen die Hexwerte. Ein Skin kommt im Katalog der Website auch als Wahl in der 3D-Ansicht vor, auf jedem Roboter ([Website](website.md#skinwechsel)).

## Proportionen (0.13)

`PARAMS['proportion']` hat vier Faktoren, die beide Typen kennen (`formgen/models/robot/proportion.py`). Standard 1,0 ändert nichts: `apply` gibt dann dasselbe Objekt zurück, die Referenzhaltung der Abnahme bleibt unberührt. Erlaubt sind 0,7–1,4 (Annahme: außerhalb schneiden sich Schale, Kern und Gelenk sichtbar durch). Ein Faktor skaliert Breite `a` und Tiefe `b` der Profilzeilen, nie Höhen `z`, Versätze, Gelenke oder Skelett; Teile und IDs bleiben.

| Faktor | Profile | Wirkung am Bild |
|---|---|---|
| `shoulders` | `torso.pauldron` (Lagen, `flare`, `flare2`) | Schulterpanzer breiter oder kleiner, Draufsicht |
| `torso` | `torso.core`, `collar`, `waist`, `gorget` | Brustkorb und Kragen; von vorn kaum sichtbar, weil Schulter und Arme die Breite tragen |
| `legs` | `legs.thigh`, `shin`, `kneecap`, `knee_r` | stärkere oder schlankere Beine, Front und Seite |
| `pack` | `torso.back.rows` | Rückenmodul, Seite und Draufsicht |

Beide Typen gehen denselben Weg: RA01 baut die skalierten Profile, RA02 überträgt die Differenz als Verschiebungsfeld auf die gemessenen Teile (554, davon 199 mit Flächendaten; `roboterbasic_02_parameters.templates`), es gibt keine Neumodellierung. Das Feld ist lokal: Bei `legs` wandern Fuß und Becken in der Nähe der Gelenke ein Stück mit. Dabei fand 0.13 einen Fehler: RA02 hängte bei jeder Profiländerung Konstruktorteile ohne gemessenes Gegenstück an (30 Teile bei den Beinen mit Faktor 1,25, darunter `shin_core`; ein Teil der linken Rippe lag bei −9922 mm). Seit 0.13 entstehen neue Teile nur für Merkmale, die der Standard nicht kennt (z. B. `torso.waist_pistons = true`). Schalter wie `gorget` oder `flare` stehen in RA01 an und in RA02 aus; sie taugen darum nicht als gemeinsame Linienparameter und bleiben außen vor.

Vielfaltsmaß `python -m formgen.robot.variety`: Silhouetten-IoU jeder Linie gegen A desselben Typs und der Linien untereinander, Front, Seite und Draufsicht, 2 mm je Pixel. Schwellen (Annahme): Linie gegen A höchstens 0,97, Linie gegen Linie höchstens 0,985 in der kleinsten Ansicht; Messung der kleinsten Ansicht 0,86–0,96 gegen A, 0,81–0,93 untereinander (Tabelle im [Bericht](versions/0.13.md)). Der Test `test_robot_proportion` fordert beides für alle acht Blätter außer A und bringt die Gegenprobe (eine Linie ohne Proportionen: IoU genau 1,0, wird gemeldet).

## Varianten-Baukasten (0.14)

RA01 und RA02 sind die Basisversionen wie BA01 bei den Waffen. Neue Roboter entstehen je Einzelteil: Der Katalog `formgen/models/robot/catalog/` hält für jedes der zehn Einzelteile Formvarianten, eine Linie wählt im Register je Einzelteil eine (`[lines.parts]`, z. B. `shoulders = "SH-C"`), fehlende bleiben bei der Grundform A.

| Punkt | Vorgabe |
|---|---|
| ID | `<Kürzel>-<Buchstabe>`, ewig; Kürzel HD Kopf, UB Oberkörper, PV Becken, SH Schulter, UA Oberarm, FA Unterarm, HN Hände, TH Oberschenkel, SN Unterschenkel, FT Füße; A = Grundform `Basic` |
| Regel | Buchstabe B–Z ohne I/O, englischer Name 1–3 Wörter ≤ 16 Zeichen, je Einzelteil nichts doppelt, `since`, Idee, Herkunft (`origin`) |
| Wirkung | nur Parameter im gemeinsamen Vokabular beider Typen (`params`, strikt), optional je Typ (`types`); gesperrt sind Skelett, Haltung, Maße, Proportionen. `catalog.OPTIONS` hat die bisher ungenannten Schalter von `body.py` mit dem Wert, den der Konstruktor ohne Schlüssel nimmt |
| Ablauf | `parts()` beider Typen: `proportion.apply(catalog.apply(params))`; nur Grundformen → gleiches Objekt, A und die Abnahme bleiben bytegleich |
| RA02 | `ra02 = 'field'`: Verschiebungsfeld und kalibrierte Aufsätze (`roboterbasic_02_parameters.templates`); `ra02 = 'replace'`: Ersatzmodus, die Messteile des Einzelteils weichen konstruierten Teilen, eingepasst je Segment um das gemessene Gelenk (`roboterbasic_02_replace.py`); kostet dort den gemessenen Look. Kopf: eigener Weg über `helmet.ra02`, kein Ersatz |
| Kopf | `PARAMS['helmet']`: Felder je Helmgruppe (Haube, Visier, Kiefer, Seiten, Kragen, Hinterkopf) und Aufsätze (Kamm, Antennen, Ohrausleger, Linse, Halsleitungen), RA01 und RA02 |
| Arme | Unterarm- und Handmaße als `PARAMS['forearm']`, `PARAMS['hand']` (`arm.FOREARM`, `arm.HAND`, vorher Konstanten); Fingermaße nur RA01 (RA02 hat gemessene Fingerrahmen) |
| Spec | Feld `variants` (alle zehn Einzelteile) nur bei einer Wahl; `spec.migrate` ergänzt bei älteren Specs die Grundformen. Register Version 2, v1 wird beim Laden migriert |
| Vielfalt | `python -m formgen.robot.variety --teile`: je Typ jede Variante allein, IoU nur der Teile ihres Einzelteils gegen die Grundform (Schwelle 0,97, Annahme) und die größte Nebenwirkung auf ein anderes Einzelteil; dazu je Linie jedes Einzelteil gegen A |

Grenzen der Einzelteile folgen in RA02 der Messung, nicht RA01: Bauchplatten und Taille gehören dort zum Becken, das Hüftgelenk zum Oberschenkel, das Knöchelgelenk zum Unterschenkel. Darum setzt keine Variante `abdomen` in RA02, und Merkmale, die das Feld in RA02 schlecht ansetzt (Kolben, Wirbelsäule), stehen in Ersatzvarianten (UB-D, TH-B, SN-B). Varianten und Messwerte: [Bericht 0.14](versions/0.14.md).

## Fasen

`bevel.evaluate(document)` ist der Auswertungsweg des Roboters: `geom.evaluate` baut Formen und Fugen, danach fast `bevel.py` jedes Teil. `geom._bevel` kann nur Konvexes, und `geom.py` steht in allen Waffenschlüsseln.

| Zahl | Wert | Herkunft |
|---|---|---|
| Breite je Form (`kit.BEVEL`), mm | `cyl` 0,8 · `hull` 2,0 · `box` 1,0 · `plate` 1,0 · `loft` 1,6 · `wrap` 1,2 · `tube` 0 | Vorgabe: BALLON 14bd78d, `tools/robot_build.py` `_piece` |
| Breite je Teil | `bevel=` in `body.py`, `arm.py` geht vor; `0` heißt dort „nicht gesetzt“ | Vorgabe: ebenda |
| Winkelgrenze, Segmente | 30°, 2 | Vorgabe: BALLON `kit.add_bevel` |
| Überlappungsschutz | gemeinsam je Teil, Fläche kippt nie (`KEEP`) | Vorgabe in der Art (`use_clamp_overlap`), Schwelle Annahme |
| Gehrung `MITER`, Kurzzug `SHORT_RUN`, `SLIVER_M`, `LOCAL_PASSES` | 1,5 · 4 · 0,02 mm · 60 | Annahme, am Bild und an der Referenz geprüft |

Die gemeinsame Klemmung trifft wie bei Blender viele Teile: 95 von 344 liegen unter der Nennbreite, 40 unter der Hälfte (`thigh_shell` rund 0,4 statt 1,2 mm). Die Schulterkugeln `arm_*_shoulder_ball` haben keine Kante über 30°, ihr Status ist `no_feature_edges`.

Teile mit Fugen klemmen örtlich je Ecke: Der Boolean hinterlässt Kleinstkanten, die gemeinsam geklemmt die Fase des ganzen Teils auslöschen würden (`chest` 0,04 statt 1,2 mm); Blender arbeitet dort auf N-Ecken und behält die volle Breite, gemessen an der Referenz. Dazu fallen Kantenzüge unter vierfacher Breite weg: Reste einer flach streifenden Fuge. Vierecke teilt `kit.py` an der kürzeren Diagonale, sonst wählt die 30°-Grenze links andere Kanten als rechts. Fasenflächen stehen in `mesh.soft` und sind in den Normalen untereinander glatt (BALLON: `harden_normals`, `WEIGHTED_NORMAL`). Keine Blender-Parität an Ecken.

## Skin

Standard ist `weiss_graphit` in `skins.toml`, Farben aus den Materialien des Referenz-GLB. Die Liveries der Linien B–E stehen daneben ([Linien](#linien-und-liveries-012)). `[skins.weiss_graphit.finish]` hält Metall/Rauheit je Rolle für GLB und Cycles, optional `spec` nur für Cycles; das Raster-Blatt nutzt nur die Farben. `[skins.weiss_graphit.aaa]` hält die Eingangsfarben für Cycles (wie `aaa_color` der Rollen): `roles` bleibt die Wirkung, GLB und Blatt zeigen sie unverändert.

Abnahme am AAA-Licht, kein Teil der Pipeline; das GLB bleibt die Lieferung:

```sh
./ce lock gpu -- "$PWD/.venv/bin/python" tools/robot_cycles.py RA01 --samples 128 --res 1200
```

Das Werkzeug lädt das fertige GLB, nimmt Materialien und AAA-Licht aus BALLONs gepinntem Kit und Lichtsetzung und Kamera aus `tools/robot_build.py` (14bd78d). Neben `<ID>_{hero,nah}.png` schreibt es `<ID>_rollen.json`: je Rolle der Median im Inneren einer Rollenmaske neben dem Hex aus `roles`, `rahmen` heißt höchstens 16 je Kanal Abstand (Annahme). Eine Skin-Änderung macht alle Waffenstufen veraltet (Lehren).

## Abnahme

Grundhaltung von RA01 ist die A-Position (`PARAMS`: Rumpf und Kopf gerade, Arme 40° vom Körper, Winkel `A_ANGLE`). Symmetrisch sind alle Bauteile bis auf den Helm (gemessene Daten) und die Bruststreifen `chest_stripe_a/b`, die schon in BALLON und im Referenz-GLB nur auf einer Seite liegen. Das Referenz-GLB steht im Kontrapost, darum misst die Abnahme nicht das ausgelieferte GLB, sondern dieselbe Quelle in `REFERENCE_PARAMS` (`--referenzhaltung`). Die Schulterteile öffnen je Seite gespiegelt um das Schultergelenk (`pose.shoulder_open`), in der Referenzhaltung ist der Winkel 0.

Für RA01 ist die Referenz `RoboterBasic-01.glb` der Sicherung vom 05.11.2026 (SHA256 im Versionsbericht), gleiche Registrierung, kein Strecken: Front, Rücken, beide Seiten IoU ≥ 0,90; zehn Höhenbänder, äußere Spannweite Modell/Referenz 0,92–1,08. Die Referenz liegt nicht im Repo.
