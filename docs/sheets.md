# Konzeptblätter

`formgen.sheet.build(document, views)` und `formgen.sheet_figure.build(document, views)` liefern vollständiges HTML als String. Die Funktionen schreiben keine Dateien, importieren keinen Rasterizer und erzeugen keine Pixel. Farben werden aus dem gemeinsamen statischen Katalog `skins.toml` gelesen; importierte Geo-Farben bleiben erhalten. Die Darstellung ist responsiv, druckbar und verwendet Barlow aus `out/fonts/`.

## Bildvertrag

`views` bildet Ansichtnamen auf separate relative Dateien ab, beispielsweise `hero: ../views/W01/hero.png`. Fehlende Bilder erscheinen als „Ansicht ausstehend“, nie als andere Ersatzansicht. Eingebettete und entfernte Bild-URLs werden abgelehnt. Der Buildprozess hält diese Pfade stabil; eine Änderung am Rasterizer erfordert kein neues HTML-Layout.

| Blatt | Ansichten |
|---|---|
| Waffe | `hero`, `side_left`, `side_right`, `front`, `back`, `top`, `bottom`, `detail_trigger`, bei vorhandener Optik `sight_iso`, `sight_side` |
| Skins | `skin_standard`, `skin_nacht`, `skin_polar`, `skin_kobalt` |
| Visier | `iso`, sechs Orthogonalansichten, vier Skins |
| Figur | `front`, `side_left`, `back`, `iso`, `exploded`, `idle`, `ready`, `assembly_<id>` je Baugruppe |

Hero ohne abnehmbares Visier: Filterung ist Aufgabe des Bildproduzenten. Orthogonalbilder haben gleich große Bildflächen und einen gemeinsamen Maßstab/Bezugspunkt; der HTML-Composer skaliert alle sechs gleich. Empfohlene Größen: Hero 1440×960, Orthos/Details 960×480, Skins 960×640, Figur 960×960. Vorhandene Größen in Metadaten gehen vor.

`views['_meta'][name]` enthält `width`, `height`, `scale_px_m`, `labels: [{label,x,y}]` sowie `reference_lines: {horizontal:[y], vertical:[x]}`. Alternativ akzeptiert die Beschriftung `anchors: {label:[x,y]}`. Positionen sind Pixel des zugehörigen Bilds. Bis zu acht priorisierte Nummernmarkierungen stehen im Bild, lesbare Namen in einer fließenden Legende; weitere Teile werden ausgeschrieben. Gleicher Maßstab wird nur bei sechs übereinstimmenden positiven Werten behauptet.

Warnungen des Dokuments und fehlende Ansichten erscheinen komprimiert im Blattkopf, mit aufklappbaren vollständigen Details. Die sechs Orthos übernehmen echte gelieferte Referenzlinien; der Composer erfindet keine geometrischen Bezugslinien. Figuren erhalten je Baugruppe einen beim Drucken getrennten Abschnitt mit vollständiger Teileliste und zugeordneten Ankern. Nicht deklarierte Zuordnungen werden sichtbar ergänzt. Fehlende Posen und `Socket_Hand` bleiben ausdrücklich offen.

## Herkunft und Prüfung

Aufteilung und Informationsumfang aus Formgen v1 `claude/generator/xl.py` und `views.py`, gelesen am 26.10.2026: Hero, Beschriftungen, sechs Orthos, Abzugsdetail, abgesetzte Optik, Materialien, Skins, zweisprachige Prompts. Das HTML ist eine neue Implementierung; die Figurenseiten sind eine v2-Erweiterung. Prompts stammen ausschließlich aus `formgen.prompts.build(document)`.

`python -m unittest tests.test_sheet` prüft Struktur, stabile Bildpfade, sichtbare Lücken, Maßstabsaussagen, Escaping, Beschriftungsgrenze, Figurenbaugruppen und Verzicht auf Rasterizer-Aufrufe. Sichtprüfung der erzeugten Blätter bleibt Aufgabe der integrierten Abnahme.
