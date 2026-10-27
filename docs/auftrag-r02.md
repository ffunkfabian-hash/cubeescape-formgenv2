# Auftrag R02 „Frost“ – Roboter nach dem weiß/blauen Blatt

Stand 27.10.2026, geschrieben von der Contour-Abschlusssitzung (Claude). Für eine **frische Sitzung ohne Verlauf/Fork**.
Dieser Auftrag ersetzt keine globalen oder Repo-Regeln; direkte Nutzeranweisungen haben Vorrang. Version, nicht Patch.

Erste Zeile des Prompts: `Opus, Denkaufwand high – Grund: Entwurf eines neuen Kernmodells (Roboterfigur) mit Referenzkonflikten`.
Sitzungsname `FORMGENV2 0.2 „Frost“ · Mac` (Vorschlag per `session_name.py --offline`; Name darf die Sitzung bestätigen).

## Ausgangslage

- Repo `/Users/ffunk/Claude/cubeescape-formgenv2`. Contour (0.1) ist lokal auf `codex/formgen-v2-first` committet, **nicht gemergt,
  nicht gepusht**. Basis für R02 ist der Commit, der diese Datei enthält. Lokalen Branch `claude/formgenv2-0.2-frost` davon anlegen.
- **Keine Remote-Reservierung:** `./ce session reserve` pusht den Branch; Push ist nicht freigegeben (siehe ENTSCHEIDUNGEN 26.10.2026).
  Sitzungsnamen nur lokal nennen. Kein Push, PR, Merge, Upload oder Release ohne ausdrückliches Ja des Nutzers.
- R01 bleibt unverändert, samt Originalen, Registrierung, Gates und Goldens. Seine offene Rücken/Band-0-Entscheidung gehört nicht zu R02.
- Nutzerentscheidung 27.10.2026: weiß/blaues Blatt als Vorlage; zuerst Referenzprobe (erledigt, unten); jetzt Auftrag für R02.
- Codex-Kontingent fast leer: keine Codex-Agenten oder `./ce codex judge`; unabhängige Prüfung durch Opus-Richter (`ce-judge`).

## Ziel (zwei Hauptziele)

1. **Referenz und Vertrag R02:** das weiß/blaue Blatt als verbindliche Orthos aufbereiten (Masken, gemeinsame Registrierung,
   Gelenkhöhen) und `docs/robot-contract-r02.md` schreiben. Offene Annahmen unten **vor** Modellcode mit dem Nutzer klären.
2. **R02-Modell bis zur Silhouettenabnahme:** neue Figur in der bestehenden Modellsprache (`formgen/models/figures/r02_*`),
   fünf Baugruppen wie R01, Farben nur in `skins.toml`, Front/Rücken/beide Profile je IoU ≥ 0,90 und alle 40 Breitenbänder 0,92–1,08.

Nicht Teil: Posen mit Waffe, Toolgen-Anpassung, neue Werkzeuge außerhalb des Repos, Veröffentlichung.

## Dateien und Zuständigkeit

- Neu: `formgen/models/figures/r02_basic_robot.py`, `formgen/models/figures/r02_parts/*.py`, `docs/robot-contract-r02.md`,
  `docs/herkunft-r02.md`, Tests `tests/test_r02_*.py`, R02-Skins in `skins.toml`.
- Anpassen: `tools/robot_reference_masks.py` und `tools/robot_evidence.py` so verallgemeinern, dass R01-Pfade, -Konstanten und -Ergebnisse
  **bytegleich** bleiben (R01-Masken-SHAs aus `refs/mask-provenance.json` und die R01-Metriken als Regressionstest festhalten).
- Nicht anfassen: R01-Module, R01-Referenzen in `refs/`, Toolgen, Formgen v1, ballon, Cube Escape, fremde Worktrees.
- Hauptagent hält VERSION-Konstanten, Montage, Integration und Commits; jeder Unteragent schreibt nur zugewiesene Dateien.

## Referenzen (extern, nicht im Repo)

Ordner `~/Library/Caches/CubeEscapeFormgen/refs-r02/`, SHA256 in `SHA256SUMS`:

