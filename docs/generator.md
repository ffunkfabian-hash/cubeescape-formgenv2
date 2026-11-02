# Waffen-Generator und Pipeline (0.2 „Anvil“, Baukasten seit 0.4 „Mosaic“)

Formgen v2 übernimmt das **Prinzip** von Formgen v1 (Varianten aus Parametern, Variantenregister mit englischem Namen,
Konzeptblatt je Blatt-ID, Vorschauen, Viewer, Inhalts-Cache, Golden auf eigene Ergebnisse, Release-Assets statt Commit
der Blätter), nicht dessen Inhalt: keine v1-Waffentypen, -Varianten oder -Blätter, kein Vergleich gegen v1.
Inhalt sind ausschließlich die 17 BASIC-Typen aus BALLON.

```sh
python -m formgen.pipeline                    # alle Blätter: Varianten × 17 Typen
python -m formgen.pipeline BA01 BB01          # einzelne Blätter
python -m formgen.pipeline --variants C --types 01,02 --stages geometry,specs
python -m formgen.variants list
python -m formgen.variants new J "Glass Fang" "Idee in einem Satz" --skin kobalt --param front=[1.0,1.1] --param 'sight=["zinken"]'
python -m formgen.variety                     # Vielfalt: Silhouetten-IoU jeder Linie gegen die Baseline
```

Bilder nur auf dem Mac unter Sperre: `~/Claude/cubeescape-nexogen/ce lock blender -- .venv/bin/python -m formgen.pipeline …`
(der Rasterizer ist reines Python; die Sperre koordiniert die CPU-Last mit anderen Bildsitzungen).

## Quelle BALLON

`config.toml › [ballon]` pinnt Repo und vollen Commit. `formgen/ballon.py` entpackt per `git archive` nur
`basic/__init__.py`, `basic/common.py`, `basic/reticles.py`, `basic/weapons/`, `basic/pilot/`, `data/specs/` nach
`~/Library/Caches/CubeEscapeFormgen2/ballon/<commit>-<Pfadhash>/` (atomar, nur gelesen, über Worktrees geteilt; der Pfadhash
sorgt dafür, dass eine erweiterte Pfadliste neu entpackt statt einen älteren Auszug weiterzunutzen).
Der **BALLON-Quellhash** eines Typs ist SHA256 über die Inhalts-Hashes seiner Import-Closure
(`wNN_*.py` bzw. `pilot/wNN_*_v21.py`, `basic/common.py`, `basic/reticles.py` (lazy Import der Visierbausteine v3),
Paket-`__init__`) – Pfade, Zeiten und die Commit-ID gehen nicht ein. Zusätzlich zählt der
Hash von BALLONs exportiertem Spec (`data/specs/BASIC-NN.spec.json` bzw. `BASIC-NN-v2.1.spec.json`). Ein neuer Pin, der einen
Typ nicht berührt, ändert für ihn nichts; der Commit steht nur im Blatt-Spec (eigener, billiger Cacheeintrag).
Bausteine (`holo_kasten`, `stock_s2`, `grip_v21`, `glow` …) ruft `ballon.call(snapshot, name, …)` aus derselben Closure auf;
v2 kopiert keinen BALLON-Code.

**Grundform.** `base = "standard"` (Vorgabe) nimmt `basic/weapons/wNN_*.py`, `base = "v21"` den v2.1-Piloten
`basic/pilot/wNN_*_v21.py` (15 Typen; 16 Schwert und 17 Gleve haben keinen und fallen mit Anpassungsnotiz auf das
Standardmodul zurück). Die Piloten brauchen die Form `xprof` ([modellsprache.md](modellsprache.md)); Abgleich gegen BALLONs
GLB mit `python tools/ballon_compare.py --base v21 --allow-stale`: Silhouetten-IoU Seite/oben ≥ 0,99 bei allen Typen mit
unverändertem BALLON-Spec (07, 13, 14, 15) und 9 der 11 übrigen; 03 (Seite 0,964) und 06 (oben 0,989, Front 0,938) weichen ab, weil BALLONs
GLB dort neuer als der Pin ist (Maße und Baugruppen geändert), Beleg `~/Library/Caches/CubeEscapeFormgen2/0.4/belege/ballon_compare_v21.*`.

## Variantenregister

