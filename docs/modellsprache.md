# Modellsprache und verbindliche Schnittstellen

Stand 0.1 „Contour“, 26.10.2026. Quelle: ballon `basic/kit.py`, `basic/common.py` und Stilhandbuch §6; keine v1-Modellsprache.

## Autorenmodell

Python-Modul mit `INFO`, `PARTS`, `ASSEMBLIES`, `ANCHORS`, optional `POSES`. `model.load(path_or_module)` liefert ein JSON-serialisierbares Dict mit `info`, `parts`, `assemblies`, `anchors`, `poses`, `source`, `warnings`. Keine numpy-Arrays an Modulgrenzen.
`INFO`: `id`, `kind` (weapon/sight/figure), `name_de`, `provenance` (kind Vorgabe/gemessen/Annahme, source). Teil-IDs eindeutig und stabil.
`PARTS`: `id`, `assembly`, `shape`, Maßfelder, `role`, optional `bevel`, `cuts`, `parent_part`, `move`, `label`, `decals`, `provenance`.
`ASSEMBLIES`: Liste von Dicts mit `id`, `de` und optional `explode` (f,u,x in mm); Roboter zusätzlich `group`, `group_de` (Baugruppe über dem Einzelteil, [Roboter](robot.md)). `ANCHORS`: Socket-Name → `at` (f,u,x mm), `part`, `source`.
Eine Herkunft im INFO gilt als ausdrücklich deklarierter Default für alle nicht separat bezeichneten Entwurfsmaße. Gemessene Ausgaben führen den Messweg zusätzlich.

## Abweichungen zu ballon

`INFO` statt `META`, `assembly` statt `asm`, `role` statt `mat`, `label` statt `de`: `model.normalize()` akzeptiert beide Schreibweisen; widersprüchliche doppelte Felder sind Fehler. Sonstige Geometriefelder bleiben identisch. Farben stehen ausschließlich in `skins.toml`. Pilot W01 ist eine dokumentierte Übertragung des Teile-Dict-Stands, keine neue Form.

## Geometrie

Autorenmaß mm: f nach vorn, u nach oben, x nach links. Gemeinsamer Ausgaberaum Meter: `(x,-f,u)/1000`, Z oben, −Y vorn. `geom.evaluate(model, *, booleans=True, bevels=True)` liefert dieselbe Dokumentstruktur, ersetzt Teile durch Netze. Jedes Teil behält Metadaten und bekommt `mesh={vertices,faces,hard}`, `bounds_m`; `anchors` bekommen `position_m`. INFO bleibt erhalten. `bounds_m` ist `[min_xyz,max_xyz]`; `counts` enthält parts, vertices, faces, triangles. Warnungen sind eine Liste von Texten, sichtbar im Blattkopf. Geometrie ist in Weltkoordinaten, kein zweiter Transformationsweg.

| Form | Felder in mm |
|---|---|
| prof | pts: (f,u), w, x=0 |
| box | f0 f1 u0 u1 w x=0 |
| cyl | axis f/x/u, c wie kit, a0 a1 r r1 optional r_in optional segs=24 |
| plan | pts: (f,x), u0 u1 |
| frame | f0 f1 cu ow oh iw ih r_out r_in cx |
| xbox | f0 f1 cu ww hh cx |
| multi | items: Formen; ein logisches Teil |
| tube | path: (f,u,x), r; offene AUTO-Bezier-Mittellinie, Auflösung12 nach Blender5.0.1; Ringtransport/Tessellation weiterhin abweichend |
| text | text, size, f u x, side, depth, align; echte Bfont-Konturen aus statischer Ressource, eine Zeile ASCII/Latin-1, Standardabstände; optionale v2-Tessellation resolution=12 |
| hull | points: (f,u,x), konvexe Hülle |
| loft | rings: gleich lange Punktlisten (f,u,x), thickness optional, caps=True |
| surface | vertices: (f,u,x), faces: Indizes, thickness optional (Innenversatz) |
| prism2 | side: (f,u), front: (x,u), Schnitt beider extrudierter Profile |
| xprof | f0 f1 cu pts: (x,u) relativ zu cu, cx=0; Querprofil quer zur Laufachse, entlang f0..f1 extrudiert (seit 0.4, wie BALLON `kit.mesh_xprof`); Löcher als `cuts` gleicher Form (BALLON `common.xprof(holes=…)`) |

