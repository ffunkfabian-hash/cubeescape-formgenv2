# Frische Sitzung: Formgen v2 fertigstellen

**Nicht fertig.** Dies ist die verbindliche Übergabe eines lokal geprüften
technischen Zwischenstands, kein freigegebenes Modell. Ohne Verlauf/Fork starten.

## Arbeitsort, Auftrag, Regeln

- Repo `/Users/ffunk/Claude/cubeescape-formgenv2`, Branch `codex/formgen-v2-first`.
  Die Codex-Projektwurzel `/Users/ffunk/formgenv2` ist NICHT das Repo: Befehle
  ausdrücklich im oben genannten Verzeichnis ausführen.
- Globale `~/.codex/AGENTS.md`, lokale AGENTS und `docs/auftrag-codex-formgen-v2.md`
  lesen. Auftrag stammt aus Downloads `auftrag-codex-formgen-v2_1.md`.
- Neueste globale Nutzerregel: keine neuen Astra-Starts. Sol/high für heikle
  Kernsysteme, Luna für Routine. Je Baugruppe separater Zuständiger; unabhängiger
  Agent ohne Implementierung prüft vor jeder Nutzermeldung. Hauptagent committet.
- Lokale Commits autorisiert. Kein Push/PR/Merge/Release-Upload. Schwestermodelle
  in Ballon und Formgen v1 ausschließlich lesen. 150 Waffen+9Visiere nur via Geo.
- Nutzer will das ganze System, nicht nur Geo-Eingang: Python-kit-Modelle,
  Rasterizer, Blätter, Specs, Prompts, Viewer, Golden, Release und Figuren.
- Aktuellen Bericht `docs/versions/0.1.md`, Entscheidungen, Lehren und die
  letzten Git-Commits lesen. Status aus Git/Tests, nicht aus Behauptungen ableiten.

## Unverrückbare Referenzentscheidung

Originale bytegleich unter `~/Library/Caches/CubeEscapeFormgen/refs/`:
`robot-ortho-{front,back,side-right,side-left}.png`, tatsächlich4096².
**Gemeinsamer** Frontmaßstab1924/3653mm/px. Frontkopf223px, rechterSeitenkopf216px,
linker218px; nur ausrichten, niemals jede Ansicht auf eigene Gesamthöhe strecken.
Front legt Gelenkhöhen, Standbreite und Fußhöhe fest; Seiten Tiefe/Profil,
Fußlänge/Zehenform; Rücken Rückenmodul. B nur Schalenstil, Konzeptblatt abgelöst.
Fußsohlen Front y3876, Seiten kürzer gezeichnet. Knie710mm, Knöchel234mm,
Hüfte1080mm, Taille1190mm, Schulter1546mm, Ellbogen1275mm, Wrist1028mm,
Hals1690mm. Restdifferenzen dokumentiert in `docs/herkunft-roboter.md`.
1924mm ist Entwurfsvorgabe, keine reale Bildvermessung.
Gelenkringe dunkel, Akzent orange, kein Cyan dort; Emission bisher nur Visier.

## Aktueller Code und offene Ziele

Alle Module unter `formgen/`. Zentrale Versionskonstanten in `versions.py` nur
Hauptagent ändern. `model.load` → normalisiertes Dict; `geom.evaluate` → Netze
in Metern `(x,-f,u)`, `raster.render` → PIL mit JSON-Metadaten und zusätzlichem
`coverage_mask`-Attribut (PIL L). Posen sind 4×4-Matrizen je Teil.

1. **Roboter geometrisch/visuell fertigstellen.** Neutral247Teile, fünf Module
   unter `models/figures/r01_parts/`. Hauptmodell `r01_basic_robot.py`.
   FrontIoU0,8817/Rücken0,8272/Seiten0,8785 und0,8753; alle vier Gesamtprüfungen
   einschließlich Bändern noch nicht bestanden. Schulteranschlüsse, Arm-/Hand-
   und Rückenkontur brauchen Arbeit. Keine Referenzmasken zum Bestehen verformen.
   Innenkerne der Beine sind inzwischen unter die tatsächlichen Innenflächen
   eingezogen (ein erfolgreicher Korrekturdurchgang), sichtbare Streifen behoben.
2. **Ready prüfen.** `r01_poses.py` erzeugt echte starre Pose, Fingergriff,
   Handanker und W01-Anhang. Sechs Daten-/Kontakt-/Freigangtests grün, visuelle
   Abnahme noch offen. W01-Dokument muss dem Helper unposiert zugeführt werden;
   build.py lädt die gecachte Anhanggeometrie und hasht sie nur für Ready.
3. **W01-Formgleichheit vervollständigen.** Planarfase statt2segmentigerRundung,
   konkave/mehrteiligeFasen, Bezier-Schläuche und Textglyphen noch eingeschränkt.
   NativeMesh enthält143 Nullflächendreiecke (Fasen-Triangulator, z.B.mag_release),
   Geoexport entfernt/zählt diese. Ursache im Geometriegenerator beheben.
