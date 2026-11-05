# Formgen v2 · Sentry

0.9 – **Waffen und Roboter auf einer Website mit 3D und Markierung.** Einstieg `out/index.html`, offline per `file://` ([Website](docs/website.md)). Heute ein Basic-Roboter, RoboterBasic-01 (`RA01`), fest in diesem Repo, ohne Verbindung zu Critic ([Roboter](docs/robot.md)).

**Varianten der echten BALLON-Spielwaffen, jetzt mit Design-Serien.** Zwölf Linien × 17 Typen = 204 Konzeptblätter auf dem neuesten
BALLON-Spielpiloten je Typ (BASIC-16/17 ohne Piloten: Formstudie, im Blatt gekennzeichnet): acht Parameterlinien aus BALLON-Bausteinen (Visier v3,
Schaft S1/S2, Griff v2.1, Längen, Leuchtstreifen) und vier Serien mit eigener Formensprache (Stealth-Facetten, Werkstatt-Prototyp, Cube-Farbwelt,
organisch-glatt), mit gesteuertem Zufall (Seed je Blatt), Spec, Prompts, GLB über BALLONs Blender-Kit (Stufe `asset`, AAA-Bake auf Anforderung),
Ansichten, Vorschau und Viewer; jede Stufe inhaltsadressiert gecacht.
Formgen v1 bleibt eingefrorenes Archiv.

Einstieg: [Regeln](AGENTS.md), [Generator und Pipeline](docs/generator.md), [Cache](docs/cache.md),
[Modellsprache](docs/modellsprache.md), [Versionsbericht 0.9](docs/versions/0.9.md).

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
./check
.venv/bin/python -m formgen.variants list
.venv/bin/python -m formgen.pipeline --stages geometry,specs,prompts      # Daten ohne Bilder
~/Claude/cubeescape-nexogen/ce lock blender -- sh -c "cd $PWD && .venv/bin/python -m formgen.pipeline"   # alles (Mac, Blender für asset)
~/Claude/cubeescape-nexogen/ce lock gpu -- sh -c "cd $PWD && .venv/bin/python -m formgen.pipeline BA01 BD01 --bake BA01,BD01"   # AAA-Bake
.venv/bin/python -m formgen.release_assets $(ls out/specs | grep '^B' | sed 's/.spec.json//')            # lokaler Release-Probelauf
```

Grundlage: BALLON-Commit aus `config.toml › [ballon]` (nur gelesen, `git archive`). Neue Variante:
`python -m formgen.variants new <Buchstabe> "<English Name>" "<Idee>" --skin … [--base pilot|standard|v21] --param front=[1.0,1.1] --param 'sight=["zinken"]' …`.
Vielfalt messen: `python -m formgen.variety` (Silhouetten-IoU jeder Linie gegen die Baseline); Serien untereinander mit `--variants J,K,L,M --pairs`.
Design-Serien (0.8): Parameter `series` in `data/variants.toml`, Formensprachen in `formgen/series.py`, Belege mit `tools/series_evidence.py`, Abnahme durch BALLON mit `tools/ballon_accept.py`.
Viewer `out/index.html`, Blätter `out/sheets/`, im Repo nur `out/specs/` und `out/prompts/` (Golden in `tests/golden.json`).
Zeiten je Stufe: `out/timing.json`. Messwerkzeuge: `tools/measure_v1.py`, `tools/measure_v2.py`, `tools/ballon_compare.py`,
`tools/line_a_parity.py` (Linie A gegen BALLONs Neubau), `tools/bake_check.py` (Bake gegen BALLONs Unity-Atlas).

## Contour-Bestand (0.1)

Roboter R01 und die Contour-Piloten (W01, KG02/VS02 als v1-Geo-Prüfeingänge) bauen weiter über `formgen.build`;
sie sind nicht Teil der Waffen-Pipeline. Entscheid 234 A deckt den R01-Rücken ([Ausnahmen je Referenz](docs/acceptance-exceptions.json));
Seiten-Band 0 (1,42) wartet auf eine Nutzerentscheidung. Der aktuelle Roboter ist RoboterBasic-01 ([Roboter](docs/robot.md)); R01/R02 stehen nicht auf der Website.

```sh
.venv/bin/python -m formgen.build --dummy
.venv/bin/python -m formgen.build --dummy  # 0 gebaut
.venv/bin/python -m formgen.build W01 KG02 VS02 R01 --stages specs,prompts,geo
```

Bilder nur auf dem Mac unter der gemeinsamen GPU-Sperre; `ce` aus Nexogen
wechselt sein Arbeitsverzeichnis, daher absolute Pfade bzw. PYTHONPATH:

```sh
~/Claude/cubeescape-nexogen/ce lock status
~/Claude/cubeescape-nexogen/ce lock gpu -- env PYTHONPATH="$PWD" "$PWD/.venv/bin/python" -m formgen.build W01 KG02 VS02 R01 --jobs 2
.venv/bin/python -m formgen.release_assets W01 KG02 VS02 R01
```

Standardbau ist inkrementell. `--force-views`/`--force-sheets` nur gezielt verwenden.
Viewer: `out/index.html`, Blätter: `out/sheets/`, JSON: `out/specs/`, `out/prompts/`,
`out/geo/`. Geo/Blätter/Bilder und Release-ZIPs sind nicht Teil von Git.
Der Releasebefehl erzeugt ausschließlich ein lokales Testarchiv, keine Veröffentlichung.

Ohne ID-Auswahl werden die vier Prüfmodelle gebaut. Die vorbereiteten159
v1-Geos können einzeln über die vorhandene Pipeline gewählt werden:

```sh
.venv/bin/python -m formgen.build KC01 --legacy-dir ~/Library/Caches/CubeEscapeFormgen/imports/v1 --stages specs,prompts,geo
```

Benötigte Visier-Specs werden mitgeliefert; zusätzliche Visierbilder entstehen
dadurch nicht. Ohne ID-Auswahl bleibt auch mit`--legacy-dir` der Vierpilotbau.
Der Datenprobelauf aller159 Modelle lieferte636Artefakte, danach0 gebaut/636 Treffer;
alle159Geo-Exporte wurden wieder geladen. Die Bibliothek wurde nicht vollständig gerendert.
W01 s native Geo-Erweiterung und figure-geo1 sind ausdrücklich keine bestätigten
Toolgen-Abnehmerverträge. Siehe [Geo-Verträge](docs/geo-export.md).

Seit der Nutzerentscheidung vom 27.10.2026 sind die geprüften GEOM8-Fasen
das akzeptierte W01-Ziel. Die native Toolgen-Anpassung ist zurückgestellt;
die lokale Roboterabnahme bleibt davon unabhängig erforderlich.

Lokale Fußabnahme vom 27.10.2026: Rücken-IoU 0,8859 und Fußband 0 in Rücken/Seiten scheiterten an
Referenzkonflikten der Originale; mit Entscheid 234 A (02.11.2026) gilt eine begründete Ausnahme nur für die
R01-Rückenmaske, allgemeine Grenzen unverändert; Seiten-Band 0 offen ([Bericht 0.1](docs/versions/0.1.md), [0.2](docs/versions/0.2.md)).