`cuts` subtrahiert kit-Formen. `bevel` ist die Fasenbreite als Rücksprung entlang der angrenzenden Flächen in mm (Blender-Offset), kein allgemeiner Rundungsradius. `segs_bevel=2` entspricht dem Kit-Standard: konvexe zusammenhängende Komponenten erhalten einzeln ein segmentiertes Kreisprofil; ein konservativer Kantenclamp schützt dünne Flächen. `segs_bevel=1` erzeugt eine planare Fase.

Unveränderte konkave `prof`-/`plan`-Extrusionen ohne Cuts erhalten zusätzlich
analytische Längsfasen an konvexen und einspringenden Kanten über30° sowie
Endrandfasen (`segmented_profile_bevel`). Konstante Hohlzylinder/Rahmen ohne
Cuts bekommen Endringfasen; bei scharfen Profilkanten über30° werden außerdem
äußere und innere Längskanten berücksichtigt (`segmented_ring_profile_bevel`).
Offene Bohrungen bleiben erhalten. Kreisprofil, positive geschlossene Netze,
konservative Wand-/Längen-/Profilclamps und nicht gefüllte tiefe Einschnitte
sind analytisch geprüft. Kollabierende Kreisbogensamples werden bereits bei
der Konstruktion als ein gemeinsamer topologischer Knoten angelegt.
Die Endübergänge verwenden eigene Offset-Ecken; das ist **keine bestätigte
Blender-Eckmiter- oder Clamp-Parität**.

GEOM6 erkennt konstante X-Extrusionen nach Cuts anhand sämtlicher Flächen,
beider Endkonturen und der symmetrischen Volumendifferenz zur rekonstruierten
Extrusion. Beliebig viele unterschiedlich lange Außen-/Lochkonturen bleiben
getrennt erhalten; W01 nutzt dies für rail, stock_spine, stock und butt_pad.
Eine vollständig nachgewiesene rechteckige X-Minus-Blindtasche erhält direkte
Außen-/Mund-/Wand-/Bodenpatches (`segmented_pocket_bevel`), mit lokalem Clamp
auf 0,49 der Taschentiefe. W01 bolt_carrier nutzt 0,98mm bei 2mm Tiefe.
Überlappende Taschenmund-/Außenrandfasen werden ausdrücklich abgewiesen.
GEOM7 ergänzt für variable oder schräge Cut-Netze ein direktes Flächen-/Kanten-
BRep (`segmented_polyhedral_bevel`): wirkliche koplanare Flächen mit allen
Löchern, Kreisprofile an konvexen/konkaven Kanten über30°, gemeinsame
Zylinder-Schnittkurven an flachwinkligen Ecken und triangulierte Offset-Ecken.
Keine Hülle und keine Umordnung von Primitive/Cut/Fase. Lokale Rücksprünge
werden seit GEOM8 gemeinsam auf das Minimum der konservativen lokalen Grenzen
(0,24 der tatsächlichen Kanten-/Flächenabstände) begrenzt. Die verbleibenden
Verträglichkeitsbedingungen flacher Ecken dürfen einzelne Kanten weiter reduzieren.
Gemeinsamer Clamp, effektives Min/Max, angeforderte Breite und Anzahl geclampter
beziehungsweise zusätzlich reduzierter Kanten stehen in `bevel_diagnostics`
und der Warnung. W01 lower behält seine 5-mm-Vorgabe und Taschenmaße; alle
ausgewählten Kanten nutzen jetzt gemeinsam 0,36 mm. Beim Handschutz beträgt
der gemeinsame Clamp 0,72 mm; vier Kanten sinken bis auf 0,719486 mm.
Damit erhalten alle sieben bisherigen W01-Restteile bei Standard2Segmenten
echte Fasen. Nichtpositive/offene Quellen, misslungene Ecktriangulation,
Selbstschnitte und koplanare Überlappungen werden abgewiesen; das Teil bleibt
ausdrücklich `unsupported`. Das gilt auch bei höheren Segmentzahlen, wenn
deren Eckkonstruktion keine gültige Geometrie ergibt. Der frühere Gegenfall
upper mit vier Segmenten ist unter dem kleineren gemeinsamen Clamp gültig;
geschlossene positive Geometrie und die Fehlerweitergabe bleiben getestet.