`data/variants.toml` (Schema 2) ist die einzige Eintragsstelle (Regel aus v1): Kennbuchstabe A–Z ohne I/O, englischer Name aus
1–3 großgeschriebenen Wörtern (≤ 16 Zeichen), Name und Buchstabe nie doppelt, `idea`, `since`, `skin` aus `skins.toml`,
optional `base` (standard/v21), `params`, `types`. **Blatt-ID = `B` + Buchstabe + BASIC-Nummer** (BA01 … BH17). Vergebene IDs sind ewig.

| Linie | Name | Skin | Grundform | Formsprache (Parameter) |
|---|---|---|---|---|
| A | Baseline | standard | Standard | BALLON-Grundform unverändert |
| B | Long Reach | polar | Standard | front 1,15 · rear 1,06 · limbs 1,12 (seit 0.4) |
| C | Close Quarters | nacht | Standard | front 0,86 · rear 0,90 · drop `vent_*` · limbs 0,88 (seit 0.4) |
| D | Refit | eloxal | v2.1 | Pilot-Formsprache (Fasen, Softgrip, Visier v3); front 1,04–1,10 · glow 1 |
| E | Lantern | kobalt | Standard | runde/offene Visiere (`holo_pille`, `boegen`, `zinken`; Präzision `scope_tropfen`, `gabel`) · Griff v2.1 · glow 1–2 · front 0,86–0,94 · limbs 1,12–1,22 |
| F | Heavy Frame | wueste | Standard | Werferoptik (`achteck`, `entfernung`, `d_linse`; Präzision `lang`) · Schaft S2 × 1,05–1,20 · mag 1,2–1,4 · muzzle 1,5–1,9 / r 1,10–1,25 · front 1,06–1,12 · limbs 0,84–0,90 |
| G | Skeleton | tarnung | Standard | `reflex_sight_v21`, `holo_kasten`, `zinken` (Präzision `scope_tropfen`) · Schaft S1 × 0,8–0,9 · mag 0,72–0,82 · muzzle 0,60–0,75 · front 0,82–0,90 · drop `vent_*`, `cheek_rest` · limbs 1,22–1,30 |
| H | Long Watch | gebraucht | v2.1 | `holo_kasten`, `achteck`, `entfernung` (Präzision `lang`, `scope_tropfen`) · front 1,15–1,30 · rear 1,04–1,12 · muzzle 1,2–1,5 · mag 1,05–1,20 · limbs 1,14–1,24 |

B und C bekamen in 0.4 nur `limbs`: ihre Bögen (BB07, BC07) waren bis 0.2 formgleich mit BA07 (nur Farbe); alle übrigen
B/C-Blätter behalten ihre Parameter. Jede der acht BALLON-Skins ist einer Linie zugeordnet.

### Gesteuerter Zufall

Ein Parameter ist fest oder ein Bereich: Zahl als `[von, bis]`, Baustein als Liste. **Seed** je Blatt =
SHA256(`formgenv2-variant|<Blatt-ID>|<Linie>`)[:16]; gezogen wird je Parameter getrennt mit
SHA256(`<Seed>|<Parameter>`) → [0, 1) – ohne `random`, ohne `hash()`, daher unabhängig von PYTHONHASHSEED und vom Python-Release;
ein neuer Parameter verschiebt keine andere Ziehung. Zahlen werden auf 0,001 gerundet, ganze Zahlen (glow) gleichverteilt.
Bausteinlisten filtert zuerst die **Präzisionsregel** (Zielfernrohre `scope_tropfen`, `gabel`, `lang` nur an 03/09/11, dort
nur Zielfernrohre); bleibt nichts übrig, entfällt der Schritt. Seed, Ziehungen und wirksame Werte stehen im Spec unter
`variation`. Test: alle Linien × Typen bitgleich mit PYTHONHASHSEED 1 und 42 (`tests/test_variety.py`).

## Generator (`formgen/generator.py`)

Grundform ist immer ein BALLON-Modell des Typs (Datensätze META/PARTS/ASSEMBLIES/ANCHORS). Der Generator erzeugt
**keine eigene Grundgeometrie**; er tauscht Teile gegen BALLON-Bausteine (Baukasten) und verändert über Parameter, in
dieser festen Reihenfolge:

