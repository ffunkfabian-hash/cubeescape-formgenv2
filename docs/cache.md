# Artefaktcache

Der unabhängig abgenommene Cache baut mit `--dummy` ein echtes JSON-Artefakt aus
`formgen/models/mini.py`. Dieser Pfad importiert weder Geometrie noch Rasterizer.

```sh
python3 -m unittest tests.test_cache -v
python3 -m formgen.build --dummy --out /tmp/formgen-proof/out --cache /tmp/formgen-proof/cache
python3 -m formgen.build --dummy --out /tmp/formgen-proof/out --cache /tmp/formgen-proof/cache
```

Erster Lauf: `1 gebaut · 0 aus dem Cache`. Zweiter Lauf: `0 gebaut · 1 aus dem Cache`.
Ohne Optionen liegt die Ausgabe unter `out/`, der Cache unter
`~/Library/Caches/CubeEscapeFormgen/artifacts/`. `--jobs N` verwendet mehrere Prozesse.
`--force` baut alle ausgewählten Artefakte, `--force-views` ausschließlich Art `views`,
`--force-sheets` ausschließlich Art `sheets`. `--force-views` erneuert außerdem die Raster-Vorschauen.
Beim Dummy bewirken beide selektiven Optionen keinen Neubau.
Unbekannte Modell-IDs und ungültige Prozesszahlen sind Fehler.

## Baupipeline

Ohne IDs werden W01 (Autorenmodell) sowie KG02 und VS02 (Geo-Eingänge) gebaut.
`--stages geometry` erzeugt ausschließlich Daten unter `out/geometry/<ID>.json`.
`--stages geometry,views --views side_left --width 480 --height 320` ergänzt gezielt Ansichten;
Bildläufe bleiben an die GPU-Sperre des Aufrufers gebunden. Weitere Stufen heißen `specs`, `prompts`, `sheets`, `previews`.
Geometrie kommt immer zuerst; Blätter benötigen zusätzlich die ausgewählten Ansichten.
Der Standard baut alle sechs Stufen. Fehlende Komponenten schlagen ausdrücklich fehl.

Ansichten besitzen je Modell/Ansicht einen eigenen PNG-Cacheeintrag und stabile Pfade
`views/<ID>/<view>.png`; die sechs Orthokameras verwenden identische Canvasgrößen und ein gemeinsames Framing.
Der Ansichtenschlüssel enthält Geometrie-Dateihash, Rasterversion, gesamten Skin-Dateihash,
Kamera, Abmessungen, Skinname und Hintergrund. `--skin` und `--bg` reichen Werte an den Rasterizer weiter.
Ohne `--views` enthält das Waffenblatt Hero ohne Visier (1440×960), sechs Orthos (960×480),
Abzugdetail (15-cm-Ausschnitt), separate Visieransichten und vier echte Skins (standard/nacht/polar/kobalt).
Nicht vorhandene Abzug-/Visierteile erzeugen keine erfundenen Bilder. Explizite Teilansichten ohne Teile sind Fehler.
Figuren haben Front/Seite/Rücken/Schräg, eine Ansicht je Baugruppe und – sofern vorhanden – dokumentierte
Explosionsvektoren bzw. Posen. Explosionsvektoren bleiben f/u/x in mm; ausgewertete Posen verwenden
`poses.<name>.part_transforms` als Teil-ID → 4×4-Matrix im Meter-Ausgaberaum. Figuren ohne Pose werden nicht umgedeutet.
`--width`/`--height` überschreiben die Standardgrößen ausdrücklich. PNG-Text `formgen_meta` speichert
sichtbare Beschriftungsanker, Boxen und Framing; der Blattadapter liest diese ohne erneutes Rendering.
Die separate Stufe `previews` erzeugt eine WebP-Vorschau unter `out/previews/<ID>.webp`.

Specs und Prompts werden unabhängig als JSON gebaut. Specs hängen zusätzlich vom Skin-Dateihash ab;
Prompts berücksichtigen die Specversion für ihre Maßberechnung. Blätter berücksichtigen Skinhash,
SHEET/PROMPTS/SPEC-Versionen, referenzieren Bilder relativ und
enthalten keine Bildbytes; neue Renderparameter oder Rasterversionen ändern ihren Schlüssel nicht.
Geometrie-Cachetreffer laden keine Autorenmodule und werten keine Geometrie erneut aus.
Statisch erkennbare lokale Python-Imports werden rekursiv in den Quellenhash einbezogen;
dynamische Importe benötigen eine ausdrückliche zusätzliche Quellenabhängigkeit vor ihrer Nutzung.
Bei Geo-Dateien gehören referenzierte Spec-Dateien einschließlich ihres Fehlens zum Quellenhash,
damit ein alter Treffer niemals die aktuelle Herkunftsprüfung umgeht.

## Schlüssel und Invalidierung

