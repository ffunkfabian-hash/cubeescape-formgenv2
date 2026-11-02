# Waffen-Generator und Pipeline (0.2 „Anvil“)

Formgen v2 übernimmt das **Prinzip** von Formgen v1 (Varianten aus Parametern, Variantenregister mit englischem Namen,
Konzeptblatt je Blatt-ID, Vorschauen, Viewer, Inhalts-Cache, Golden auf eigene Ergebnisse, Release-Assets statt Commit
der Blätter), nicht dessen Inhalt: keine v1-Waffentypen, -Varianten oder -Blätter, kein Vergleich gegen v1.
Inhalt sind ausschließlich die 17 BASIC-Typen aus BALLON.

```sh
python -m formgen.pipeline                    # alle Blätter: Varianten × 17 Typen
python -m formgen.pipeline BA01 BB01          # einzelne Blätter
python -m formgen.pipeline --variants C --types 01,02 --stages geometry,specs
python -m formgen.variants list
python -m formgen.variants new D "Glass Fang" "Idee in einem Satz" --skin kobalt --front 1.1
```

Bilder nur auf dem Mac unter Sperre: `~/Claude/cubeescape-nexogen/ce lock blender -- .venv/bin/python -m formgen.pipeline …`
(der Rasterizer ist reines Python; die Sperre koordiniert die CPU-Last mit anderen Bildsitzungen).

## Quelle BALLON

`config.toml › [ballon]` pinnt Repo und vollen Commit. `formgen/ballon.py` entpackt per `git archive` nur
`basic/__init__.py`, `basic/common.py`, `basic/weapons/`, `data/specs/` nach
`~/Library/Caches/CubeEscapeFormgen2/ballon/<commit>/` (atomar, nur gelesen, über Worktrees geteilt).
Der **BALLON-Quellhash** eines Typs ist SHA256 über die Inhalts-Hashes seiner Import-Closure
(`wNN_*.py`, `basic/common.py`, Paket-`__init__`) – Pfade, Zeiten und die Commit-ID gehen nicht ein. Zusätzlich zählt der
Hash von BALLONs exportiertem Spec (`data/specs/BASIC-NN.spec.json`, basic-spec 1). Ein neuer Pin, der einen Typ nicht
berührt, ändert für ihn nichts; der Commit steht nur im Blatt-Spec (eigener, billiger Cacheeintrag).

## Variantenregister

`data/variants.toml` ist die einzige Eintragsstelle (Regel aus v1): Kennbuchstabe A–Z ohne I/O, englischer Name aus
1–3 großgeschriebenen Wörtern (≤ 16 Zeichen), Name und Buchstabe nie doppelt, `idea`, `since`, `skin` aus `skins.toml`,
`params`, optional `types`. **Blatt-ID = `B` + Buchstabe + BASIC-Nummer** (BA01 … BC17). Vergebene IDs sind ewig.

| Linie | Name | Skin | Parameter |
|---|---|---|---|
| A | Baseline | standard | keine – BALLON-Grundform unverändert |
| B | Long Reach | polar | front 1,15 · rear 1,06 |
| C | Close Quarters | nacht | front 0,86 · rear 0,90 · drop `vent_*` |

## Generator (`formgen/generator.py`)

Grundform ist immer das BALLON-Modell des Typs (Datensätze META/PARTS/ASSEMBLIES/ANCHORS). Der Generator erzeugt
**keine eigene Grundgeometrie**, sondern verändert nur über Parameter:

| Parameter | Bereich | Wirkung | Herkunft der Zahlen |
|---|---|---|---|
| `front` | 0,7–1,4 | Vorderlänge Socket_Hand → Socket_Muzzle × Faktor; Schnitt in der mittleren Hälfte zwischen Socket_SupportHand (sonst Socket_Hand) und Socket_Muzzle an der Stelle, die die wenigsten kurzen Teile kreuzt | Anker gemessen aus BALLON; Faktor Vorgabe Register |
| `rear` | 0,7–1,4 | Hinterlänge (hinterstes Teil → Socket_Hand) × Faktor; Schnitt im Schaft; ohne Baugruppe `stock` übersprungen | wie oben |
| `drop` | Muster | entfernt Teile per `fnmatch`; Teile mit Anker oder Kindteilen bleiben (Bericht `protected`) | Vorgabe Register |
| Skin | `skins.toml` | nur Farben/Oberflächen; Form unverändert | Spiegel von BALLON `kit.SKINS` |

