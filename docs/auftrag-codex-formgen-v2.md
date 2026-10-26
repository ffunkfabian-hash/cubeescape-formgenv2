# Auftrag an Codex: Formgen v2 – Konzeptblattwerk wie v1, in ballons Designsprache, mit Roboter

Stand 26.10.2026, aus der Sitzung „Image-to-3D für KI-Agenten“ (Claude-App). Für eine **frische Codex-Sitzung** geschrieben,
Repo `cubeescape-formgenv2` (neu, leer). GPT Astra, Reasoning `high`. Es gelten die globalen Regeln aus `~/.codex/AGENTS.md`; eine
`AGENTS.md`/`CLAUDE.md` für dieses Repo ist Teil des Auftrags (Muster: `cubeescape-formgen`).

## Entscheidungen des Nutzers (26.10.2026)

| Entscheidung | Grund |
|---|---|
| **v2 kann alles, was v1 kann:** Modelle in Python entwerfen, Blätter rendern (eigener Rasterizer, kein Blender), Specs, Prompts, Viewer, Golden, Release-Assets. | bewährter Ablauf, keine Abhängigkeit vom Mac für die Bildstufe |
| **Modellsprache = ballons `kit`-Vokabular.** Formen `prof`, `box`, `cyl`, `plan`, `frame`, `multi`, `tube`, Autorenmaß mm (`f` vorn, `u` oben, `x` links), Materialrollen und Skins aus `docs/stilhandbuch.md` §4/§5, Gestaltungsregeln §2, Schlichtheitsbudget. `eng.py`/`prism` aus v1 wird nicht fortgeführt. | Designsprache übernehmen heißt dieselbe Sprache sprechen; ballon kann v2-Modelle 1:1 in Blender bauen |
| **Erweiterung um Körper:** neue Formen `hull`, `loft`, `surface`, `prism2` (Schnitt aus Seiten- und Frontprofil) für Roboter und andere Figuren; Figurenblatt mit Baugruppen, Ankern, Explosionsansicht. | Waffen sind Seitenprofil mit Breite, Körper nicht |
| **Nie alles neu rendern.** Cache je Artefakt mit Versionen je Komponente; ohne `--force` nur Fehlendes/Veraltetes. | Hauptgrund für v2 |
| v1 bleibt eingefroren und lesbar; die 150 Waffen und 9 Visiere kommen in v2 über v1s Geo-Export (`KXnn.geo.json`), nicht über die alten Modelle. | kein doppelter Bestand, nichts geht verloren |
| KI-Generierungsmodelle nur als Zusatzoption, nie Voraussetzung. Konzeptbilder sind Zielbilder, keine Quelle für Maße. | kostenlos, reproduzierbar, messbar |
| **Ein Modell liegt zu jedem Zeitpunkt in genau einem Repo.** Entwurf und Blätter in formgen v2; geht ein Modell ins Spiel, wandert das Modul nach ballon, und formgen rendert es ab dann aus ballons Geo-Export (Liste `docs/herkunft.md`: Modell → Repo, Datum). | zwei Autorenorte dürfen nicht driften |

## Auftrag

**1. Modellsprache (`formgen/model.py`).** Ein Modell ist ein Python-Modul wie in ballon (`basic/weapons/wNN_*.py`): `INFO`,
`PARTS` (Liste von Dicts mit `id`, `assembly`, `shape`, Maßfeldern, `role`, optional `bevel`, `cuts`, `parent_part`, `move`,
`label`, `decals`), `ASSEMBLIES`, `ANCHORS` (`Socket_*`), optional `POSES`. Felder und Bedeutung exakt wie `cubeescape-ballon/basic/kit.py`
und `docs/stilhandbuch.md` §6 – Abweichungen nur dokumentiert in `docs/modellsprache.md`. Neue Formen für Körper:
`hull` (Punkte → konvexe Hülle), `loft` (Querschnittsringe, optional Wandstärke), `surface` (Vertices/Faces mit Innenversatz),
`prism2` (Seitenprofil (f,u) und Frontprofil (x,u), extrudiert und geschnitten). Diese vier gehören als Vorschlag auch nach ballon
(`kit.py`), damit die Sprache deckungsgleich bleibt; der Vorschlag steht als Datei `docs/vorschlag-ballon-kit.md` im Repo.

