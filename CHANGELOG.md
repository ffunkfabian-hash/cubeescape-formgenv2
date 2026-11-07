# Changelog

## 0.12.0 Livery — Roboterlinien B–E, Skinwechsel in der 3D-Ansicht

- Roboter: vier neue Linien Night Watch (B), Signal (C), Field Olive (D), Cobalt Line (E) für beide Basic-Typen, zusammen zehn Blätter `RA01`–`RE02`. Eigener Skin je Linie (`nachtwache`, `signal`, `feldoliv`, `kobaltblau`, nur Farben, `robot = true`), C und D ändern zusätzlich den Armquerschnitt (`arm_bulk`). `python -m formgen.robot --list` zeigt das Register ([Roboter](docs/robot.md#linien-und-liveries-012)).
- Website: Die 3D-Seite wechselt den Skin live (Roboter: Roboter-Skins, Waffen: Farbskins), der Skin steht in der Adresse und bleibt beim Blättern. Roboterseite mit Suche und Linienfilter, Farbpunkte des Skins auf Roboter- und Waffenkarten, Roboter nach Kennbuchstabe sortiert ([Website](docs/website.md#skinwechsel)).
- [Bericht](docs/versions/0.12.md)

## 0.11.4 Patch skinfix

- Blatt: Der Haupt-Skin der Variante steht als erstes, markiertes Feld in der Skin-Übersicht; bisher fehlte er bei 8 von 12 Linien.
- GLB und 3D-Seite: `asset.skin_glb` schreibt die Skinfarben der Linie in die Materialien, Skin im Cache-Schlüssel; bisher trugen alle Waffen die Standardfarben.

## 0.11.3 Patch pin40

- Pin auf Agent Tools 0.40.0, sonst keine Änderung.

## 0.11.2 Patch pin37

- Pin auf Agent Tools 0.37.0 (Waybill), sonst keine Änderung.

## 0.11.1 Patch runde

- Trimline-Runde: Pin auf Agent Tools 0.36.2, `AGENTS.md` ohne veraltete Kopien globaler Regeln.

## 0.11.0 Keystone — RoboterBasic-02 als RA02

- RoboterBasic-02 steht im Register und auf der Website: 554 Teile, gemessen aus `robot_v2.blend`, Blatt `RA02`, 3D und Markierung wie RA01. Silhouette gegen die Quelle bestanden (Front und Rücken IoU 0,9273, Seiten 0,9995).
- `silhouette --typ` misst jeden Basic-Typ in seiner Referenzhaltung.
- [Bericht](docs/versions/0.11.md)

## 0.10.0 Chamfer — RoboterBasic-01 optisch auf dem Stand der Waffen

- Fasen: 344 Teile von RA01 tragen Fasen wie BALLON 14bd78d (`formgen/robot/bevel.py`, 30°, zwei Segmente, nach den Fugen); Helm H 80 und Leitungen unverändert. Silhouette besser als zuvor, IoU ≥ 0,9990.
- Cycles: `tools/robot_cycles.py` misst Weiß-Graphit am AAA-Licht; 6 von 9 Rollen im Rahmen, vom Nutzer am Bild angenommen. Eingangsfarben in `[skins.weiss_graphit.aaa]`, GLB und Blatt unverändert.
- [Bericht](docs/versions/0.10.md)

## 0.9.0 Sentry — RoboterBasic-01 im Repo, Website mit Navigation, 3D und Markierung

- Roboter: RoboterBasic-01 (`RA01`) mit zehn Einzelteilen, vier Baugruppen und A-Position als Python-Modell unter `formgen/models/robot/`, Körper und Arme parametrisch aus BALLON 14bd78d, Helm H 80 als offen ausgewiesene Flächendaten. Register `data/robots.toml` als Linie × Basic-Typ, vorbereitet für `RA02`, Bau `python -m formgen.robot` ohne Blender, Skin `weiss_graphit`, keine Critic-Verbindung ([Roboter](docs/robot.md)).
- Website: `out/index.html` mit Navigation, getrennte Seiten Waffen und Roboter, 3D-Ansicht und Markierung für alle 205 Modelle, offline per `file://`, Three.js 0.186.1 fest im Repo ([Website](docs/website.md)). R01/R02 erscheinen nicht mehr.
- Format `formgen/change-request` v1 für Waffen und Roboter, Altdateien `formgen/robot-change-request` werden migriert. 3D-Daten als eigenes Release-Zip.
- Regel „Roboter ruhen / Zielbilder anfordern“ gestrichen (Nutzerentscheid 05.11.2026).

## 0.8.2 — Patch kern-sweep

- Nur Doku und Konfiguration: AGENTS.md auf den harten Kern 1–8 und Repo-Eigenes gekürzt (CLAUDE.md importiert sie), LESSONS auf wiederkehrende Fallen gekürzt (Rest in `LESSONS-lang.md`), Werkzeug-Pin 0.35, `core_paths`, `docs.changelog`.

## 0.8.1 — Patch visierfix

- Visiertausch: `sight_emitter` behält die Leuchtbewegung des Grundvisiers (BE10–BH10, BJ10–BL10); BE14–BH14 sitzen wie der Pilot seitlich auf der Schiene (BALLON `side_mount`) statt im Rohr.
- Raster: Trommel (`cylinder`, alle Linien BASIC-04) ohne helle Innenkanten, sie wirkte wie Glas; Netz, Normalen und GLB waren in Ordnung.

## 0.8.0 Hallmark — Design-Serien wie in v1: vier eigene Formensprachen

- Vier neue Linien × 17 Typen (68 Blätter, gesamt 204): J Cold Shard (Stealth-Facetten), K Bolt Works (Werkstatt-Prototyp), L Cube Blocks (Cube-Escape-Farbwelt), M Pearl Drift (organisch-glatt). Neuer Parameter `series` (`formgen/series.py`): Verkleidungen außen auf dem Piloten aus BALLONs Kit-Vokabular, eigene Palette (`skins.toml`, `formgen = true`) und Leuchtführung.
- Funktion bleibt: vorhandene Teile, Anker, Weltpunkte, Aktionen unverändert; Schalen schneiden sich um Wege bewegter Teile, Griffe, Hände, Auswurf, Leuchtanzeigen, Sichtlinie und Mündung (`tests/test_series.py`, Gegenprobe rot). Bake-Paket 2 je Serie von BALLON angenommen. Vielfalt gegen A: Schwelle 0,95 statt 0,98. Bericht: [0.8](docs/versions/0.8.md).

## 0.7.0 Waypoint — BALLON 0.41/0.42 übernommen: Weltpunkte, Paket 2, neuer Pin

- BALLON-Pin fe4a5dc (0.42); Bau über `blender_build.main(W, base)` (`basic/variant.as_module`) statt Modul in `sys.modules`, Bake über `export_unity.bake_weapon(arms=False)` – Waffenatlas ohne Arme, Regel beider Wege. Linie A weiter bytegleich zu BALLONs Neubau.
- Weltpunkte `POINTS` (Auswurf, Griffkontakte) folgen im Generator ihren Teilen wie die Anker (Dehnen, Stauchen, Spiegeln, Magazin, Tausch, drop); Bake-Paket `format_version` 2 mit Datensatz `model`, Format 1 bleibt lesbar. Probe BG02 in BALLON angenommen (Unity-Tests grün), als Paket 1 abgelehnt. Bericht: [0.7](docs/versions/0.7.md).

## 0.6.0 Hangar — Alle Linien auf den Spiel-Piloten, Asset-Stufe in der Pipeline

- Nutzerentscheid 242: jede Linie A–H nimmt den neuesten BALLON-Piloten (`base = "pilot"`, heute v2.1) als Grundform; BASIC-16/17 ohne Piloten bleiben auf der Formstudie, im Blatt „Formstudie – kein Pilot“. Linie A = Pilot unverändert. Vielfalt auf Pilotbasis: C/E zusätzlich kurze Mündung und Magazin, D längere Wurfarme (sonst 6 Blätter über 0,98); 119/119 ≤ 0,9752.
- Stufe `asset` fest nach `geometry`: GLB je Blatt über BALLONs unverändertes Kit am Pin, Stufen-Cache, Index `out/assets/index.json`; AAA-Bake nur mit `--bake <IDs>` unter `ce lock gpu`, gecacht als `out/assets/<ID>.bake.zip`. Linie A 17/17 bytegleich zu BALLONs Neubau (`tools/line_a_parity.py`). Blatt-Spec Version 3 (`pilot`) mit Migration 2→3. Bericht: [0.6](docs/versions/0.6.md).

## 0.5.0 Forge — Machbarkeitsnachweis Asset-Backend (BALLON-Kit; Arbeitsnummer 0.3, Nutzerentscheid 239)

- Waffen-GLB je Blatt-ID über BALLONs unverändertes `tools/blender_build.py` (gepinnter Schnappschuss, Blender 5.2.2 headless): `python -m formgen.asset BA01 …` → `out/assets/<ID>.glb` mit Cache und SHA-Index; noch keine Pipeline-Stufe (nach 0.4).
- BA01 bytegleich zu BALLONs Neubau am Pin, dreiecks- und materialgleich zu BALLONs Cache-GLB (`tools/ballon_compare.py --asset`); BB01/BC01 gebaut; Kit baut `xprof` (16/16 Piloten objektgleich zum Unity-Export). Spielpaket (FBX, AAA-Atlas) als Probe. Bericht: [0.5](docs/versions/0.5.md).

## 0.4.0 Mosaic — Variantenbaukasten

- Acht Linien × 17 Typen = 136 Blätter: neu D Refit, E Lantern, F Heavy Frame, G Skeleton, H Long Watch; B/C erhalten Wurfarmlänge (Bogen war formgleich). Alle acht BALLON-Skins im Einsatz.
- Baukasten aus BALLON-Bausteinen: Visiertausch (Visier-Baukasten v3, Zielfernrohr nur 03/09/11), Schaft S1/S2, Griff v2.1, Magazin, Mündung, Leuchtstreifen, Wurfarme; v2.1-Piloten als zweite Grundform (`base = "v21"`), dafür Form `xprof`.
- Gesteuerter Zufall: Bereiche je Linie, Seed aus Blatt-ID + Linie, bitgleich mit PYTHONHASHSEED 1/42; Blatt-Spec v2 mit Migration aus v1. Vielfaltstest (IoU ≤ 0,98, gemessen ≤ 0,973) und Designvertrag-Prüfung. Bericht: [0.4](docs/versions/0.4.md).

## 0.2.0 Anvil — Waffen-Pipeline auf BALLON-Basis

- Neuaufbau nach v1-Prinzip: Variantenregister (A Baseline, B Long Reach, C Close Quarters) × 17 BALLON-Typen = 51 Blätter mit Spec, Prompts, Ansichten, Vorschau, Viewer und Release-Probelauf.
- Grundform je Typ ist BALLONs Modell per Quellhash (gepinnter Commit, `git archive`, nur gelesen); Generator ändert nur über Parameter (front/rear/drop/Skin). Baseline gegen BALLONs GLB: Seiten-IoU ≥ 0,985, Maße auf 0,01 mm (außer drei Zielfernrohr-Höhen, BALLON-Kegeldefekt).
- Stufen-Cache mit Quellen-Closure des Stufencodes und Umgebung im Schlüssel; Manifest gebündelt, warmer Lauf aller 51 Blätter 3,2 s. Blatt-Spec `formgenv2/weapon-sheet-spec` v1 mit Schema und Migrationspflicht.
- Entscheid 234 A: R01-Rücken-Ausnahme je Referenzmaske (IoU ≥ 0,88, Band 0 ≤ 1,10); Seiten-Band 0 (1,42) bleibt Entscheidung. Bericht: [0.2](docs/versions/0.2.md).

## 0.1.0 Contour — technischer Zwischenstand, nicht abgenommen

- Kit-Modelle, manifold3d-Geometrie, eigener Rasterizer und Artefaktcache; Legacy-Geo bleibt separat kompatibel.
- Blätter, Specs, Prompts, Galerie, Geo-Export und lokal prüfbarer Releasepfad; BASIC-Roboter als neutraler und Ready-Entwurf.
- GEOM4/RASTER5: echte Bfont-Glyphen, vier Endringfasen, Legacy-Herooberflächen und einzeln zugängliche159Geo-Importe;202Quick- und24Rastertests, vollständiger Zweitlauf0gebaut/82Treffer.
- GEOM5/SPEC4: fünf zusätzliche W01-Fasen, Spec2-konforme Flächenfarbanteile und geometrisch geprüfte Schulter-/Nacken-/Hüftkorrekturen;221Quick-Tests,33Bauten/49Treffer, danach0/82; R01nun3/4IoUs und37/40Breitenbänder, weiterhin nicht abgenommen.
- GEOM6: vier Cut-Profilfasen und eine echte Blindtaschenfase, toleranzfeste Butt-Pad-Stationen, lokale Oberarmwange;55gezielteTests,234Quicktests mit gezielt behobenem Alt-Testfehler,31Bauten/51Treffer, danach0/82. Sieben variable Cut-Fasen und Roboter-Gesamtabnahme bleiben offen.
- GEOM7: sieben Post-Cut-BRep-Fasen mit zwingender Selbstschnittprüfung, Kopf-Innenwände und lokale Hinterkopf-Freistellung;244Quicktests,31Bauten/51Treffer, danach0/82. Reale Blender-Abweichungen dokumentiert; R01weiter3/4IoUs und37/40Breitenbänder.
- GEOM8: gemeinsamer konservativer BRep-Fasenclamp, alle sieben Blendervergleiche verbessert; maximale Volumendifferenz 0,499 %, Bounds 0,083772 mm. 247 Quicktests, 31 Bauten / 51 Treffer, danach 0 / 82; R01-Abnahme weiter offen.
- Offene Modell-/Bild-/Releaseabnahme und Prüfbelege: [Versionsbericht](docs/versions/0.1.md).