Teile ganz jenseits des Schnitts werden verschoben, Teile über dem Schnitt mit mindestens 60 mm Länge (Annahme
`SHORT_MM`) gedehnt oder gestaucht, kürzere nie verzerrt. Stauchen ist auf die freie Zone hinter dem Schnitt begrenzt
(1 mm Fuge wie BALLON `SEAM`); `limited: true` im Bericht. Anker und Bewegungspunkte (`pivot`, `tip`, `nock`,
`expect`) folgen ihrem Teil. Bögen ohne Längsachse (Socket_Muzzle < 100 mm vor Socket_Hand) überspringen `front`.

**Anpassungen an BALLON-Daten** (im Spec unter `generator.adaptations`, alle als *Annahme*):
- Hohlkegel mit `r_in ≥ r` (Objektive der Zielfernrohre BASIC-03/09/11): BALLON skaliert `r_in` mit `r1/r`, die Wand stülpt
  sich um und BALLONs gemessene Höhe/Breite enthält den umgestülpten Innenmantel (2,3/9,4/9,1 mm). v2 bezieht `r_in` auf
  das große Ende. Meldung an Sightline (Liste unten).
- Deklarierte, aber leere Baugruppen (`support` in BASIC-08/10) entfallen.

## Stufen und Cache

| Stufe | Ausgabe | Schlüssel (außer Cacheformat, Blatt-ID, Art) |
|---|---|---|
| geometry | `out/geometry/<ID>.json` | BALLON-Quellhash, BALLON-Spec-Hash, Registereintrag, Typnummer; Closure `generator.py` (inkl. geom/model/ballon); MODEL, GEOM |
| specs | `out/specs/<ID>.spec.json` (im Repo) | Geometrie-Hash; Closure `wspec.py`; BALLON-Commit; WSPEC |
| prompts | `out/prompts/<ID>.prompts.json` (im Repo) | Geometrie-Hash; Closure `prompts.py`; PROMPTS, SPEC |
| views | `out/views/<ID>/*.png` | Geometrie-Hash; Kamera, Größe, Skin + `skins.toml`-Hash, Hintergrund; Closure `raster.py`; Umgebung; RASTER |
| sheets | `out/sheets/<ID>.dc.html` | Geometrie-Hash; Bildpfade + Bildmetadaten; Closure `sheet.py`; SHEET |
| previews | `out/previews/<ID>.webp` | wie views (Held 720×480, Variantenskin) |
| viewer | `out/index.html` | Liste aller Blätter mit Spec-Daten; Hash von `viewer.py`; VIEWER |

Closure = SHA256 über die statisch importierten lokalen Module des Stufencodes (`build.source_hashes`), daher keine
handgepflegten Funktionslisten wie in v1. Umgebung = Python-Minor, numpy, Pillow. Ein geänderter Rasterizer baut nur
Ansichten/Vorschauen; eine Geometrie, die bytegleich bleibt, behält alle nachfolgenden Treffer. Cache:
`~/Library/Caches/CubeEscapeFormgen/artifacts` (geteilt über Worktrees, atomar, Payload-SHA geprüft, siehe
[cache.md](cache.md)). `out/timing.json` hält Zeiten, Neubauten und Treffer je Stufe.

## Spec-Format (`formgenv2/weapon-sheet-spec`, Version 1)

Schema [weapon-sheet-spec-1.schema.json](schemas/weapon-sheet-spec-1.schema.json), Code `formgen/wspec.py`.
Inhalt: ID, Namen, Variante (Registereintrag), Typ (BALLON-META), BALLON-Herkunft (Commit, Quellhash, Spec-Hash, Datei-Hashes),
Generatorschritte mit Schnitt/Delta/verschobenen und gedehnten Teilen, Anpassungen, Maße (eigene und BALLONs),
Zähler, Baugruppen, Teile mit Ausdehnung in mm (f/u/x), Anker, Herkunft, Warnungen. **Ab Version 1 Migration Pflicht:**
neue Version → `FORMAT_VERSION` erhöhen, `MIGRATIONS[alt]` ergänzen, Test.

## Für Sightline (BALLON nicht geändert)

1. `common.scope()`: Objektiv `r=r_tube+1`, `r1=r_obj`, `r_in=r_obj−3` – `r_in` > `r` stülpt die Kegelwand um (BASIC-03/09/11);
   BALLONs Spec-Maße Höhe/Breite enthalten dadurch 2–9 mm Innenmantel.
2. BASIC-08 und BASIC-10 deklarieren die Baugruppe `support` ohne Teile.