| Schritt | Parameter | Wirkung | Herkunft der Zahlen |
|---|---|---|---|
| Visier | `sight` | ersetzt Baugruppe `sight` durch einen Baustein aus BALLONs Visier-Baukasten v3 (`reflex_sight_v21`, `holo_kasten`, `holo_pille`, `zinken`, `boegen`, `achteck`, `d_linse`, `entfernung`; Zielfernrohre `scope_tropfen`, `gabel`, `lang`), Größe M. Holo: Klemmfuß (46 mm) mittig auf dem alten Fuß, auf der Schiene BRI-22 (Schienenoberkante). Zielfernrohr: Visierlinie Laufachse + 66 mm, Sattel und Fuß auf der Schiene (v2.1 mit zwei Schienen: Sattel hinten, Fuß vorn). Anker Socket_Sight/Eye/Reticle(/Objective) kommen aus dem Baustein. Übersprungen ohne Schiene, am Bogen (Pinvisier), bei zu kurzer Schiene oder wenn die Visierlinie 60–80 mm verletzt würde | BALLON `common.py`, `reticles.SIGHT` (Vorgabe) |
| Schaft | `stock`, `stock_scale` | S1 ↔ S2 (`stock_s1`/`stock_s2`) am Gehäuseende f0 und der Laufachse ua, beide aus dem vorhandenen Schaft zurückgerechnet (S1: Verbindung f0−11…f0+1, ua−22; S2: erster Punkt f0+2, ua−40); `stock_scale` = Längenfaktor s (ohne Angabe der gemessene); nur bei Schaft S1/S2 ohne Anker | BALLON `stock_s1`/`stock_s2` (Vorgabe); Länge bei s = 1: 179/170 mm (gemessen) |
| Griff | `grip = "v21"` | `grip_rifle(top)` → `grip_v21(top)` (Fingerauflagen, Gummi, Griffboden); nur wenn die Griffgruppe genau `grip_rifle(top)` ist (nicht 06 mit Neigung, 17 ohne Bügel) | BALLON `grip_v21` |
| Magazin | `mag` 0,7–1,4 | Stangenmagazin (BMW-R oder Magazin im Griff, Entnahme per translate) entlang der Entnahmerichtung: Punkte jenseits der halben Länge wandern um (Faktor − 1) · Länge | Richtung aus BALLON `move.vector_mm`; Schnitt `MAG_CUT` 0,5 (Annahme) |
| Mündung | `muzzle` 0,6–2,0, `muzzle_r` 0,8–1,3 | Teil `muzzle` (BMZ-15) länger/kürzer, Teile davor und Socket_Muzzle verschoben; Radius × `muzzle_r` | Vorgabe Register |
| Leuchten | `glow` 0–2 | 1–2 Leuchtstreifen (`glow`, Rolle energy, 3 mm hoch, 3 mm Abstand) auf der längsten freien Creme-Gehäuseseite, mittlere 40 %, links zuerst; übersprungen, wenn Seitenteile im Weg sind | Annahme `GLOW_*` |
| Weglassen | `drop` | entfernt Teile per `fnmatch`; Teile mit Anker oder Kindteilen bleiben (Bericht `protected`) | Vorgabe Register |
| Länge vorn | `front` 0,7–1,4 | Vorderlänge Socket_Hand → Socket_Muzzle × Faktor; Schnitt in der mittleren Hälfte zwischen Socket_SupportHand (sonst Socket_Hand) und Socket_Muzzle an der Stelle, die die wenigsten kurzen Teile kreuzt | Anker gemessen aus BALLON; Faktor Vorgabe Register |
| Länge hinten | `rear` 0,7–1,4 | Hinterlänge (hinterstes Teil → Socket_Hand) × Faktor; Schnitt im Schaft; ohne Baugruppe `stock` übersprungen | wie oben |
| Wurfarme | `limbs` 0,8–1,3 | Bogen: oberer und unterer Wurfarm in u × Faktor (Schnitt in der mittleren Hälfte des Arms, gespiegelt für unten); Rollen, Sehnenenden und Bewegungspunkte folgen, Nockpunkt bleibt | `LIMB_WINDOW` (Annahme) |
| Skin | `skins.toml` | nur Farben/Oberflächen; Form unverändert | Spiegel von BALLON `kit.SKINS` |

Teile ganz jenseits eines Schnitts werden verschoben, Teile über dem Schnitt mit mindestens 60 mm Länge (Annahme
`SHORT_MM`; Schnittfenster `FRONT_WINDOW` 25–75 %, Schaftrand `STOCK_MARGIN` 20 %, beide Annahmen) gedehnt oder gestaucht, kürzere nie verzerrt. Stauchen ist auf die freie Zone hinter dem Schnitt begrenzt
(1 mm Fuge wie BALLON `SEAM`); `limited: true` im Bericht. Die Dehnung arbeitet in f (Länge) und u (Wurfarme) auf allen
Formen der Piloten (`prof`, `box`, `cyl`, `plan`, `frame`, `xbox`, `xprof`, `multi`, `tube`, `text`, samt `cuts`); Anker und
Bewegungspunkte (`pivot`, `tip`, `nock`, `expect`) folgen ihrem Teil. Ein übersprungener Schritt steht mit Grund im Bericht.