| Datei | SHA256 | Rolle |
|---|---|---|
| `r02-blauweiss.svg` | `d997c46b…a4814` | **Vorlage** (Original aus Downloads `Pasted-20261027-110039.svg`) |
| `r02-blauweiss-marker.svg` | `4da6e597…1909d` | Codex-Arbeitsmarker auf unverändertem Original |
| `markers.json` | `51ef70c0…cfcfc` | ausgelesene Marker aller drei Blätter |
| `probe.py` | `8a0b5003…5f3` | Probe-Skript (Scratch, kein Repo-Werkzeug) |
| `candidates/weissgold*.svg`, `candidates/violett*.svg` | siehe `SHA256SUMS` | nur Vergleich, keine Vorlage (Violett: beide Profile mit „←“ beschriftet) |

Das Blatt ist eine vektorisierte Illustration (viewBox 2723×1155, 4663 Pfade) mit sechs Ansichten: Front, Rücken, Profil A (→),
Profil B (←), Draufsicht, Untersicht. Ober-/Untersicht sind nur Gestaltungsreferenz, keine Abnahme. Gestaltung: helle Panzerschalen,
dunkelgrauer Unterbau, hellblaue Kristallfelder an Schultern/Armen/Schienbeinen, Gürtel mit Taschen, dunkler Kragen, Helm mit blauem Visier.

## Probe-Ergebnisse (27.10.2026)

Beleg `~/Library/Caches/CubeEscapeFormgen/evidence/svg-probe-blue/` (`probe.json` SHA `03a7fa33…a2cc`, `probe-sheet.png`, Masken/Overlays).
Render mit `rsvg-convert -w 9803` (Faktor 3,6 → Figurenhöhe ≈ 3665 px wie R01). Masken: Vektor-Alpha > 127, Komponenten ≥ 0,2 % der
größten (abgelöste Hände), closing 2, fill. Keine Ansicht einzeln skaliert. Scheitel aller vier Ansichten px 174.

| Prüfung (Obergrenze für ein symmetrisches Modell) | Blau | R01-Originale |
|---|---|---|
| Front ↔ gespiegelter Rücken, IoU | 0,9746 | 0,9007 |
| Front ↔ Rücken, Bänder in 0,92–1,08 | 10/10 (Band 0: 0,963) | 9/10 |
| Profil ↔ gespiegeltes Profil, IoU | 0,9769 | 0,9925 |
| Profile, Bänder | 10/10 | 10/10 |
| Profilboden gegenüber Frontboden | ≈ 5,5 mm (px 3838 vs 3827/3828) | ≈ 53 mm |

Codex-Bodenlinien in SVG-Einheiten bestätigen das: Front 1065, Rücken 1064, Profil A 1062, Profil B 1063.
Maße unter der Höhenannahme 1924 mm (0,52497 mm/px): Frontbreite inkl. Arme 1023 mm, Profiltiefe 408 mm.
Das Bandmaß der Probe nutzt Bänder je Ansicht zwischen eigenem Scheitel und Boden; die Abnahme nutzt den gemeinsamen Front-u-Bereich.
**Die Probe belegt nur die innere Konsistenz der Vorlage, kein Bestehen eines Modells.** Nebenbefund: Bei R01 erreicht selbst ein
perfekt zur Front passendes symmetrisches Modell am Rücken nur etwa 0,90 – Ursache der R01-Rücken-IoU 0,8859 liegt in den Originalen.

## Offene Annahmen – vor Modellcode mit dem Nutzer klären

1. **Höhe:** Das Blatt nennt keine reale Größe (`design_height_mm: null`). Vorschlag: 1924 mm wie R01 (Vorgabe aus massfigur-v2) als
   *Annahme*, alle Bildmaße als *gemessen, auf Vorgabehöhe normalisiert*. Andere Höhe nur auf Nutzerangabe.
2. **Gelenkhöhen:** Die Codex-Marker sind Schätzungen („?“, gestrichelt) und widersprechen sich zwischen den Ansichten. In einem
   orthografischen Satz muss jede Höhe in allen Ansichten gleich sein. Höhen über Boden in mm (Annahme 1924):

   | Gelenk | Front | Rücken | Profil | größte Differenz |
   |---|---|---|---|---|
   | Hals N | 1669 | 1703 | 1688 | 34 |
   | Schulter S | 1480 | 1453 | 1529 | 76 |
   | Ellbogen E | 1268 | 1249 | 1276 | 27 |
   | Handgelenk W | 994 | 992 | 905 | 89 |
   | Hüfte H | 1055 | 1015 | 1049 | 40 |
   | Knie K | 631 | 641 | 646 | 15 |
   | Knöchel A | 163 | 163 | 163 / A1 217 | 0 (A1/A2 = zwei sichtbare Achsen) |

   Vorschlag analog R01: eigene Messung an sichtbaren Gelenkscheiben/Konturknicken je Ansicht, **Front verbindlich** für Höhen und
   Breiten, Profile für Tiefe/Fußlänge, Rücken für das Rückenmodul; jede Abweichung > 10 mm im Herkunftsdokument ausweisen.
   Handgelenk 89 mm: prüfen, ob die Profilarme anders hängen als in der Front (dann widerspricht die Vorlage einer starren Pose und
   der Nutzer muss entscheiden, welche Armhaltung gilt) oder ob nur der Marker falsch sitzt.
