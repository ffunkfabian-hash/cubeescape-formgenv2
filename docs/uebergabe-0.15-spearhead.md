# Übergabe 0.15 „Spearhead“ – EXTENDED-01 Automatikgewehr

Stand 23.11.2026, Sitzung 1 (Sichtung) → frische Sitzung (Entwurf, Bau, Renders, Prüfung). Version reserviert: Branch
`claude/formgenv2-0.15-spearhead` (origin), Modell Opus `high`. Die Sichtung ist abgeschlossen; nichts gebaut, nichts gerendert.

## Auftrag (Nutzer, Wortlaut gekürzt auf die Anforderungen)

EXTENDED-01: vollständig neues, eigenständiges Sci-Fi-**Automatikgewehr** auf Grundlage von **BASIC-01**. Kreative Individualität von
Formgen v1 + hochwertige 3D-Modellierung und Designqualität von Formgen v2.
- Eigene Silhouette, eigene Proportionen, eigene Formarchitektur; eindeutig als Automatikgewehr erkennbar.
- Designsprache von BASIC bleibt (gleiche Produktfamilie); außergewöhnlich, kreativ, aber industriell glaubwürdig, harmonisch, hochwertig.
- Geometrie eigenständig entwickeln – **nicht** BASIC umbauen oder Teile anbringen. Starke Hauptformen, differenzierte Gehäusestrukturen,
  saubere Übergänge, hochwertige Hard-Surface-Details.
- Arbeitsweise: mehrere unterschiedliche Formideen → die überzeugendste wählen → vollständig als 3D-Modell mit vorhandenen Werkzeugen →
  echte Renderings aus mehreren Perspektiven → Schwächen selbst verbessern.
- **Unabhängig von bisherigen EXTENDED-Experimenten.** Nur BASIC-01, Formgen v1 und Formgen v2 als Referenz.
- Ergebnis: ein einziges, vollständig ausgearbeitetes Automatikgewehr. Leitgedanke: gleiche Designfamilie, neue individuelle Form,
  höchste gestalterische Qualität.

**Tabu (frühere Experimente, nicht öffnen):** Cache-Ordner `~/Library/Caches/CubeEscapeFormgen2/extended-*`, `extended-restart.*`,
`extended-formlabor-06`, `bulkhead-abnahme.*` und der Branch `claude/formgen-hybrid-rifle-9eb969`.

## Referenzen (gesichtet)

| Quelle | Ort | Was daraus zählt |
|---|---|---|
| BASIC-01 Pilot v2.1 | Snapshot `~/Library/Caches/CubeEscapeFormgen2/ballon/fe4a5dc4…-85ed1991/basic/pilot/w01_auto_rifle_v21.py` (284 Z.) | Familie: Creme-Oberteil `shell` über Graphit-Unterteil, lange Haube kragt frei über den Lauf, offener Laufraum mit Kühlrippen, Kern links (Blickfang, `energy` hinter `glass` + `trim`-Ring), Seitenpaneele `anodized` mit 4 `trim`-Schrauben, Chevronband `accent` (einziges Grafikelement), Schriftzug, skelettierter Schaft mit Puffer, gekrümmtes Magazin mit Fenster/Patronen, Kompensator mit 2–3 breiten Schlitzen |
| BASIC-01 Bilder | `~/Library/Caches/CubeEscapeFormgen2/0.8/belege/aaa/BA01_hero.png`, `BA01_side.png` | Vergleichsbild für „gleiche Familie, andere Form“ |
| Stilhandbuch BALLON | `~/Claude/cubeescape-ballon/docs/stilhandbuch.md` §2–4 | Schlicht zuerst; drei Detailebenen 60/30/10; Negativraum; Schichtung 2–3 mm Stufe; genau ein Blickfang; mehrstufige Front; Budget: ≤ 3 Leuchtfunktionen, 1 Grafikband, 1 Schrift, ≤ 3 Orange-Bedienfunktionen, Schrauben nur an Panzern/Paneelen; Teilungen eher 70:30 statt 50:50; Akzente kameranah (Visier, Verschluss, linke Seite); Dreiecke Ziel 20 k, Grenze 50 k |
| Formgen v1 | `~/Claude/cubeescape-formgen/claude/generator/` (`g02.py` Keilschaft, `f02.py` Bullpup + Tragebügel als Visierschiene, `c02.py`), Bild `claude/output/previews/KJ02.webp` (Black Ice: Facettenkörper, Keilschaft), `claude/reference/crops/w02.png`, `docs/masterprompt.md` | Stärke von v1: **eine mutige Gesamtarchitektur je Waffe** (Bullpup, Bügel, Keil, Facetten), klar lesbare Funktionskomponenten, keine schwebenden Teile; Schwäche: grobe 2D-Extrusionen |
| Formgen v2 | `docs/generator.md` (Serien, Designvertrag, Vielfalt), `formgen/series.py` | Grenze: Serien setzen nur Schalen auf Piloten; „ganz neue Gehäuse brauchen eigene Bausteine“ → EXTENDED-01 ist ein **eigenes Modell** |

