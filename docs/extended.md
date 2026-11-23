# EXTENDED-Modelle

Seit 0.15 „Spearhead“. Ein EXTENDED-Modell ist eine eigenständige Waffe der BASIC-Familie: eigene Silhouette, eigene Proportionen
und eigene Formarchitektur, gebaut im Vokabular des BALLON-Kits. Es ist kein Generatorlauf über einer BASIC-Grundform und kein
Umbau eines Piloten. Aus `basic.common` kommen nur die genormten Familienschnittstellen: Griffmodul BGM-1, Holovisier H0 auf der
Schiene BRI-22, Feuerwahlhebel und Ladehebel-Form, Schraubenköpfe sowie die Hilfen `rot`, `cut_box` und `mirror`.

| Kurzname | ID | Blatt-ID | Modul | Typ |
|---|---|---|---|---|
| `e01` | EXTENDED-01 „Spearhead“ | `EA01` | `formgen/models/extended/e01_spearhead.py` | Automatikgewehr |
| `e10` | EXTENDED-10 „Bellmouth“ | `EA10` | `formgen/models/extended/e10_bellmouth.py` | Fusionsgewehr |
| `e11` | EXTENDED-11 „Collimator“ | `EA11` | `formgen/models/extended/e11_collimator.py` | Lineares Fusionsgewehr |

IDs sind ewig. Die Blatt-ID folgt dem Schema `E<Linie><NN>` (Nutzerentscheid vom 23.11.2026), analog zu `BA01` und `RA01`:
Linie A ist die Grundform, NN die EXTENDED-Nummer, spätere Linien folgen als `EB01` usw. Sie steht in `formgen/extended.py` ›
`SHEETS` und in `META.sheet_id`. Vergeben ist bisher nur die ID; ein Blattweg über `formgen.pipeline` und die Aufnahme auf die
Website folgen in einer eigenen Version.

## Werkzeuge

- `formgen/extended.py`: `load(key)` liefert den Datensatz tief kopiert. Der BALLON-Snapshot steht nur während des Imports auf
  `sys.path`. `source(key)` bildet den Quellhash aus der Modelldatei und den importierten `basic`-Modulen. `side_mask` und
  `side_iou` liefern die Seitensilhouette (1 mm je Pixel, Ursprung Socket_Hand, ohne Fit). `bounds` und `components` prüfen über
  Hüllquader, dass kein Teil schwebt.
- `tools/extended_render.py`: AAA-Ansichten mit BALLONs unverändertem `tools/blender_build.main(W=<Datensatz>)`: hero (eigenes
  `HERO`), hero_p (70 mm), side_left, side, top, front und rear, mit `--extra` dazu clay und exploded. Das Werkzeug setzt einen
  Kontaktbogen und den Vergleich mit BA01. Ausgabe nach `~/Library/Caches/CubeEscapeFormgen2/0.15/belege/<tag>/`.

```bash
W=$PWD; ./ce lock gpu -- $W/.venv/bin/python $W/tools/extended_render.py e01 --tag r3 --res 1600 --gpu --extra
```

Die Pfade müssen absolut sein, weil die Sperre das Arbeitsverzeichnis wechselt. Ein Tag rendert nur neu, wenn Bilder fehlen oder
der Stempel `render.json` nicht passt; er enthält den Datensatz- und den Quellhash, den Kit-Snapshot, Samples, Auflösung und
Ansichten. `--force` rendert trotzdem neu.

## EXTENDED-01 „Spearhead“

### Formideen

Vier Ideen wurden als Seitensilhouetten skizziert, mit Griff und Magazin der Familie (`…/0.15/belege/skizzen/skizzen_v1.png`). Die
Spalte IoU ist die Seiten-IoU gegen BA01.

| Idee | Architektur | IoU | Urteil |
|---|---|---|---|
| A Kielbogen | durchgehender Creme-Rücken als Bogen, Daumenlochschaft | 0,79 | wirkt wie die BASIC-Haube mit dunklem Block darunter |
| B Brücke | niedriges Gehäuse, Tragebügel mit Visier | 0,67 | am fremdesten, liest sich aber als konventioneller Tragegriff |
| D Zange | Creme-Schalen umgreifen einen dunklen Kern, zwei Zinken | 0,77 | starker Negativraum, wirkt aber wie eine Energiewaffe |
| **F Speerspitze** | Oberlinie fällt, Unterlinie steigt zur Spitze, Draufsicht verjüngt | 0,75 | **gewählt** |

F hat die stärkste einzelne Geste, ist klar als Automatikgewehr erkennbar und lässt sich mit dem Kit glaubwürdig bauen: Die Klinge
entsteht als Seitenprofil, das mit `plan`-Schneidkörpern in der Draufsicht verjüngt wird. Aus D kommt der Negativraum als
Fuller-Schlitz dazu.

### Formsprache

