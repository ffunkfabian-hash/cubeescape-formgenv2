# Vorschlag an ballon: vier Körperformen und gemeinsame Netzschnittstelle

Status: implementierter Vorschlag in Formgen v2; ballon wurde nicht geändert. Referenz für vorhandene Formen: `cubeescape-ballon/basic/kit.py`, Funktionen `mesh_prof`, `mesh_plan`, `mesh_cyl`, `mesh_frame`, `build_shape` und `build_part`, gelesen am 26.10.2026. Quellenmaße des Piloten stehen unverändert in dessen Teile-Dicts; Herkunft und Quellenhash führt `W01.INFO.source`.

Alle neuen Autorenkoordinaten verwenden `(f,u,x)` in Millimetern. Ausgabe wie kit: `(x,-f,u)/1000` in Metern. Keine Maße werden aus Konzeptbildern abgeleitet. Herkunft ist je Teil angegeben oder erbt ausdrücklich `INFO.provenance`.

| Form | Eingabe | Verbindliche Semantik |
|---|---|---|
| `hull` | `points`: mindestens vier nicht koplanare Punkte | Konvexe Hülle; konsistent nach außen gerichtete Dreiecke. Innenpunkte ändern das Volumen nicht. |
| `loft` | `rings`: mindestens zwei gleich lange Punktlisten, `caps=True`, optional `thickness` | Korrespondierende Ringpunkte verbinden, Reihenfolge ohne Verdrehung; mit `caps` beide Enden schließen. Innenversatz erhält die Außenmaße. Bei geschlossenen Enden entsteht eine geschlossene Innenkammer; ohne Enddeckel bleiben die Öffnungen offen, ihre Randflächen schließen die Wand. |
| `surface` | `vertices`, `faces`, optional `thickness` | Autorierte Oberfläche, deren Flächenorientierung die Außenseite festlegt. Ohne Dicke bleibt sie gegebenenfalls offen. Mit Dicke entsteht ein Innenversatz plus geschlossene Randflächen. |
| `prism2` | `side`: `(f,u)`-Profil, `front`: `(x,u)`-Profil | Beide Profile über die Spanne des jeweils anderen extrudieren, dann exakter Volumenschnitt. Ohne Boolean-Backend wird diese Form ausdrücklich abgelehnt; ein angenähertes Volumen wäre irreführend. |

`thickness` ist positiv. Innenpunkte werden durch den Schnitt versetzter angrenzender Flächenebenen bestimmt, nicht durch pauschale Skalierung um den Schwerpunkt. Dadurch hat ein rechtwinkliger geschlossener 100-mm-Würfel mit 10 mm Wand eine 80-mm-Innenkammer. Unvereinbare nichtplanare Knoten, kollabierende oder umgekehrte Innenkanten werden abgelehnt. Das Verfahren ist kein allgemeiner CAD-Offset für selbstschneidende oder beliebig stark gekrümmte Flächen; solche Modelle benötigen passende Unterteilung und gesonderte geometrische Prüfung.

Für kit wird dieselbe Eingabesemantik empfohlen; `bmesh` kann Hull/Loft/Surface bauen, `prism2` kann den vorhandenen exakten Boolean-Weg verwenden. Formgen liefert bereits JSON-serialisierbare Weltkoordinaten mit `mesh.vertices`, `mesh.faces` und einem Härtewert pro Fläche sowie expliziten Vertex-/Flächen-/Dreieckzahlen. Konkave Profildeckel werden tatsächlich trianguliert, nicht als Dreiecksfächer angenähert.

## Bestehende kit-Semantik und offengelegte Grenzen der ersten Etappe

- `cyl` übernimmt `c=(u,x)` bei `axis='f'`, `(f,u)` bei `'x'`, `(f,x)` bei `'u'`, Winkelphase `pi/segs`, `segs=24` und konischen Innenradius `r_in*r1/r`. `xbox` benutzt kit-Felder `ww/hh`.
- `multi` fügt Netze wie ballons Mesh-Zusammenführung in einem logischen Teil zusammen. Es ist keine pauschale Volumenunion; überlappende Unterformen bleiben möglich.
- `cuts` verwenden echte manifold3d-Differenzen. Ohne Backend bzw. mit `booleans=False` bleibt das Volumen erhalten; `decal_meshes` markieren ausgesparte Bereiche dunkel und eine Warnung muss sichtbar im Blattkopf erscheinen. Exakte Boolean-Fehler werden nicht stillschweigend degradiert.
- Aktuelle Fasen sind echte planare Kantenabschnitte konvexer Körper über manifold3d-Schnitte. Sie sind **nicht** ballons Rundung mit zwei Segmenten. Konkave Körper, Rahmen, Hohlkörper und mehrteilige Netze erhalten derzeit ausdrücklich `bevel_status='unsupported'` und eine Warnung. `bevel=0` erzeugt keine Fase. Ohne Angabe gilt kit-konform 1 mm. Diese Etappe genügt nicht für die endgültige vollständige Pilotparität.
- `tube` nutzt Ringtransport entlang der autorierten Polylinie; ballons automatisch geglättete Bezierkurve wird nicht nachgebildet. Eine Warnung kennzeichnet diesen Unterschied.
- `text` erzeugt eine dünne sichtbare Ersatztafel mit deklarierter Textausdehnung; die Schriftkontur bleibt offen. Textinhalt bleibt als Metadatum erhalten, der Unterschied erscheint in den Warnungen.
- `frame` unterstützt eckige Außen-/Innenprofile sowie beidseitig abgerundete Profile. Gemischt eckige/abgerundete Lochrahmen werden ausdrücklich abgelehnt und brauchen getrennte Profil-Cuts.
- `move` beschreibt Bewegung und bleibt unverändert als Metadatum; das Basisnetz erhält keine implizite Animation. Posen sind Aufgabe des Figurenablaufs.

## Prüfbelege ohne Rendering

`tests/test_model.py`: Alias-Konflikte, eindeutige IDs, vollständige Baugruppen, Ankerreferenzen, Elternzyklen, Herkunft, endliche Zahlen, erneutes Laden nach schneller Quelldateiänderung und alle 72 übertragenen Pilotteile. Der Lade-Test prüft geänderten Quell-SHA und aktualisierte Geometriezahl trotz identischer Dateilänge; Timestamp-Pythoncache wird nicht verwendet.

`tests/test_geom.py`: Analytische Volumina und konsistente geschlossene Kanten für Box, konkave Profile, Plan, konische Hohlzylinder in allen Achsen, Rahmen, Tube, Hull, Loft, Wandstärke, Surface, Prism2 und Boolean-Durchbruch; Ablehnung zu großer Dicke; Fase verändert Volumen bei gleichen Außenmaßen; fehlendes Boolean-Backend erzeugt Warnung plus Decal-Netz; kompletter W01-Bau bleibt endlich und JSON-serialisierbar.

Reproduktion: `.venv/bin/python -m unittest tests.test_model tests.test_geom -v`. W01 in dieser Etappe: 72 Teile, 4.881 Vertices, 9.374 Dreiecke; lokale Geometriezeit rund 0,42 Sekunden. Es wurden keine Bilder oder Blender-Szenen erzeugt.