**2. Geometrie-Auswertung (`formgen/geom.py`).** Die Formen werden in numpy zu Netzen ausgewertet. `cuts` (Durchbrüche, Fugen)
und Fasen über `manifold3d` (pip; exakte Booleans ohne Blender) – fällt das Paket aus, werden `cuts` als Decal-Flächen angedeutet
und im Blattkopf vermerkt. Ergebnis je Modell ist dasselbe Teilemodell, das auch `geo.json` liefert (unten), damit Rasterizer
und Blatt nur eine Eingangsform kennen.

**3. Zweiter Eingang: `geo.json` (`formgen/geo.py`).** Liest Formgen v1s `cubeescape-design/geometry-spec` Version 1 (alle
KC01–KJ25, VS01–VS09 aus dem Release-Asset) und ballons `cubeescape-ballon/geo` Version 1, sobald es das gibt (Blender-gebaute
Modelle mit echten Fasen). Schema- und Versionsprüfung, unbekannte Felder ignorieren.

**4. Rasterizer (`formgen/raster.py`).** Aus v1 übernommen (Quellenhinweis): Z-Buffer, Toon in 4 Stufen, Konturen aus Flächen-ID,
Supersampling, Objektraum-Texturen. Erweitert um Materialrollen (Schale hell satiniert, Graphit dunkel matt, Gummi, Eloxal,
Metall, Trim blank, Akzent orange, Energie ungeschattet, Glas halbtransparent) und Skins aus `skins.toml` (Spiegel von ballons
`SKINS`; Farben nur dort, nie in Modellen). Standardhintergrund grau (`--bg mid`), kein Bloom.

**5. Blätter (`formgen/sheet.py`, `sheet_figure.py`).** Waffenblatt XL wie v1 (`xl.py`/`views.py`: Isometrie ohne Visier mit bis zu
8 Beschriftungen, sechs Orthos gleicher Maßstab mit Bezugslinien, Detail Abzug, Visier separat, Materialfelder, vier Skins,
Prompt DE/EN). Figurenblatt neu: Front/Seite/Rücken/Schräg, je Baugruppe ein Blatt mit Teileliste, Explosionsansicht entlang der
Anker, Posen `idle`/`ready` (Waffe aus einem Waffenmodell in der Hand, Anker `Socket_Hand`). Ausgabe `out/sheets/<ID>.dc.html`,
Vorschau WebP, Viewer `out/index.html`.

**6. Specs und Prompts (`formgen/spec.py`, `prompts.py`).** Weapon-Spec 2 und Sight-Spec 2 unverändert kompatibel (Toolgen liest sie);
neu `figure-spec` 1 für Roboter (Baugruppen, Teile, Anker, Posen, Maße aus dem Modell); Geo-Spec 1 wie v1 als Release-Asset.
Prompts aus dem Masterprompt-Vokabular.

**7. Cache (`formgen/cache.py`, `build.py`) – die zentrale Regel.** Schlüssel je Artefakt = sha256 über (Modellquelle oder Geo-sha,
Artefakt-Art, Parameter, Version der beteiligten Komponente: `geom.VERSION`, `raster.VERSION`, `sheet.VERSION`, `spec.VERSION`).
Cache `~/Library/Caches/CubeEscapeFormgen/`, Manifest `out/manifest.json`. `build` ohne Argumente baut nur Fehlendes/Veraltetes,
parallel in Prozessen, Ausgabe `n gebaut · m aus dem Cache`. `--force` alles; `--force-views`/`--force-sheets` gezielt. Eine
Renderer-Änderung erhöht `raster.VERSION` und invalidiert nur Ansichten; Specs und Layouts bleiben. Release-Stichprobe wie v1.