**Anpassungen an BALLON-Daten** (im Spec unter `generator.adaptations`, alle als *Annahme*):
- Hohlkegel mit `r_in ≥ r` (Objektive der Zielfernrohre BASIC-03/09/11): BALLON skaliert `r_in` mit `r1/r`, die Wand stülpt
  sich um und BALLONs gemessene Höhe/Breite enthält den umgestülpten Innenmantel (2,3/9,4/9,1 mm). v2 bezieht `r_in` auf
  das große Ende. Meldung an Sightline (Liste unten).
- Deklarierte, aber leere Baugruppen (`support` in BASIC-08/10) entfallen.
- Akzent-Grenze: bringt ein Baustein (Klemmhebel, Höhenturm) mehr als max(3, Grundform) Akzent-Bedienfunktionen, wird er
  in `sight_anod` (Visier) bzw. `graphite` entfärbt.
- Grundform `v21` ohne Pilot (16, 17): Standardmodul.

### Designvertrag

Gemessen am Autorenmodell vor und nach den Schritten, im Spec unter `contract` (BALLON `docs/designvertrag.md`):
- **Hand = Graphit:** Teile an Socket_Hand/Socket_SupportHand haben die Rolle `graphite` oder `rubber` (BALLON 0.32 Softgrip:
  Griff der Haupthand Gummi) oder die der Grundform (Bogensehne).
- **Höchstens drei Akzent-Bedienfunktionen:** verschiedene `func` der `accent`-Teile; Munitionskennung und das lackierte Band
  der Piloten zählen nicht (Vertrag: „nur Bedienelemente … und Munitionskennung“). Grenze max(3, Grundform), weil die
  v2.1-Piloten nach dieser Zählung selbst 3–5 haben (Meldung an Sightline).
- **Visierlinie 60–80 mm** über der Laufachse (Socket_Eye − Socket_Muzzle in u): hält die Grundform sie ein, muss die Variante
  sie einhalten; sonst darf sie sich nicht verschlechtern (11/14/15 liegen in BALLON bei 88/98/95 mm, Pistolen/Bogen darunter).

### Vielfalt

`formgen/variety.py` misst wie `tools/ballon_compare.py` gefüllte Dreiecksmasken (0,5 mm/px, Ursprung Socket_Hand, kein Fit)
in Seite, Draufsicht und Front gegen BAnn; Geometrie ohne Booleans/Fasen (Außenkontur gleich, schnell).
**Schwelle: min(IoU Seite, IoU oben) ≤ 0,98** je Nicht-Baseline-Blatt (`tests/test_variety.py`). Begründung (Annahme): Das
Blatt zeigt eine Waffe von ~1 m auf ~900 px, also rund 1 px/mm; die gefüllte Seitenfläche liegt bei 30 000–100 000 mm².
2 % davon sind 600–2000 px² – mindestens ein Block von etwa 25 × 25 px, im Blatt klar sichtbar. Front allein zählt nicht (die
Stirnansicht der Langwaffen ist bei allen Linien fast gleich). Stand 0.4: alle 119 Blätter B–H ≤ 0,973 (Median 0,872, kleinster Wert 0,421 BD07).

**Grenze (ehrlich):** Die Vielfalt bleibt im BALLON-Vokabular – Längen, Tausch genormter Bausteine, Leuchtlinien, Skins.
Die v1-Linien waren je Linie von Hand modelliert (eigene Gehäusekonturen); radikal neue Silhouetten brauchen neue Bausteine
in BALLON (Gehäuse- und Handschutzvarianten je Familie). Vorschlag an Sightline: [vorschlag-ballon-varianten.md](vorschlag-ballon-varianten.md).

## Stufen und Cache