Ein `cache.Artifact` enthält Modell-ID, Art, Quellen-SHA256, Parameter, relevante Komponentenversionen,
stabilen relativen Ausgabepfad, Builder (`modul:funktion`) und Builder-Eingaben.
Der Schlüssel ist SHA256 aus kanonischem JSON über Cacheformat, Modell-ID, Quelle, Art, Parameter und Versionen.
Ausgabe- und Eingabepfade gehören nicht zum Schlüssel: eine verschobene unveränderte Quelle bleibt wiederverwendbar.
Alle inhaltlich wirksamen Eingaben müssen deshalb in Quelle, Parametern oder Versionen abgebildet werden.
`versions.py` bleibt die einzige Quelle der Komponentenversionen.

`build.Stage` und `build.plan(sources, stages)` planen unabhängige Artefakte.
`cache.run_artifacts(artifacts, out, cache, jobs=1, force=False, force_kinds=())` führt eine Stufe aus.
Ein Builder erhält das Artefakt und liefert `bytes` oder `str`; er wird erst bei einem nötigen Bau importiert.
Abhängige Stufen werden nacheinander geplant: Geometrieschlüssel als Quelle für Ansichten/Specs/Prompts,
Layout mit stabilen Bildpfaden. Eine neue Rasterversion gehört ausschließlich in Ansichten-Schlüssel;
sie invalidiert weder Specs noch Layouts. Kamera, Skininhalt und Renderparameter gehören in Ansichten-Parameter.
Die Pipeline hängt solche Stufen ein, ohne dass der Cache Renderer kennen muss.

## Integrität und parallele Läufe

Jeder Schlüssel besitzt `<cache>/<sha>/artifact` und `entry.json` mit Schlüssel, SHA256 und Größe.
Jeder Treffer prüft Payload-Hash und Größe. Fehlende oder beschädigte Ausgaben werden atomar aus dem
verifizierten Cache restauriert, ohne Builderaufruf. Ein fehlender oder beschädigter Cache wird neu gebaut.
Eine nach der Planung geänderte Dummy-Quelle bricht vor der Veröffentlichung ab.

POSIX-Dateisperren koordinieren Ausgabepfad, Cache-Schlüssel und Manifest über Prozesse hinweg.
Gleichzeitige Erstbauten desselben Artefakts führen genau einen Builder aus; Wartende erhalten den Cachetreffer.
Dateien werden im Zielverzeichnis geschrieben, synchronisiert und mit `os.replace` veröffentlicht.
Ein Cacheeintrag wird vollständig in einem temporären Verzeichnis vorbereitet und unter Schlüsselsperre ersetzt.
Builderfehler lassen bisherige Ausgaben und Cacheeinträge bestehen.

`out/manifest.json` wird unter eigener Sperre atomar zusammengeführt und erklärt je Ausgabepfad den
letzten Lauf: Modell, Art, Quelle, Parameter, Versionen, Schlüssel, Payload-Hash, Größe, `built`/`cached`
und Grund (`missing_cache`, `corrupt_cache`, `force`, `cache_hit`, `restored_missing_output`,
`restored_corrupt_output`). Der Cache ist wiederherstellbarer lokaler Zustand; ein defektes Ausgabemanifest
wird beim nächsten Lauf aus den tatsächlich geprüften Artefakten neu aufgebaut. Keine Zeitstempel bestimmen
Invalidierung. Tests prüfen Disk-Wiederholung, Modellisolation, Parameter/Versionen, selektives Force,
beschädigte Dateien, Prozessrennen und Manifest-Zusammenführung, vollständig ohne Bildstufe.

Aktueller Zwischenstand: Registry enthält zusätzlich R01. Weitere Stufen `geo`
(nach Specs), `viewer`; Schriften sind eigene content-gehashte Ressourcen.
R01-Ready lädt W01-Geometrie als explizite Abhängigkeit; ihr Hash gehört nur in
betroffene Ansichtenschlüssel. Für den Blattcache wird ein Fingerabdruck der
wirklich verbrauchten PNG-Abmessungen und Layoutmetadaten aufgenommen. Reine
Rasterfarbänderungen ändern keinen Layoutschlüssel; geänderte Callouts/Skalen
oder Abmessungen müssen das Blatt erneuern. Kein veraltetes SVG über neuem Bild.

Native Geometrie bindet `docs/fonts/bfont-contours.json` in den bestehenden
Quellfingerabdruck ein; der Worker prüft dessen SHA vor und nach dem Bau.
Ein Fontwechsel invalidiert native Geometrie und ihre Folgeartefakte,
importierte Legacy-Geos bleiben unberührt. Der Fontleser cached nach tatsächlichen
Bytes und erkennt Ressourcenänderungen auch in einem langlebigen Prozess.
Legacy-Ansichten/Previews binden separat den Texturkatalog-SHA ein.

`--legacy-dir` ergänzt einzeln wählbare Geo-IDs. Eine referenzierte Visier-Spec
wird über die bestehende Geometrie-/Specstufe mitgebaut; Bild-/Prompt-/Geo-
Ausgaben des Visiers entstehen nur bei ausdrücklicher Auswahl. Ohne ID-Auswahl
bleiben die vier Piloten der Standardbau.