**8. Roboter als erstes Figurenmodell (`formgen/models/figures/r01_basic_robot.py`).** Fünf Baugruppen Kopf, Arme, Oberkörper,
Unterkörper, Beine; Anker `Socket_Neck`, `Socket_Shoulder_R/L`, `Socket_Elbow_R/L`, `Socket_Wrist_R/L`, `Socket_Waist`,
`Socket_Hip_R/L`, `Socket_Knee_R/L`, `Socket_Ankle_R/L`. Arme als Teile-Dicts aus ballons `basic/arms/robot_arm.py` übernommen
(Quellenhinweis, Hash). Entwurfsmaße aus dem Codex-Stand `~/Documents/Codex/2026-10-26/…/outputs/roboter-massfigur-v2/` –
Schulteranker 520/1560, Hals 1665, Taille 1160, Hüfte 1020, Beine 420/420, Höhe 1924 – im Docstring als Entwurf gekennzeichnet;
Formprinzipien von dort: offene Schulterkappen mit Anschlussring, gefaltete Brust mit Mittelgrat, breiter Schulterträger,
schmales Rückenmodul, getrennte Bein-Vorder-/Rückschalen mit Fuge, eingefasste Füße, Helm mit feinerer Facettierung. Zielbilder:
Formstudie B und Roboterkonzeptblatt vom 26.10.2026 (den Nutzer in der Sitzung darum bitten, unter
`~/Library/Caches/CubeEscapeFormgen/refs/` sichern). Abnahme messbar: Silhouette des gerenderten Modells gegen das Zielbild,
IoU ≥ 0,90 Front und Seite, kein Höhenband unter 0,92 oder über 1,08 (Werkzeuge `compare_silhouettes.py`, `landmarks.py` aus dem
Ordner `img2mesh/` des Nutzers nach `tools/` übernehmen, Quellenhinweis). Jede Zahl hat eine Herkunft: Vorgabe, gemessen, Annahme.

**9. Pilotwaffe in der neuen Sprache.** `formgen/models/weapons/w01_auto_rifle.py` als Übertragung von ballons
`basic/pilot/w01_auto_rifle_v21.py` (Teile-Dicts übernehmen, nicht neu entwerfen). Blatt daneben mit dem v1-Blatt KG02 und ballons
Blender-Stills vergleichen: Form identisch, Material als Toon-Rolle lesbar.

**10. Tests und Check.** `tests/test_cache.py` (zweimal bauen, zweiter Lauf 0; Modell ändern → nur dessen Artefakte), `test_golden.py`
wie v1, `test_model.py` (Schema der Modellsprache, stabile IDs, Anker auf Teilen, Baugruppen vollständig), `test_geo.py`,
`test_figure.py` (Baugruppen schließen aneinander an, Posen kollisionsfrei im Groben). `./check` ohne Bildstufe; Bildstufe mit
`heavy_lock` auf dem Mac.

## Dateien

```
cubeescape-formgenv2/
  README.md AGENTS.md CLAUDE.md CHANGELOG.md .ce-repo.json  config.toml  skins.toml  requirements.txt
  formgen/   model.py geom.py geo.py raster.py sheet.py sheet_figure.py spec.py prompts.py cache.py build.py viewer.py release_assets.py
  formgen/models/weapons/   w01_auto_rifle.py …      formgen/models/figures/   r01_basic_robot.py
  docs/      modellsprache.md (Vokabular, Abweichungen zu kit.py), vorschlag-ballon-kit.md, figure-spec.md, cache.md,
             masterprompt.md (Kopie aus v1), ENTSCHEIDUNGEN.md, LESSONS.md, versions/
  tests/     test_cache.py test_golden.py test_model.py test_geo.py test_figure.py golden.json
  out/       specs/ prompts/ (im Repo); sheets/ previews/ index.html geo/ (gitignoriert, Release-Asset)
```

