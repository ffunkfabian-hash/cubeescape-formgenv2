# Changelog

## 0.3.0 Forge — Machbarkeitsnachweis Asset-Backend (BALLON-Kit)

- Waffen-GLB je Blatt-ID über BALLONs unverändertes `tools/blender_build.py` (gepinnter Schnappschuss, Blender 5.2.2 headless): `python -m formgen.asset BA01 …` → `out/assets/<ID>.glb` mit Cache und SHA-Index; noch keine Pipeline-Stufe (nach 0.4).
- BA01 bytegleich zu BALLONs Neubau am Pin, dreiecks- und materialgleich zu BALLONs Cache-GLB (`tools/ballon_compare.py --asset`); BB01/BC01 gebaut; Kit baut `xprof` (16/16 Piloten objektgleich zum Unity-Export). Spielpaket (FBX, AAA-Atlas) als Probe. Bericht: [0.3](docs/versions/0.3.md).

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