Die Checkliste folgt Stilhandbuch §3; Einzelheiten und die Herkunft jeder Zahl stehen im Docstring und in den Kommentaren des Moduls.

- **Leitmerkmal Speerspitze:** Die Höhe sinkt von 80 mm an der Fuge zwischen Gehäuse und Klinge auf 27 mm vor der Stirnfase (f 500). In der
  Draufsicht verjüngt sich die Klinge von 44 auf 20 mm, und die eloxierte Mittelrippe läuft von 14 auf 5 mm zu.
- **Negativraum:** Der Fuller-Schlitz in der Creme-Klinge zeigt Lauf und Kühlringe. Dazu kommt der Dreiecksdurchbruch des
  Fachwerkschafts, durch den der Puffer in der Laufachse sichtbar ist.
- **Zweiton:** Creme liegt über Graphit. Die Trennfuge ist eine Gerade, die vom Gehäuseende zur Spitze steigt.
- **Blickfang:** Einziger Blickfang ist der Energiekern links, ein langgezogenes Sechseck mit Spitze nach vorn, gefasst von Glas und
  blankem Rahmen.
- **Schichten:** Die Mittelrippe steht 2,5 mm über der Klinge, die Deckplatte mit der Munitionsanzeige 3 mm über dem Gehäuse. Die
  Seitenpaneele liegen in Mulden, und das Unterteil ist je Seite 1 mm schmaler als das Oberteil.
- **Grafik:** Ein Chevronpaar an der Klingenwurzel ist das einzige Grafikelement; dazu kommt eine Schrift rechts.
- **Mehrstufige Front:** Die Spitze hat Fasen, dahinter folgen die blanke Laufbuchse, ein kurzer freier Lauf und der
  Sechskant-Kompensator mit blanker Krone.
- **Ergonomie:** Griff BGM-1 an derselben Stelle wie in der Familie, ein Handstopp-Sporn vor der Stützhand, ein Gummipolster und der
  Ladehebel vorn links für die Stützhand. Akzent-Bedienfunktionen sind Ladehebel, Magazinhalter und Feuerwahlhebel, also drei.
- **Gleich wie BASIC-01:** Laufachse u 106, Visierlinie 70 mm darüber, Schnittstellen BGM-1, BMW-R, BMZ-15 und BRI-22, Baugruppen,
  Aktionen `fire_auto` und `reload_empty`. Die Ego-Griffpunkte sind eigene Kontakte auf diesem Modell; Richtungen und
  Fingerstellungen übernimmt es aus `basic.arms.ego`.

### Prüfung

`tests/test_extended.py` prüft:

- Felder und eindeutige IDs.
- Blatt-ID: Format `E<Linie><NN>`, Register gleich META, eindeutig, kein Zusammenstoß mit Waffen- und Roboterblättern.
- Weltpunkte mit `basic.variant.problems` als Orakel.
- Budgets: höchstens drei Leuchtfunktionen und drei Akzent-Bedienfunktionen, genau eine Schrift und ein Grafikelement.
- Visierlinie 60–80 mm über der Laufachse.
- Die Schrift liegt ganz auf der ebenen Gehäusefläche zwischen Auswurffenster und Klingenfuge. Gegenprobe: an der alten Lage f 184
  läuft sie über die Fuge.
- Seiten-IoU gegen BA01 unter 0,85. Gegenproben: BA01 gegen sich selbst ergibt 1,0, BA01 ohne Mündung bleibt über 0,85.
- Keine schwebenden Teile. Gegenprobe: ein um 40 mm versetzter Kernrahmen bildet eine eigene Gruppe.
- Länge.
- Der Quellhash enthält keinen BASIC-01-Piloten.
- Das Renderwerkzeug überspringt einen aktuellen Tag. Gegenproben, jede gegen einen frisch gültigen Stempel: geänderter Datensatz,
  anderer Quellhash, andere Samples, andere Auflösung, `--extra`, `--force` und ein fehlendes Bild starten Blender. Liefert Blender eine Ansicht nicht, bleibt das Ziel ohne
  Stempel.
- Die Seitensilhouette meldet ein Teil, das über den Rasterrahmen ragt, statt es still zu beschneiden.

## EXTENDED-10 „Bellmouth“ und EXTENDED-11 „Collimator“ (0.19 „Crucible“)

Beide Typen laden Energie auf und setzen sich deshalb bewusst voneinander ab: Das Fusionsgewehr streut, ist kurz und rund, das lineare
Fusionsgewehr bündelt, ist lang, offen und quadratisch. Gleich bleiben die Familienschnittstellen BGM-1 (Griff), BEC-1 (Energiezelle),
BMZ-15 (Mündung), BRI-22 (Schienen), die Visiere F1 „Bögen“ und Z2 „Gabel“, Kernachse und Visierlinie (66 mm), die Baugruppen und die
Aktionen von BASIC-10/11. Energiewaffen haben keinen Hülsenauswurf.

