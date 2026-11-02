# Formgen v2 · Anvil

0.2.0 – **Waffen-Pipeline nach v1-Prinzip auf den 17 BALLON-Grundformen.** Drei Variantenlinien × 17 Typen = 51 Konzeptblätter
mit Spec, Prompts, Ansichten, Vorschau und Viewer; jede Stufe inhaltsadressiert gecacht. Formgen v1 bleibt eingefrorenes Archiv.

Einstieg: [Regeln](AGENTS.md), [Generator und Pipeline](docs/generator.md), [Cache](docs/cache.md),
[Modellsprache](docs/modellsprache.md), [Versionsbericht 0.2](docs/versions/0.2.md).

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
./check
.venv/bin/python -m formgen.variants list
.venv/bin/python -m formgen.pipeline --stages geometry,specs,prompts      # Daten ohne Bilder
~/Claude/cubeescape-nexogen/ce lock blender -- sh -c "cd $PWD && .venv/bin/python -m formgen.pipeline"   # alles (Mac)
.venv/bin/python -m formgen.release_assets $(ls out/specs | grep '^B' | sed 's/.spec.json//')            # lokaler Release-Probelauf
```

Grundlage: BALLON-Commit aus `config.toml › [ballon]` (nur gelesen, `git archive`). Neue Variante:
`python -m formgen.variants new <Buchstabe> "<English Name>" "<Idee>" --skin … --front … --rear … --drop …`.
Viewer `out/index.html`, Blätter `out/sheets/`, im Repo nur `out/specs/` und `out/prompts/` (Golden in `tests/golden.json`).
Zeiten je Stufe: `out/timing.json`. Messwerkzeuge: `tools/measure_v1.py`, `tools/measure_v2.py`, `tools/ballon_compare.py`.

## Contour-Bestand (0.1)

Roboter R01 und die Contour-Piloten (W01, KG02/VS02 als v1-Geo-Prüfeingänge) bauen weiter über `formgen.build`;
sie sind nicht Teil der Waffen-Pipeline. R01 gilt mit Entscheid 234 A als abgenommen
([Ausnahmen je Referenz](docs/acceptance-exceptions.json)); Roboterarbeit ruht auf Nutzerwunsch.

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
Referenzkonflikten der Originale; mit Entscheid 234 A (02.11.2026) gelten begründete Ausnahmen nur für diese
R01-Referenzmasken, allgemeine Grenzen unverändert ([Bericht 0.1](docs/versions/0.1.md), [0.2](docs/versions/0.2.md)).