4. **Blätter/Viewer visuell abnehmen**, KG02 daneben v1 und W01 neben Ballon.
   CUA hat lokale file-URL durch Sicherheitsrichtlinie verweigert. Nicht über
   andere Browser/localhost die konkrete Sperre umgehen. Statische HTML-Prüfung
   vorhanden, keine behauptete Browserabnahme. Neue sichere Möglichkeit nur
   im Rahmen der gültigen Werkzeugrichtlinie.
5. Registry bisherW01/KG02/VS02/R01. Alle159LegacyGeo-Daten extern vorbereitet
   unter `~/Library/Caches/CubeEscapeFormgen/imports/v1/`, Manifest
   `docs/v1-imports.json`; erweitern ohne vollständigen unaufgeforderten Render.
6. Golden und Release nach wirklicher Abnahme finalisieren. Der jetzige
   Probelauf/Golenstand ist technisch, keine Designfreigabe.

## Cache und Verträge

Cachetests vor erstem Pixel unabhängig bestanden, nicht wieder bei null anfangen.
Artefakte: geometry/views/specs/prompts/sheets/previews/geo/viewer plusFonts.
NativeQuelle und statischeImports gehasht; Geo samtSpec-Abhängigkeiten gehasht.
Legacy-Specs bytegleich erhalten; Prompt-Exportpfade relativ, interne Geo-Ladepfade
bleiben absolut für Original-Spec-Lesen. Sheets-Key enthält nur tatsächlich
verbrauchte Layoutmetadaten (PNG-Größe/Labels/Boxen/Skala), keine Pixelbytes;
reine Farbwechsel lassen Layouts imCache, geänderteCallouts invalidieren sie.

LegacyGeo v1 unverändert. W01 braucht `cubeescape-formgen/geometry-spec`v1,
weil v1-Schema W01-ID nicht zulässt; KEIN Alias zu belegtemKG01. Figure eigener
`cubeescape-formgen/figure-geo`v1. Toolgen-Produzentenabnahme fehlt; nicht behaupten.
`geo.export(document,spec_path)`; Paket prüft echte Referenzen/Hashes inklusive
Fonts, HTML/CSS und Zusatz-Specs. Keine externeURL oder absoluteDateipfade imZIP.

## Befehle und Belege

```sh
cd /Users/ffunk/Claude/cubeescape-formgenv2
./check
./ce check
.venv/bin/python -m formgen.build W01 KG02 VS02 R01 --stages specs,prompts,geo
~/Claude/cubeescape-nexogen/ce lock status
~/Claude/cubeescape-nexogen/ce lock gpu -- env PYTHONPATH="$PWD" "$PWD/.venv/bin/python" -m formgen.build W01 KG02 VS02 R01 --jobs 2
.venv/bin/python -m formgen.release_assets W01 KG02 VS02 R01
```

Nexogen-ce wechselt cwd; absolute Pfade/PYTHONPATH sind deshalb nötig.
**Nie alles neu:** Quellen-/Versionen begründet ändern, nur betroffene
Baugruppen/Ansichten bauen; kein pauschales --force.

`tools/robot_reference_masks.py` reproduziert bytegleich Maskenrevision2;
`tools/robot_evidence.py GROUP...` rendert vier registrierte Ansichten inkl.
Deckungsmaske aus denselben Frames unter GPU-Lock. GanzeFigur:
`legs lower_body upper_body head arms`. TeilbandBeine `legs --u-max 986`
ist NICHT vollständige Baugruppenabnahme. Backspiegelung/nichtlinearerFit verboten.

Externe Belege: `~/Library/Caches/CubeEscapeFormgen/evidence/robot/`, `refs/`,
`releases/`; aktuelle Tests/Logs im Versionsbericht. Referenzmasken weiterhin
mitOriginalen visuell gegentesten. Kein Gruppenmodul als abgenommen melden,
solange Bild/Zahlen und unabhängige Prüfung das nicht belegen.

## Technischer Abschluss dieses Checkpoints

Der eigene GPU-Auftrag ist beendet, **kein wartender eigener Job** mehr.
`/tmp/formgen-full4.log`:51gebaut31Treffer nach625sWarten. Wiederholung
`/tmp/formgen-full4-second.log`:0gebaut82Treffer, vorab Cacheeinträge geprüft,
Renderer zur Sicherheit mit Fehlerguard gesperrt (keine neuen Pixel).

Reales Testarchiv mit4Modellen/77Dateien unter
`~/Library/Caches/CubeEscapeFormgen/releases/formgen-v0.1.0-dry-run.zip`,
8.639.449Bytes; `/tmp/formgen-release-real.log`. 66Golden-Hashes des jetzigen
Entwurfs,3gezielteGolden-Testsgrün. Quick128Tests =119pass+9Bildskip,
14,203s; `/tmp/formgen-check-final.log`.

Ready-Bild `out/views/R01/ready.png`, Baugruppenbilder im gleichenOrdner;
HTMLViewer+4Blätter vorhanden. StatischeReleaseprüfunggrün, keineBrowserabnahme.
VorEndrelease noch eine gezielte frische Pixeldeterminismusprobe mit identischer
Geometrie/Parametern in getrenntenProzessen (unterGPU-Lock), nichtalleModelle.
NativeFasen und vierRoboterIoUs bleibenwieobenoffen. Beginne mit Bildbefunden und
separatenKorrekturaufträgen; keineerneuteGrundgerüst-/Cacheimplementierung.