### Formideen

Drei Ideen je Typ als Seitensilhouette mit Griff, Visier und Zelle der Familie (`…/0.19/belege/skizzen/skizzen_v1.png`). Die Spalten
sind die Seiten-IoU gegen den eigenen BASIC-Typ und gegen EA01.

| Idee | Architektur | IoU BASIC | IoU EA01 | Urteil |
|---|---|---|---|---|
| **E10-A Glocke** | Ladetrommel und Streutrichter vor kurzem Gehäuse, Ringschaft | 0,69 | 0,53 | **gewählt**: die Streuung wird zur Form |
| E10-B Fächer | Blockgehäuse, vorn drei gespreizte Emitterlamellen | 0,71 | 0,54 | Lamellen lesen sich als Zähne (Stilhandbuch: verboten) |
| E10-C Kessel | Bullpup, Kugelkessel über dem Griff, dünnes Rohr | 0,49 | 0,44 | am fremdesten, wirkt aber wie ein Werfer, das Rohr bündelt statt zu streuen |
| **E11-A Kollimator** | Stabkäfig mit Fokusplatten in enger werdendem Takt, Fokuskegel | 0,62 | 0,47 | **gewählt**: die Bündelung wird zur Form |
| E11-B Hängelauf | Oberzug mit darunter gehängtem Rohr, Spalt dazwischen | 0,67 | 0,48 | dasselbe Prinzip wie die Doppelschiene von BASIC-11 |
| E11-C Teleskop | Rundrohr in vier Stufen nach vorn dünner | 0,65 | 0,53 | liest sich als Scharfschützenlauf; die Verjüngung liegt nahe an der Speerspitze |

### Formsprache

| | EXTENDED-10 „Bellmouth“ | EXTENDED-11 „Collimator“ |
|---|---|---|
| Leitmerkmal | Glocke: dicke Ladetrommel Ø 92, davor ein Trichter aus Hals und Mund (Ø 60 → 104) | Kollimator: vier blanke Stäbe, quadratische Fokusplatten im Takt 128 → 40 mm, Fokuskegel |
| Silhouette | kurz (0,56 m), vorn breiter als hinten | lang (1,13 m), offen, gerade, vorn spitz |
| Querschnitt | Drehkörper (Trommel, Trichter) über einem Gehäuse mit Tonnendach | Quadrat: Kastengehäuse mit Fasen, Platten 60 × 60, Stäbe auf den Ecken |
| Blickfang | Glutring zwischen Trommel und Glocke | Linearkern im Käfig |
| Negativraum | offener Glockenmund mit Streuscheibe, Ringschaft-Schlaufe | der ganze Käfig, Durchbruch im Optikbock, offen unter dem Schaftholm |
| Front | Lippe → Trichter → Streuscheibe mit sechs Ports → Düse | Kennplatte → Fokuskragen → Kegel mit zwei Rillen → Krone |
| Zweiton | Creme (Gehäuse, Trommel) über Graphit (Unteres Gehäuse, Wiege, Schaft); Trichter eloxiert | Creme (Gehäuse, Platten, Schaftplatte) über Graphit (Unteres Gehäuse, Unterzug, Holm) |
| Grafik, Schrift | Kennring um die Trommel; „BASIC  EX-10“ rechts | lackierte Kennplatte; „BASIC  EX-11“ rechts |

### Prüfung

`tests/test_extended_fusion.py` prüft für beide Modelle Felder, Blatt-IDs, Anker, Weltpunkte und Aktionen wie BASIC-NN (`variant.problems`
als Orakel), die Familienschnittstellen, die Budgets (genau ein Ladekern als Blickfang, höchstens drei Leuchtfunktionen), die Visierlinie,
die Lage der Schrift, die Seiten-IoU unter 0,85 gegen BASIC-NN, gegen jedes andere EXTENDED-Modell und gegeneinander (Rahmen bis f 940,
`side_iou(…, lo=…, size=…)`), den Gegensatz „Trichter öffnet / Kegel bündelt, Plattenabstand nach vorn kürzer“, den freien Kern zwischen
den Stäben, die durchgehenden Ports der Streuscheibe, Zusammenhang, Länge und Quellhash. Gegenproben haben alle Regelprüfungen
(Blatt-IDs, Weltpunkte, Schnittstellen, Budgets, Visierlinie, Schrift, Silhouette, Gegensatz, Ports, Käfig, Zusammenhang, Länge,
Renderwerkzeug); Felder, Quellhash und Snapshot-Freigabe sind reine Bestandsprüfungen. `tools/extended_render.py` registriert BALLONs
Leuchtrolle `charge_core` (`basic.pilot.energy_roles`) nur für Datensätze, die sie nutzen; Wrapper und Stempel von e01 bleiben gleich.