Aus v1 übernehmen (mit Quellenhinweis): `raster.py`, `xl.py`/`views.py`, Schriften, `docs/masterprompt.md`, Prompt-Vokabular,
`make_viewer.py`, `release_assets.py`, Golden-Mechanik. Nicht übernehmen: `eng.py`, alle Modelle `c02.py`…`j25.py`, `vsmodels.py`.
Nicht anfassen: `cubeescape-formgen` (nur lesen), `cubeescape-ballon` (nur lesen; Vorschläge als Datei hier), Toolgen, Cube Escape.
Branch `codex/formgen-v2-first`; Commits auf dem Branch erlaubt, Push/PR/Release nur auf Wunsch des Nutzers.

## Unteragenten

Ausdrücklich erwünscht. Aufteilung: `geom.py` + `model.py` (Sprache und Auswertung, inkl. `manifold3d`), `raster.py` + Materialrollen,
`cache.py` + `build.py` + Tests, `sheet.py`/`sheet_figure.py`, `spec.py`/`prompts.py`, Roboter-Modell je Baugruppe. Der Hauptagent
legt zuerst `docs/modellsprache.md` und ein Mini-Modell (zwei Teile, ein Anker) an, gegen das alle arbeiten, hält die
`VERSION`-Konstanten und committet. Ein Prüf-Unteragent, der nichts gebaut hat, fährt `./check`, Cache-Test, Blattvergleich mit v1
und den Silhouettenvergleich des Roboters, bevor etwas an den Nutzer geht.

## Prüfen

- `./check` grün; `python3 -m formgen.build` zweimal: zweiter Lauf `0 gebaut`.
- KG02 aus v1-Geo mit v2 gebaut neben dem v1-Blatt: gleiche Teile, Beschriftungen, Lesbarkeit.
- Pilotwaffe aus der neuen Modellsprache neben ballons Blender-Stills: gleiche Form, Material als Rolle erkennbar.
- Roboterblatt mit Overlays Front/Seite und IoU-Werten; Figurenblätter je Baugruppe; Explosionsansicht.

## Fertig wenn

- Blätter, Specs, Prompts für KG02 (v1-Geo), W01 (neue Sprache) und R01 (Roboter) liegen vor; Viewer zeigt sie; Release-Probelauf durch.
- Cache-Test grün, Manifest erklärt jeden Bau- oder Cache-Treffer.
- `docs/modellsprache.md` und `docs/vorschlag-ballon-kit.md` (die vier Körperformen) sind fertig; der Nutzer hat den Roboter gesehen.
- Bericht `docs/versions/0.1-<name>.md`, `ENTSCHEIDUNGEN.md`, `LESSONS.md`.

## Reihenfolge

1. Gerüst, `AGENTS.md`, `docs/modellsprache.md`, Mini-Modell.
2. `cache.py`/`build.py` mit Dummy-Artefakt – Cache-Test grün, bevor ein Pixel gerendert wird.
3. `geom.py` für `prof`/`box`/`cyl`/`plan`, dann `raster.py` aus v1 – erste Ortho der Pilotwaffe.
4. `multi`, `frame`, `tube`, `cuts`/Fasen (`manifold3d`), Materialrollen, Skins – Pilotwaffe komplett, Vergleich mit ballon.
5. `geo.py` – KG02 und VS02 aus v1-Geo, Golden.
6. Körperformen, Roboter Baugruppe für Baugruppe (Beine, Unterkörper, Oberkörper, Kopf, Arme einhängen), nach jeder Baugruppe
   Silhouettenvergleich der betroffenen Höhenbänder.
7. Figurenblatt, figure-spec, Viewer, Release-Probelauf, Bericht.
