# Roboterherkunft und Referenzregistrierung

Direkte Nutzerentscheidung vom 26.10.2026: vier neue Orthos verbindlich, Front legt Gelenkhöhen, Standbreite und Fußhöhe fest; Seiten Tiefe/Profil, Fußlänge und Zehenform; Rücken Rückenmodul. Formstudie B liefert Schalengestaltung. Altes Konzeptblatt nur Stimmung.

Die Bilddateien sind4096×4096px. Frontfigur y223..3876 (=3653px). **1924mm ist eine Entwurfsvorgabe** aus massfigur-v2, keine gemessene Realgröße. Einheitlicher Maßstab k=1924/3653=0,526690mm/px in allen Ansichten. Registriert an der Helmoberkante (Front223px, side-right216px, side-left218px), ohne Streckung. f0 bei side-right x2150px ist eine gemeinsame Registrierungsannahme. Front-Mittellinie x2048px.

## Gelenkhöhen

Gemessen an Cyan-Flächen der Ringscheiben, nur als Messmarker; Materialfarbe wird ausdrücklich nicht übernommen. Frontmittel über sichtbare Scheiben; gemittelte Begrenzungsrahmen-Zentren, gerundet. Individuelle Frontscheiben streuen Knie703–716, Knöchel230–238mm. Unabhängig vom Prüfagenten nachgerechnet.

| Gelenk | Front mm | Seite rechts mm | Seite links mm | gewählt mm | Grund |
|---|---:|---:|---:|---:|---|
| Knie | 710,0 | 685,0 | 685,5 | 710 | Front ist nach Nutzerentscheidung verbindlich; Seite ca25mm tiefer |
| Knöchel | 233,6 | 205,1 | 205,1 | 234 | Front ist verbindlich; Seite ca28mm tiefer |
| Ellbogen | 1275,3 | 1252,4 | 1254,1 | 1275 | Front legt Gelenkhöhe fest; Ringscheiben aus arms.PROVENANCE |
| Handgelenk | 1027,6 | 1000,2 | 1001,2 | 1028 | Front legt Gelenkhöhe fest; Handgelenk visuell abgelesen, gerundet |
| Hüfte | ca1080 | noch kein sicherer sichtbarer Ringmittelpunkt | noch offen | 1080 | angenommene Gelenkachse im gemessenen Front-Beckenbereich, keine Millimeterpräzision behauptet |

Ursprüngliche separate Höhennormalisierung ergab58/74mm Differenz und ist **verworfen**. Nach gemeinsamem Maßstab verbleiben25/28mm; diese liegen über der genannten10mm-Zeichnungstoleranz und werden nicht weggerechnet. Frontpriorität löst die Konstruktionsentscheidung, die Bildabweichung bleibt dokumentiert.

## Gestaltungs- und Materialquellen

- massfigur-v2: Entwurfsmaß1924mm, offene Schulterkappen, gefaltete Brust, getrennte Beinschalen und eingefasste Füße; ältere Gelenklagen durch neue Orthos ersetzt.
- ballon robot_arm.py: Ego-Armformen und Quelldaten, keine Veränderung im Schwesterrepo.
- Stilhandbuch: shell/graphite, dark_metal/anodized für Gelenkscheiben, Orange sparsam; kein Cyan an Gelenken. Leuchten nur Visier plus höchstens zwei weitere Funktionen.
- Referenzoriginale und Masken außerhalb Repo unter ~/Library/Caches/CubeEscapeFormgen/refs/. Masken sind vorläufig bis Sichtprüfung; IoU ist keine Aussage über Material oder Wandstärke.