## Technik: so entsteht das Modell mit den vorhandenen Werkzeugen

**Vokabular (BALLON `basic/common.py`, `basic/kit.py`).** Maße mm, f nach vorn, u nach oben, **x nach links** (Kern links = x > 0).
Socket_Hand = (0,0,0) auf der Griffachse; BASIC-01: Laufachse `BORE = 106`, Schiene ab u 135, Länge ≈ 0,93 m (Mündung f ≈ 616, Schaft bis f ≈ −299).
Formen (`kit.build_shape`): `prof` (Seitenprofil pts (f,u), Breite w, Versatz x), `box`, `cyl` (axis f/x/u, c, a0..a1, r, `r1` = Kegel,
`r_in` = hohl, segs), `plan` (Draufsicht (f,x), u0..u1), `xprof` (Querprofil (x,u) relativ cu, f0..f1 – für Querschnitte mit Schrägen!),
`xbox`, `frame` (Rahmen quer zur Achse), `multi` (items vereinigt), `tube` (Bezier-Leitung), `text`. `cuts` = Boolesche Differenz (EXACT)
mit beliebigen Formen. Fase: `bevel` mm, Winkelgrenze 30°, 2 Segmente, `harden_normals`. Radien `R_BODY 5`, `R_MID 3`, `R_SMALL 1,5`,
`R_FINE 0,8`, `R_SOFT 6,5` (nur Griff Gummi), `SEAM 1` mm Fuge. Rollen: `shell`, `graphite`, `rubber`, `anodized`, `sight_anod`,
`dark_metal`, `metal`, `trim`, `accent`, `energy`, `brass`, `decal`, `glass`. Bausteine wiederverwendbar (Familienteile, keine Umbauten):
`grip_v21(top=42)` (BGM-1), `reflex_sight_v21(f,u)` (liefert Teile + Anker), `rifle_mag`, `selector`, `charging_handle`, `rail`,
`screws`, `mirror`, `cut_box`, `glow`. Pflichtfelder je Modell: `META` (id, type `auto_rifle` …), `ASSEMBLIES` (wie BASIC-01:
receiver, barrel, ammo, sight, grip_controls, support, stock, mechanism), `PARTS`, `ANCHORS` (Socket_Hand, Socket_SupportHand,
Socket_Muzzle, Socket_MagWell, Socket_Charge + Visieranker), `POINTS` (`basic.variant.collect`), `ACTIONS` (fire_auto, reload_empty).

**Rendern (unverändertes BALLON-Werkzeug).** `tools/blender_build.main(W=<dict>, base=<Modul>, argv=[...])` im Kit-Snapshot
`~/Library/Caches/CubeEscapeFormgen2/ballon/fe4a5dc4e026fba503bf9354da2fb055cbc7e724.kit` baut Datensätze (fehlende Felder vom Grundmodul
`basic.pilot.w01_auto_rifle_v21`), schreibt `.blend`, `.glb`, Spec mit Maßen/Dreiecken und rendert mit `--views --aaa --skins standard
--samples N --res N --bg mid` die AAA-Ansichten (`VIEWS` + `hero_p` 70 mm Perspektive; eigenes `HERO` möglich). Vorlage für den
Aufruf: Wrapper in `tools/series_evidence.py` (Blender headless `-b --factory-startup -P wrapper.py -- job.json`, `BASIC_OUT` setzt den
Ausgabeordner; Bilder `skin_*.png`). Schwere Läufe nur unter `~/Claude/cubeescape-nexogen/ce lock blender -- …` (CPU) bzw. `gpu` mit `--gpu`.
Blender: `/Applications/Blender.app/Contents/MacOS/Blender`. Belege außerhalb des Repos, z. B. `~/Library/Caches/CubeEscapeFormgen2/0.15/belege/`.