Die Erweiterungen bestätigen weiterhin **keine Blender-Eckmiter-/Clamp-Parität**.
Ein tatsächlicher Blender-5.2.2-Bevel auf denselben sieben Post-Cut-Netzen
zeigt nach GEOM8 bei allen sieben Teilen weniger symmetrische Volumendifferenz
als zuvor: maximal 0,499 % statt 2,292 %, maximal 0,083772 mm Bounds-Abweichung
statt 0,728651 mm. Die gemeinsame Clampsemantik folgt
dem [versionierten Blender-Kern](https://github.com/blender/blender/blob/v5.2.2/source/blender/bmesh/tools/bmesh_bevel.cc#L8186);
der konservative Grenzwert und die Eckkonstruktion bleiben abweichend.
Unveränderte
Quellbelegung fern der effektiven Kantenumgebungen und echte Taschenböden/
Durchgänge sind separat geometrisch geprüft. Die zwingende Selbstschnittprüfung
erhöht den einmaligen W01-Datenbau gemessen von1,125sauf6,454s; der Cache bleibt
unverändert komponentenweise.

Mesh64-Ein-/Ausgabe bewahrt die Genauigkeit von Boolean- und Fasenknoten
(manifold3d ≥3.5.4). Fehlende echte Booleans/Fasen dürfen nie stillschweigend
als vollständig gelten. Ersatz-Cuts sind sichtbar gekennzeichnete Decal-Flächen.
Kein Renderer wird vor Cache-Abnahme ausgeführt.

Schriftgröße folgt Blenders Bfont-Metriken, die Grundlinie bleibt der Ursprung.
Die Extrusion reicht symmetrisch von−depth bis+depth; Ausrichtung berücksichtigt
den gesamten Zeichenfortschritt einschließlich Leerzeichen. Nicht unterstützte
Zeichen und Layoutvarianten erzeugen einen ausdrücklichen Fehler. Herkunft,
Grenzen und Prüfmethode: [Bfont-Ressource](fonts/README.md).

## Abnehmer und Cache

`raster.render(document, view='side_left', width=960, height=640, skin='standard', bg='mid', scale=None, center=None)` → PIL.Image. `raster.project` liefert projizierte Punkte, gemeinsame Kamerabasis; Skala px/m. `geo.load(path)` → dasselbe ausgewertete Dokument. `sheet.build(document, views, ...)` verarbeitet vorhandene Bilder und rendert nicht selbst.
`spec.build(document)` und `prompts.build(document)` sind reine Datenoperationen. VERSION-Konstanten importieren Werte aus `formgen/versions.py`; nur Hauptagent ändert diese.
Artefakte werden separat adressiert: geometry ← source+geom; views ← geometry+raster+Skin+Kamera; specs ← geometry+spec; prompts ← geometry+prompts; sheets ← geometry+sheet+stabile Bildpfade. Eine raster.VERSION-Änderung verändert ausschließlich Bilder; HTML referenziert stabile relative Bildpfade und braucht kein Re-Layout.

## Herkunft und Modellbesitz

`docs/herkunft.md` führt den Autorenort. Bei Übergabe ins Spiel wandert das Modell nach ballon; hier danach ausschließlich Geo-Eingang. Die beauftragte W01-Übertragung ist zunächst ein Vergleichspilot mit festgehaltenem Quellenhash; ballon bleibt bis zu einer ausdrücklich beauftragten Migration der produktive Autorenort.