| Stufe | Ausgabe | Schlüssel (außer Cacheformat, Blatt-ID, Art) |
|---|---|---|
| geometry | `out/geometry/<ID>.json` | BALLON-Quellhash und Spec-Hash der tatsächlichen Grundform, Registereintrag (mit `base`), Typnummer; Closure `generator.py` (inkl. geom/model/ballon/variants); MODEL, GEOM |
| specs | `out/specs/<ID>.spec.json` (im Repo) | Geometrie-Hash; Closure `wspec.py`; BALLON-Commit; WSPEC |
| prompts | `out/prompts/<ID>.prompts.json` (im Repo) | Geometrie-Hash; Closure `prompts.py`; PROMPTS, SPEC |
| views | `out/views/<ID>/*.png` | Geometrie-Hash; Kamera, Größe, Skin + `skins.toml`-Hash, Hintergrund; Closure `raster.py`; Umgebung; RASTER |
| sheets | `out/sheets/<ID>.dc.html` | Geometrie-Hash; Bildpfade + Bildmetadaten; Closure `sheet.py`; SHEET |
| previews | `out/previews/<ID>.webp` | wie views (Held 720×480, Variantenskin) |
| viewer | `out/index.html` | Liste aller Blätter mit Spec-Daten; Hash von `viewer.py`; VIEWER |

Closure = SHA256 über die statisch importierten lokalen Module des Stufencodes (`build.source_hashes`) plus die Dateien
mit den Buildern selbst (`pipeline.py`, `build.py`; Richterbefund 0.2), daher keine
handgepflegten Funktionslisten wie in v1. Umgebung = Python-Minor, numpy, Pillow. Ein geänderter Rasterizer baut nur
Ansichten/Vorschauen; eine Geometrie, die bytegleich bleibt, behält alle nachfolgenden Treffer. Cache:
`~/Library/Caches/CubeEscapeFormgen/artifacts` (geteilt über Worktrees, atomar, Payload-SHA geprüft, siehe
[cache.md](cache.md)). `out/timing.json` hält Zeiten, Neubauten und Treffer je Stufe.

## Spec-Format (`formgenv2/weapon-sheet-spec`, Version 2)

Schema [weapon-sheet-spec-2.schema.json](schemas/weapon-sheet-spec-2.schema.json), Code `formgen/wspec.py`.
Inhalt: ID, Namen, Variante (Registereintrag mit `base` und Bereichen), Typ (BALLON-META), BALLON-Herkunft (Commit, Quellhash,
Spec-Hash, Datei-Hashes), tatsächliche Grundform `base`, `variation` (Seed, Ziehungen, wirksame Werte), Generatorschritte mit
Schnitt/Delta/verschobenen, gedehnten, ersetzten und hinzugefügten Teilen, Anpassungen, `contract` (Designvertrag Grundform
und Variante), Maße (eigene und BALLONs), Zähler, Baugruppen, Teile mit Ausdehnung in mm (f/u/x), Anker, Herkunft, Warnungen.
**Migration Pflicht:** `MIGRATIONS[1]` hebt 0.2-Specs auf 2 (`base` standard, Seed aus der Blatt-ID, keine Ziehungen,
`contract` null); Test mit einem echten 0.2-Spec (`tests/fixtures/BA04.spec-v1.json`).
Abnehmer: `formgen.viewer` und `formgen.release_assets` (prüfen über `wspec.migrate`); Toolgen liest das Blatt-Spec nicht.

## Für Sightline (BALLON nicht geändert)

1. `common.scope()`: Objektiv `r=r_tube+1`, `r1=r_obj`, `r_in=r_obj−3` – `r_in` > `r` stülpt die Kegelwand um (BASIC-03/09/11);
   BALLONs Spec-Maße Höhe/Breite enthalten dadurch 2–9 mm Innenmantel.
2. BASIC-08 und BASIC-10 deklarieren die Baugruppe `support` ohne Teile.
3. Visierlinie über der Laufachse außerhalb 60–80 mm in den Standardmodulen 11 (88), 14 (98), 15 (95); die Piloten halten 66 ein.
4. v2.1-Piloten: nach Designvertrag-Zählung 3–5 Akzent-Bedienfunktionen (Klemmhebel des Visiers, Höhenturm, Ladehebel,
   Feuerwahl, Magazinhalter …); entweder die Regel nennt Visier-Bedienelemente als Ausnahme oder die Piloten entfärben.

## Golden

`FORMGEN_GOLDEN_IMAGES=1 python -m unittest tests.test_golden` ist die **Gesamtabnahme** (voller Vergleich aller Golden-Dateien,
`FORMGEN_GOLDEN_MODELS` nicht setzen). `FORMGEN_GOLDEN_MODELS=BA01,…` ist eine ausdrücklich benannte Teilabnahme; im Bericht nennen.