**Umgebung.** Worktree-venv angelegt (`.venv`, `requirements-lock.txt`). Snapshot-Import wie `formgen/ballon.load` (Snapshot auf `sys.path`,
`basic.*` danach aus `sys.modules` entfernen).

## Vorgeschlagener Zuschnitt (Version, > 300 Zeilen)

1. Modell `formgen/models/extended/e01_<name>.py` im BALLON-Vokabular (eigene Geometrie; Familienbausteine nur für genormte Schnittstellen
   wie Griff, Visier, Magazin-Schnittstelle). Docstring mit Formsprache-Checkliste (Stilhandbuch §3: Leitmerkmal, Schichten, Negativraum,
   Blickfang, Zweiton 70:30, Grafik, Front, Übergänge, Ergonomie). Jede Zahl mit Herkunft (Vorgabe/gemessen/Annahme).
2. Lader `formgen/extended.py` (Snapshot auf Pfad, Datensatz tief kopiert, Quellhash = eigene Datei + BALLON-Closure).
3. Renderwerkzeug `tools/extended_render.py` (Wrapper wie oben; Hero, hero_p, links, rechts, oben, vorn, hinten + Kontaktbogen,
   Vergleich neben BA01).
4. Tests `tests/test_extended.py`: lädt, IDs eindeutig, Baugruppen deklariert, Anker/Punkte auf vorhandenen Teilen, Hand = graphite/rubber,
   ≤ 3 Akzent-Bedienfunktionen, Visierlinie 60–80 mm über der Laufachse, Seitensilhouette gegen BA01 deutlich anders (IoU < 0,85 wie BALLON A1,
   Masken mit `formgen.variety`), Gegenprobe (BA01 gegen sich selbst ≥ 0,99).
5. Doku `docs/extended.md`, Versionsbericht `docs/versions/0.15.md`, CHANGELOG, README-Zeile; `./check`; Richter `./ce judge`
   (`~/.claude/templates/pruefung.md`), dann PR.

**Entscheidung nötig (nicht eigenmächtig):** Blatt-ID/Website-Eintrag. IDs sind ewig; `B<Buchstabe><NN>` ist für Linien reserviert.
Vorschlag: META `id = 'EXTENDED-01'`, keine Blatt-ID in 0.15; Aufnahme in Pipeline/Website als Folgeschritt nach Nutzer-Ja.

## Formideen (Rohliste aus der Sichtung – in der neuen Sitzung prüfen, skizzieren, eine wählen)

| Idee | Architektur | v1-Erbe | Risiko |
|---|---|---|---|
| A „Kielbogen“ | Ein durchgehender Creme-Rücken als flacher Bogen vom Schaft bis über den Lauf; Gehäuse hängt darunter; Schaft mit Daumenloch als Teil des Rückens | Keilschaft g02, Black Ice | kann wie BASIC-Haube wirken, wenn der Bogen zu flach ist |
| B „Brücke“ | Gehäuse niedrig, darüber ein offener Tragebügel auf zwei Stützen, Visier auf der Brücke, Kern im Bogenfenster | f02 Tragebügel | Visierlinie 60–80 mm einhalten |
| C „Bullpup-Monocoque“ | Magazin hinter dem Griff, kurzes Gesamtmaß, langer Laufmantel | f02 Bullpup | Griff-/Magazin-Schnittstellen anders als BASIC-01 |
| D „Zange“ | Zwei seitliche Creme-Schalen umgreifen einen dunklen Kernkörper, oben ein offener Längsspalt (Lauf/Kern sichtbar), vorn laufen die Schalen zu zwei Zinken um den Mündungsbereich | eigene, Negativraum als Leitmerkmal | Übergänge und Halt der Schalen glaubwürdig machen |
| E „Stufenkeil“ | Facettierter Keilkörper in drei Stufen, nach vorn spitz zulaufend | KJ02 Facetten | nahe an Serie `facet` (J) – Eigenständigkeit prüfen |

Danach: Seitensilhouetten der Ideen als schnelle Skizze (Rastermaske oder Blender-Kurzrender), Auswahl begründen, bauen, AAA-Renders
aus ≥ 5 Perspektiven sichten, nachbessern (mindestens zwei Runden), Belege und Bericht.