3. **Profilseiten:** Codex ordnet Profil A/B keiner anatomischen Seite zu. Festlegen per sichtbarer Asymmetrie oder Nutzerentscheidung;
   Kamerazuordnung wie R01 dokumentieren (Blickrichtung ↔ Rasterkamera), nie Geometrie spiegeln.
4. **Maskenmethode:** Vektor-Alpha statt R01-Schwellwert 248. Abgelöste Hände gehören zur Silhouette. Als `mask revision 1 (R02)` mit
   Begründung festschreiben; danach nicht mehr verändern.
5. **Zielbilder:** Repo-Regel „vor Roboterbau beide Zielbilder anfordern“: beim Start bestätigen lassen, dass das weiß/blaue Blatt
   Silhouette **und** Schalengestaltung vorgibt (bei R01 waren es Orthos plus Formstudie B), und ob Kristallfelder leuchten dürfen
   (Vorgabe „Visier plus max. zwei Funktionen“).

## Prüfen

- `./check` vor jedem Commit; gezielte R02-Tests (geschlossene Netze, Spiegelung über Export, Kern-/Schalenschnitte, koplanare Überdeckung
  aller Teile, Spec-/Geo-Roundtrip). Lehren aus `docs/LESSONS.md` beachten (kanonische Triangulation vor Spiegelung, konforme Zerlegung,
  Registrierung an gemeinsamer Landmarke, Maske und Beleg aus demselben Frame).
- Rendering nur auf dem Mac unter `~/Claude/cubeescape-nexogen/ce lock gpu -- …`, vorher `./ce lock status`; mittelgrauer Hintergrund,
  kein Bloom. Vor dem ersten R02-Render Cache-Abnahme mit echtem Artefakt; nie ungefragt alles neu rendern, kein `--force`.
- R01-Regression: Masken-SHAs, Metriken und Goldens unverändert.

## Fertig wenn

- Vertrag und Herkunft R02 geschrieben, offene Annahmen 1–5 vom Nutzer entschieden und in `docs/ENTSCHEIDUNGEN.md` eingetragen.
- R02 baut inkrementell (zweiter Lauf 0 gebaut), zwei cachefreie Seeds pixelgleich, R02-Goldens nach Sichtprüfung eingetragen.
- Front/Rücken/beide Profile IoU ≥ 0,90 und 40/40 Bänder 0,92–1,08 mit unveränderten Grenzwerten, Maske und Beleg aus demselben Frame;
  andernfalls konkrete Restabweichung mit Bild als „Entscheidung nötig“ melden, nichts lockern.
- Beleg: Kontaktbogen (vier Ansichten + Overlays + Baugruppen), kein MP4 (keine Bewegung). Opus-Richter mit `pruefung.md` vor Meldung.
- Bericht `docs/versions/0.2.md` (erste Zeile fertig/nicht fertig/Entscheidung nötig; Ist-Zeit Warten/Rechnen/Lesen/Umsetzen).

## Release

Nein. Lokale Commits auf dem lokalen R02-Branch sind beauftragt, sobald `./check` grün ist. Vor einem ausdrücklich beauftragten Merge
Pflichtprüfung durch einen Richter; Codex nur, wenn das Kontingent dann wieder reicht (`codex_quota.py`), sonst Opus und im Bericht nennen.

## Start-Check (erste Antwort, vor jeder Änderung)

Sitzungsname und Branch nennen (nie `main`); benötigte Ressource `gpu` nennen und `./ce lock status` zeigen; keine Remote-Reservierung
(Grund oben) – stattdessen lokalen Branch zeigen; fremde Bereiche nennen (R01, Toolgen, v1, ballon); dann Annahmen 1–5 dem Nutzer
vorlegen, bevor Modellcode entsteht.
