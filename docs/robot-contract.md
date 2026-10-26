# R01 – Baugruppenvertrag (aktuelle Nutzerentscheidung)

26.10.2026: Verbindlich sind vier neue Orthos unter `~/Library/Caches/CubeEscapeFormgen/refs/robot-ortho-{front,back,side-right,side-left}.png`.
Sie bestimmen Silhouette, Proportionen und Gelenklagen. B ist ausschließlich Schalengestaltung; altes Konzept nur Stimmung.
Originale tatsächlich 4096². Masken/Pixelmessungen `refs/ortho-measurements.json`, vorläufige Masken noch sichten.
Körperhöhe 1924 mm ist weiterhin **Vorgabe als Entwurfsmaß aus massfigur-v2**, keine aus dem Bild gewonnene reale Größe.
Bildanteile dürfen gemäß neuer Nutzerweisung als **gemessen (Pixel, auf Vorgabehöhe normalisiert)** in den Entwurf eingehen.
AKTUELLE KORREKTUR: Ein gemeinsamer Frontmaßstab 1924/3653 mm/Pixel für ALLE Ansichten; Helmoberkante Front223, Seite rechts216/links218 ausrichten. KEINE individuelle Höhennormalisierung. Fußstand, Fußhöhe und Breite aus Front. Keine unabhängige X/Y-Streckung in Abnahmemasken.

## Schnittstelle

Jedes Modul unter `formgen/models/figures/r01_parts/` exportiert `PARTS` (Liste kit Dicts), `ANCHORS` (Socket→at/part/source), `PROVENANCE`.
Alle Koordinaten bereits im gemeinsamen Welt-Autorenrahmen **mm (f,u,x)**, Boden u=0; vorn f+, anatomisch links x+.
Kein eigener Modulimport außerhalb Repo. Zahlenherkunft pro Teil oder PROVENANCE, Kennzeichnung Vorgabe/gemessen/Annahme.
`assembly` genau `legs`, `lower_body`, `upper_body`, `head`, `arms`. Teile id mit Präfix Baugruppe, Seite _r/_l.
Beine umfassen Füße und Knie; Arme umfassen Hände/Ellbogen/Schulter-Gelenk, Schulter-Panzer gehören upper_body.
Hauptagent montiert r01_basic_robot.py und hält POSES/VERSION. Keine fremden Dateien ändern.

## Form

Kit-Körperformen hull/loft/surface/prism2 nutzen; große Schalen mit echter Wandstärke und Fugen. Ober-/Unterbein aus getrennten Vorder-/Rückschalen.
Materialrollen aus skins.toml: helle shell, Unterbau graphite, Gelenkscheiben dark_metal/anodized, Akzent orange. **Kein Cyan an Gelenken.** Leuchten Visier plus max zwei Funktionen.
Formstudie B Facettierung/Schichtung ohne Zusatzdekoration. Herkunft Codex massfigur-v2 als Entwurf/Prinzipien, nicht als Abnahme.
Geometrie in eigenen Modulen editierbar, keine reine Mesh-Übernahme der Gesamtfigur.

## Abnahme

Front/Rücken/beide Seiten jeweils IoU≥0,90; zehn Höhenbänder Breitenverhältnis 0,92–1,08. Volle Silhouette erst mit allen Gruppen sinnvoll, Gruppen isoliert in ihren belegten Höhenbändern vergleichen.
Referenz side-right blickt im Bild nach links → Rasterkamera side_left; side-left blickt nach rechts → Rasterkamera side_right. Das ist eine dokumentierte Namenszuordnung, kein Spiegeln der Geometrie.
Neue Gelenklagen aus Orthos ersetzen widersprechende alte Entwurfsanker mit dokumentiertem Vergleich, niemals stumme Anpassung.
Fertige Gruppe erst nach Bild und gemessenen Zahlen unabhängiger Prüfung melden.

## Gemeinsame Registrierung (26.10.2026, nach Vermessung)

- Front x-Mitte 2048 px (gemessen, Bildbreite 4096), Figur y=223..3876, Höhe3653 px; k=1924/3653 mm/px.
- side-right f=0 bei Bild-x=2150 px; f=(2150-x)·1924/3653 (gemeinsame Registrierungsannahme). Gegenansicht side-left Ursprung x=1946.
- Neue vorläufige Gelenkhöhen aus sichtbaren Ringscheiben: Hüfte1080, Knie710, Knöchel234 mm. Alte Entwurfswerte1020/600/180 sind abgelöst und bleiben nur im Herkunftsvergleich.
- Bein-Knie x≈±195, Knöchel±240, Fußmitten±260 mm (normalisierte Bildmessung). Seitenlage Knie f≈30, Knöchel f≈−30, Hüfte f≈50 mm.
- Diese Werte sind gerundete Pixelmessungen mit Skalierungsannahme1924; keine real vermessene Maschine. Gruppen dürfen sie nur gemeinsam ändern.

- Restabweichungen nach einheitlicher Registrierung: Knie Seite685 vs Front710 mm; Knöchel Seite205 vs Front234 mm. **Frontwerte verbindlich**, Seiten liefern Tiefe/Profil, Fußlänge/Zehenform; Rücken das Rückenmodul (direkte Nutzerentscheidung).
