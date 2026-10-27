# Formgen v2 · Contour

0.1.0 – **technischer Zwischenstand, Roboter noch nicht abgenommen**.
Eigene Pythonmodelle in ballons kit-Sprache, unabhängiger Rasterizer und v1-Geo-Import.

Einstieg: [Regeln](AGENTS.md), [Auftrag](docs/auftrag-codex-formgen-v2.md),
[Modellsprache](docs/modellsprache.md), [Versionsbericht](docs/versions/0.1.md).

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
./check
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

Lokale Fußabnahme vom 27.10.2026: Fußkorrektur, Bild-, Golden- und Paketprüfung
abgeschlossen; Rücken-IoU (0,8859) und Fußband 0 in Rücken/Seiten scheitern an
Referenzkonflikten. Keine Gesamtfreigabe, siehe [Bericht](docs/versions/0.1.md).
