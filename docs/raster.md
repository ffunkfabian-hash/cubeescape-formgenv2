# Rasterizer: Vertrag und Herkunft

`formgen/raster.py` übernimmt und adaptiert den CPU-Rasterablauf aus
`cubeescape-formgen/claude/generator/raster.py`, SHA256
`7ab4863e8eb4e4fe21fdfdf5fb3cf84dc0b0075b29cd010d3b0b47daea240057`.
Übernommen sind Z-Buffer, Flächen-ID-Konturen, Supersampling 2×, Rekonstruktion
von Objektkoordinaten für Texturen und ein nachgelagerter Glasdurchgang.
Die frühere `eng`-Geometrie, v1-Autorensprache, SVG-Einbettung und Bloom wurden
nicht übernommen. Dreiecke werden baryzentrisch ausgewertet, konkave ebene
Polygone über Ear-Clipping trianguliert. Benachbarte Flächen eines Teils mit einem Diederwinkel unter 25° teilen eine
Flächen-ID; gering verwundene Loftquads erhalten keine Triangulierungsdiagonale
als Kontur. Identische Vertexkoordinaten werden für die Nachbarschaftsermittlung
zusammengefasst. Scharfe Falten, Teilegrenzen und Silhouetten bleiben erhalten.
Nichtmannigfaltige Kanten werden nicht automatisch geglättet.
`mesh.hard` ist ein Bool oder eine Liste mit einem Bool je Fläche. Weiche
Flächen teilen innerhalb des Teils eine ID. Normale und Beleuchtung bleiben
pro Fläche; dies ist bewusst kein interpoliertes Phong-Shading.

## Aufruf und Kamera

`render(document, view='side_left', width=960, height=640, skin='standard',
bg='mid', scale=None, center=None)` liefert ein RGBA-PIL-Bild. `document` enthält
bereits ausgewertete `parts[].mesh={vertices,faces,hard}`. Weltkoordinaten sind
Meter: Z oben, −Y vorn, +X links. Es findet kein zweiter Modelltransform statt.
Größere Kameratiefe liegt näher. Ansichten: `side_left`, `side_right`, `front`,
`back`, `top`, `bottom`, `iso`; Aliase `left/right/side/rear/oblique/threequarter`.
Von links betrachtet zeigt −Y im Bild nach links. Front zeigt +X nach rechts.
Oben/unten zeigen −Y nach links: Die Waffenlänge liegt auch dort horizontal.
Oben zeigt −X nach oben, unten +X nach oben.

`framing(document, views, width, height, padding=.08, center=None)` liefert
`{'scale': px_pro_Meter, 'center': [x,y,z]}`. Für alle sechs Orthos dieses Dict
unverändert übergeben: individuelle Autoanpassung allein garantiert keinen
gemeinsamen Maßstab. `project(points, view, width, height, scale, center)` nutzt
dieselbe Basis und liefert Pixel-x, Pixel-y, Tiefe in Metern. Ein Punkt bleibt
ein Dreiervektor, eine Punktliste liefert Nx3. `image.info` enthält `framing`,
`view`, `skin`, `anchors`, `boxes`, `raster_version`, `supersampling`.
Anker sind tatsächlich sichtbare Pixel nahe dem sichtbaren Schwerpunkt, keine
potenziell verdeckten geometrischen Mittelpunkte. Boxen/Anker sind Bildpixel
nach Supersampling; Schlüssel ist ein nichtleeres `label`, sonst `id` (auch bei Geo-Importen mit `label=null`).

## Material und Grenzen

Rollen, Farben, Skins, Hintergrund und Konturfarbe kommen aus `skins.toml`.
Eine explizite Geo-Importfarbe bleibt im Standardskin erhalten; ein Skin darf
sie über seine Rollenfarbe ersetzen. Licht besitzt vier diskrete Toonstufen;
der Ambientboden liegt bei 0,72, damit dunkle Rollen lesbar bleiben. Innere
Flächenkanten auf dunklem Material werden aus dessen Farbe und der vorhandenen
Konturfarbe aufgehellt; Außenkonturen bleiben dunkel. Rauheit moduliert feines, deterministisches Objektraumkorn, Metall beeinflusst
die Stufenschwelle. Tarnung, Gebrauchsspuren und Schmutz verwenden ebenfalls
Weltkoordinaten. Energie und importierte emissive Teile sind ungeschattet,
ohne Bloom. Glas nutzt TOML-alpha; opaque Flächen verdecken Glas korrekt.
Mehrere Glasbauteile werden je Pixel nach Tiefe sortiert. Pro Glasbauteil wird
nur die nächste Oberfläche gerechnet: dünne Scheiben erhalten keine doppelte
Deckkraft durch ihre Rückseite. Brechung, Fresnel und echte Reflexion sind
nicht Teil dieses Toon-Renderers. Glas-Effekt-Varianten verwenden derzeit die
jeweilige Grundrolle/Deckkraft, keine gesonderte Staub-/Risssimulation.

## Prüfung

`python -m unittest tests.test_raster.CameraMaterialTests` prüft Kamerabasis,
Maßstab, Framing, Materialauflösung, ungeschattete Energie und konkave
Triangulation ohne Bildproduktion. Pixeltests werden ausdrücklich aktiviert:
`ce lock gpu -- env FORMGEN_RENDER_TESTS=1 .venv/bin/python -m unittest tests.test_raster`.
Sie prüfen Tiefenreihenfolge, fehlende Triangulierungsnähte, Glasverdeckung,
Glasreihenfolge, fehlenden Bloom und sichtbare Beschriftungsanker.
Bildproduktion erst nach der separat bestätigten Cache-Abnahme.
