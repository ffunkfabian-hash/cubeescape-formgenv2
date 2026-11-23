# EXTENDED-Modelle

Seit 0.15 „Spearhead“. Ein EXTENDED-Modell ist eine eigenständige Waffe der BASIC-Familie: eigene Silhouette, eigene Proportionen
und eigene Formarchitektur, gebaut im Vokabular des BALLON-Kits. Es ist kein Generatorlauf über einer BASIC-Grundform und kein
Umbau eines Piloten. Aus `basic.common` kommen nur die genormten Familienschnittstellen: Griffmodul BGM-1, Holovisier H0 auf der
Schiene BRI-22, Feuerwahlhebel und Ladehebel-Form, Schraubenköpfe sowie die Hilfen `rot`, `cut_box` und `mirror`.

| Kurzname | ID | Blatt-ID | Modul | Typ |
|---|---|---|---|---|
| `e01` | EXTENDED-01 „Spearhead“ | `EA01` | `formgen/models/extended/e01_spearhead.py` | Automatikgewehr |
| `e02` | EXTENDED-02 „Cadence“ | `EA02` | `formgen/models/extended/e02_cadence.py` | Impulsgewehr |
| `e03` | EXTENDED-03 „Meridian“ | `EA03` | `formgen/models/extended/e03_meridian.py` | Spähergewehr |
| `e04` | EXTENDED-04 „Sledge“ | `EA04` | `formgen/models/extended/e04_sledge.py` | Handfeuerwaffe (Handkanone) |
| `e05` | EXTENDED-05 „Duplex“ | `EA05` | `formgen/models/extended/e05_duplex.py` | Pistole (Seitenwaffe) |
| `e10` | EXTENDED-10 „Bellmouth“ | `EA10` | `formgen/models/extended/e10_bellmouth.py` | Fusionsgewehr |
| `e11` | EXTENDED-11 „Collimator“ | `EA11` | `formgen/models/extended/e11_collimator.py` | Lineares Fusionsgewehr |
| `e16` | EXTENDED-16 „Sweepguard“ | `EA16` | `formgen/models/extended/e16_sweepguard.py` | Schwert |
| `e17` | EXTENDED-17 „Gorget“ | `EA17` | `formgen/models/extended/e17_gorget.py` | Glefe |

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

Seit 0.20 (Nahkampf) vergleicht `--ref <Ordner>` mit einer beliebigen BASIC-Referenz (Bilder `hero`, `side_left`, `front`, `top`;
Ausgabe `vergleich_<Ordner>.png`), und `DETAIL` je Modell legt Ausschnitte für lange, schmale Formen an (`detail_<n>_<Ansicht>.png`).
Die e01-Ansichten und -Stempel bleiben unverändert. Ohne `--out` rendert jedes neue Modell nach `<OUT>/<Kurzname>/<tag>`,
e01 weiter nach `<OUT>/<tag>`; so überschreibt derselbe Tag kein anderes Modell.
`--ref <Ordner>` (vorhandene Bilder, `compare_dir`) und `--basic NN` aus 0.17 (Pilot im selben AAA-Weg, `compare_ref`)
bestehen nebeneinander; ohne `--out` liegt auch `BA<NN>/` von `--basic` im Ordner des Modells.

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

## EXTENDED-02 „Cadence“ (0.17 „Outrider“)

### Formideen

Vier Ideen als Seitensilhouetten mit Griff und Magazin der Familie (`~/Library/Caches/CubeEscapeFormgen2/0.17/belege/skizzen/skizzen_v1.png`).
Seiten-IoU gegen BA02 und EXTENDED-01:

| Idee | Architektur | IoU BA02 | IoU E01 | Urteil |
|---|---|---|---|---|
| **A Monoblock-Bullpup** | Magazin hinter dem Griff, Kolben in der Schale, kurz und hoch | 0,61 | 0,55 | **gewählt** |
| B Dreitakt-Segmente | konventionell, drei Haubensegmente mit Lücken | 0,82 | 0,68 | zu nah an BASIC-02 (Hülle gleich) |
| C Stirnschild | Oberlinie steigt zu einer hohen, stumpfen Stirn | 0,74 | 0,66 | starke Geste, wirkt aber kopflastig |
| D Über-Unter | zwei gestapelte Rohre | 0,77 | 0,66 | liest sich als Flinte |

A trennt sich am klarsten von BASIC-02 und von der Speerspitze und bleibt ein Impulsgewehr: Salve, Kammer mit Spulen, Salvenanzeige.
Aus B kommt der Takt der drei Spulen als Schlitzreihe dazu.

### Formsprache

- **Leitmerkmal Parallelogramm:** Kolbenende, Stirn, beide schrägen Fugen, die drei Taktschlitze, die Leuchtbalken und das Magazin
  neigen sich um 15°, so viel wie der Griff BGM-1. Länge 0,70 m, Magazin hinter dem Griff (Bullpup).
- **Querschnitt Trapez:** Schulterfasen 8 × 10 mm über die ganze Länge, oben 30 statt 46 mm.
- **Negativraum:** drei Taktschlitze, oben offen und quer durch die Kammerhaube; darin je eine Impulsspule mit blankem Ring.
- **Blickfang:** das Taktfenster links am Kolben, drei Leuchtbalken hinter Glas im blanken Rahmen; je Salvenschuss leuchtet einer.
- **Schichten:** Kammerhaube 6 mm unter dem Kolbendeck und 1 mm je Seite schmaler, schräge Fuge; Paneele in Mulden; Stirnplatte 1,5 mm vor.
- **Grafik und Schrift:** ein Schrägband parallel zur Stirn, die Schrift rechts zwischen Fuge und erstem Schlitz.
- **Front:** vorgeneigte Stirn, eloxierte Stirnplatte, blanke Laufbuchse, achtkantige Mündung, dunkle Spitze, blanke Krone.
- **Gleich wie BASIC-02:** Laufachse u 100, Holovisier H4 „Kasten“, Schnittstellen BGM-1, BMW-R, BMZ-15, BRI-22, Baugruppen, Aktionen
  `fire_burst` (drei Schuss) und `reload_empty`.

## EXTENDED-03 „Meridian“ (0.17 „Outrider“)

### Formideen

Vier Ideen im selben Skizzenbogen; Seiten-IoU gegen BA03 und EXTENDED-01:

| Idee | Architektur | IoU BA03 | IoU E01 | Urteil |
|---|---|---|---|---|
| **A Rohrachse** | Rohrschaft, Trommel und Vorderrohr auf der Laufachse | 0,70 | 0,57 | **gewählt** |
| B Teleskop | Rundrohr in drei kleiner werdenden Stufen | 0,79 | 0,60 | läuft wie die Speerspitze auf einen Punkt zu |
| C Rahmenträger | Oberer Träger mit Zielfernrohr, Lauf frei im langen Fenster | 0,66 | 0,58 | langes Fenster wiederholt den Fuller-Schlitz |
| D Kiel | schlankes Gehäuse, langer Kiel unter dem Lauf | 0,78 | 0,58 | zu nah an BASIC-03 |

A ist eine einzige ruhige Geste mit parallelen Linien statt einer Spitze. Sie setzt sich am stärksten von EXTENDED-02 ab (kurz,
hoch, kantig) und bleibt klar ein Spähergewehr: lang, Zielfernrohr, Einzelfeuer.

### Formsprache

- **Leitmerkmal koaxiale Rohrlinie:** Rohrschaft, Gehäusetrommel (r 26), Vorderrohr (r 22), Handschale, Stirn und Mündung sind
  Zylinder auf der Laufachse u 96. Ober- und Unterlinie laufen gerade und parallel vom Schaft bis zur Stirn. Länge 0,91 m.
- **Querschnitt Kreis:** Die Trommel hat seitliche Flächen bei |x| 23 für Auswurf, Paneele und Schrift, das Vorderrohr oben vier
  Längsrillen.
- **Negativraum:** das Fenster der Wangenbrücke über dem Rohrschaft und der offene Raum unter dem Rohrschaft.
- **Blickfang:** die Meridianlinie, eine Ladeanzeige als Leuchtlinie in der linken oberen Rille.
- **Schichten:** Trommel 4 mm über dem Vorderrohr mit blankem Kupplungsring, Handschale 3,5 mm über dem Rohr mit Lochreihe,
  Stirnkappe 2,6 mm zurückgesetzt.
- **Grafik und Schrift:** ein Farbring direkt vor der Handschale, die Schrift rechts auf der Trommelfläche vor dem Auswurffenster.
- **Front:** runde Rohrstirn mit Fase, eloxierte Stirnkappe, blanke Krone, eingelassene dunkle Mündung (integrierter Dämpfer).
- **Gleich wie BASIC-03:** Laufachse u 96, Zielfernrohr Z1 „Tropfen“ auf zwei Schienen BRI-22 (Visierhöhe 64 mm), Schnittstellen
  BGM-1, BMW-R, BMZ-15, Baugruppen, Aktionen `fire_semi` und `reload_empty`.

### Prüfung (beide Modelle)

`tests/test_extended_gewehre.py` prüft je Modell mit Gegenproben: Felder, Typ und Blatt-ID, dieselben Aktionen und Schusszahl wie
der BASIC-Pilot, Weltpunkte (`basic.variant.problems`), Schnittstellen, Budgets, Visierlinie, Seiten-IoU < 0,85 gegen BASIC-NN und
jedes EXTENDED-Modell ab 0,6 m, Zusammenhang, Länge, Quellhash ohne BASIC-NN. Dazu die Leitmerkmale: bei 02 eine Neigung von 15°
für Kolben, Stirn, Fugen, Schlitze, Leuchtbalken und Magazin, Durchblick in den Taktschlitzen, Leuchtbalken im offenen
Fensterschacht (Runde 1 lagen sie im Vollmaterial); bei 03 alle Rohrteile auf der Laufachse, Rillen oben, Wangenfenster offen, Lage
der Schrift. Das Paar muss sich unterscheiden (Seiten-IoU < 0,70, Bullpup gegen konventionell, Trapez gegen Kreis), und
`--basic NN` rendert nur Fehlendes oder Veraltetes.

`tools/extended_render.py e02 --tag r4 --basic 02 --out <Ziel>` rendert zusätzlich den Piloten BASIC-02 im selben AAA-Weg nach
`<Ziel>/BA02/` und setzt `vergleich_BA02.png`.

## EXTENDED-04 „Sledge“

Handkanone (Revolver) der Familie, 0.18 „Holster“. Belege außerhalb des Repos unter `~/Library/Caches/CubeEscapeFormgen2/0.18/belege/e04/`
(Runden r1–r4, je Kontaktbogen, Clay, Explosion und `vergleich_BA04.png` neben BASIC-04 v2.1), Skizzen unter `…/0.18/belege/skizzen/`.

### Formideen

Seitensilhouetten mit Griff BGM-1 und Trommel (`skizzen_v1.png`, `skizzen_v2.png`); IoU gegen BA04, BA05 und EA01.

| Idee | Architektur | BA04 | EA01 | Urteil |
|---|---|---|---|---|
| X Keule | Haube wird nach vorn tiefer, Unterlinie fällt zur Mündung | 0,71 | 0,24 | Gegenbewegung zur Speerspitze, also mit ihr verwandt |
| **A Hammerkopf** | schwerer Kopf mit Prallkammer, schlanker Hals über offener Kehle | 0,73 | 0,22 | **gewählt** |
| B Joch | tiefe Laufachse, Brücke und Lauf schließen ein großes Fenster | 0,49 | 0,23 | am fremdesten, aber das Fenster zeigt den Lauf (Motiv von EA01) |
| C Trommelring | runde Creme-Trommelhaube, kurzer Lauf | 0,75 | 0,22 | rund und weich statt wuchtig, nah an der Perlschale |
| D Stufenbrücke | erhöhte Visierbrücke hinten, gerader Kastenlauf | 0,71 | 0,25 | schwächste Geste |

A trägt die Wucht in der Masse vorn und gibt Seite, Draufsicht und Front je ein eigenes Bild (Kopf breiter als Brücke und Hals). Der
Querschnitt war zuerst als Walm mit Dachfasen gedacht; weil „Gewehre“ für EXTENDED-02 das Trapez mit Schulterfasen belegt, ist er ein
Doppel-T mit Längsnuten.

### Nachbesserung

| Runde | gesehen | geändert |
|---|---|---|
| r1 → r2 | Hals 20 mm hoch und 118 mm lang, wirkt wie ein Werkzeugstiel; Kopf weit weg | Hals 28 mm, Kopf 10 mm näher; Rahmenbug schräg, Kehle als Trapez; Kopf 38 mm breit, Stirnplatte größer; Hahnsporn kräftiger |
| r2 → r3 | Creme-Hals liest sich weiter als dünner Stiel, Hammer nicht eindeutig | Hals dunkel (Laufmantel): Sattel und Kopf stehen als zwei helle Massen |
| r3 → r4 | eloxierter Hals zeigt auf 110 mm weiße Kratzsprenkel (Stilhandbuch §9) | Hals in Graphit wie der Rahmen |

### Formsprache

Checkliste und Herkunft der Zahlen stehen im Docstring des Moduls. Kurz: Oberlinie Sattel – Hals – Kopf; Doppel-T-Querschnitt mit
durchgehender Längsnut; Negativraum in der offenen Kehle und in der Prallkammer mit drei Prallplatten und zwei Gasschlitzen; genau ein
Blickfang, das runde Zündauge links hinter der Trommel; Front mehrstufig (Kopf mit Fasen, Stirnplatte, Mündungsmulde, Krone).
Creme deckt nur 32 % der Seitenfläche über dem Griff (BA04 53 %): ein dunkles Fahrgestell mit zwei hellen Massen, keine Teilung um 50:50.
Gemessen r4: 0,300 m, 19 096 Dreiecke.

## EXTENDED-05 „Duplex“

Seitenwaffe (Schlittenpistole) der Familie, 0.18 „Holster“. Belege unter `…/0.18/belege/e05/` (r1–r4, `vergleich_BA05.png`).

### Formideen

| Idee | Architektur | BA05 | EA01 | Urteil |
|---|---|---|---|---|
| A Schräglage | Parallelogramm-Schlitten, Stirn und Heck parallel zur Griffachse | 0,80 | 0,19 | verworfen: Parallelogramm ist EXTENDED-02 |
| B Offener Schlitten | Oberseite vorn offen, Lauf liegt frei | 0,79 | 0,19 | Oberlinie hoch-tief-hoch wie E04, zu nah an BA05 |
| C Stufenschlitten | Schlitten vorn eine Stufe tiefer | 0,82 | 0,20 | fallende Oberlinie (Speerspitze), zu nah an BA05 |
| D Bogen | Oberlinie als Bogen, runde Nase | 0,80 | 0,19 | fällt zur Nase, zu nah an BA05 |
| **E Doppeldeck** | flacher Schlitten über tiefem Laufrohr, Schlitz dazwischen | 0,62 | 0,16 | **gewählt** |

Mit demselben Griff lagen alle Schlittenideen bei 0,79–0,82 gegen BA05. Erst die tiefe Laufachse (12 mm über dem Griff statt 40)
trennt die Form. Die Seite gewinnt dabei eine durchgehende Speedlinie.

### Nachbesserung

| Runde | gesehen | geändert |
|---|---|---|
| r1 → r2 | Schlitz (6,5 mm) liest sich als Strich; Schlitten 192 mm, lang und kastig; Rahmen eine dünne Platte | Schlitz 8 mm, Schlitten 20 mm kürzer, Heck gerundet, Oberdeck je Seite 2 mm eingezogen, Rahmen als Wiege fürs Rohr; Blickfang von Leuchtring auf Kapselanzeige (Glutring ist EXTENDED-10) |
| r2 → r3 | Rohrende glatt, Front ohne Stufe; Heckradius R 14 kaum sichtbar | Mündungsring mit zwei Gasschlitzen, Heck R 22, Laufbuchse kräftiger |
| r3 → r4 | Schrift hell auf Creme kaum lesbar | Schrift dunkel (`anodized`) wie BASIC-04 |

### Formsprache

Doppeldeck mit flacher, durchgehender Oberlinie; Querschnitt zweistöckig (Oberdeck 22 × 18 mm über Rundrohr Ø 20, 8 mm Luft); Negativraum ist der
Schlitz zwischen Laufbuchse und Stirn, quer ganz offen; Blickfang die Kapselanzeige links am Verschlussblock; Front zweistufig
(Schlittenstirn, 8 mm davor Mündungsring mit Krone). Creme 62 % der Seitenfläche über dem Griff. Gemessen r4: 0,197 m, 11 002 Dreiecke.

### Prüfung EXTENDED-04/05

`tests/test_extended_faustwaffen.py` prüft je Modell Felder, Blatt-IDs `EA04`/`EA05`, Weltpunkte (`variant.problems`), Familienschnittstellen
(BGM-1, Kimme/Korn K1), Budgets (genau ein Blickfang außerhalb des Visiers), freie Visierlinie, Schrift auf ebener Fläche, Seiten-IoU
< 0,85 gegen den eigenen BASIC-Typ und jedes EXTENDED-Modell bis 0,40 m, IoU < 0,70 im Paar, die Leitmotive (Hammerkopf breiter als Hals,
freie Kehle; freier Schlitz), Zusammenhang, Länge und Quellhash ohne BASIC-Piloten. Jede Schranke hat eine Gegenprobe, die aus dem
erwarteten Grund anschlägt (z. B. ein Unterlauf in der Kehle, ein Steg im Schlitz, ein Kopf über der Visierlinie).

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

## EXTENDED-16 „Sweepguard“ und EXTENDED-17 „Gorget“ (Nahkampf, 0.20)

Beide Typen entstanden in einer Sitzung, damit sie sich gezielt voneinander absetzen: Das Schwert ist eine Einhandwaffe, bei der die
Klinge dominiert, die Glefe eine Stangenwaffe, bei der der Schaft dominiert. Klingenform, Querschnitt und Leitmotiv sind verschieden,
und keines der Motive von EXTENDED-01 kehrt wieder (kein Fuller-Schlitz, keine Draufsicht-Verjüngung, keine Chevrons).

### Formideen

Je vier Seitensilhouetten (`~/Library/Caches/CubeEscapeFormgen2/0.20/belege/skizzen/skizzen_v1.png`), IoU im Rahmen f −700…1300,
u −300…400 (der Standardrahmen von `side_mask` reicht nur bis f 780).

| Idee | Architektur | IoU BASIC | IoU e01 | Urteil |
|---|---|---|---|---|
| **S-A Bogen-Säbel** | gekrümmte einschneidige Klinge, Korbbügel | 0,38 | 0,04 | **gewählt**: stärkste Geste, Negativraum aus der Funktion |
| S-B Kassettenrücken | gerade Rückenklinge, Tanto, Kreuzbalken | 0,77 | 0,04 | zu nah an BASIC-16 |
| S-C Breitkeil | Falchion, Scheibenstichblatt, Ringknauf | 0,77 | 0,04 | zu nah an BASIC-16, Keil liegt bei Serie J |
| S-D Langschwert | gerade Doppelklinge, lange Parierstange | 0,73 | 0,04 | generisch |
| **G-A Kragen** | Rundschaft mit Kragen im Takt, Keilklinge, Laterne | 0,66 | 0,10 | **gewählt**: Schaft dominiert, gerade Linien gegen den Säbel |
| G-B Sichelkopf | Sichelblatt auf Rundschaft | 0,52 | 0,12 | doppelt das Bogenmotiv des Säbels |
| G-C Drachenschild | Rautenschild um die Klingenwurzel | 0,62 | 0,12 | Raute und Spitze liegen bei EXTENDED-01 |
| G-D Gabel | zwei Zinken mit Emitter dazwischen | 0,57 | 0,12 | Formgen v1 KF18 „Gabelkrone“ hatte das schon |

### Formsprache

| | EXTENDED-16 „Sweepguard“ (Schwert) | EXTENDED-17 „Gorget“ (Glefe) |
|---|---|---|
| Leitmotiv | Schwung: Rücken steigt auf einem Bogen (54 mm Stich), Clip zur Spitze; der Korbbügel nimmt den Schwung zurück | Ringkragen im Takt: vier Creme-Kragen mit derselben vorgeneigten Stirn auf dem runden Graphitschaft |
| Silhouette | Bogen, Klinge 76 % der Länge (1,04 m), Einhandgriff 120 mm | lange Gerade, Schaft 70 % der Länge (1,60 m), kompakter asymmetrischer Kopf |
| Querschnitt | dreistufig geschichtet: Rückenschiene 11, Körper 7, Schneide 3 mm | Rundschaft, gefaste Rechteck-Kragen, Keilklinge (Querprofil) mit Rückenfläche 10 mm |
| Blickfang | Ladebogen links: drei Leuchtsegmente im Paneel | Emitterlinse in der Laterne, blank gefasst |
| Negativraum | Handraum im Korbbügel | Laternenfenster quer durch Rahmen und Schildflügel; Schusslinie unter dem Klingenrücken |
| Front | Spitze, Schneidenstufe, Klingenschuh, Parierblock mit Daumenrampe, Bügel | Schneide, Klingenhalter, Laterne mit Linse und Krone, Schildflügel, Kopfkragen |
| Zweiton | Creme-Rahmen (Parierblock, Bügel, Knaufkragen) um die dunkle Hand; Parierblock Creme über Graphitfuß | Creme-Kragen über Graphitschaft; Abzugskragen Creme über Graphit |
| Grafik, Schrift | Orange-Schrägband über zwei Stufen; Schrift rechts auf dem Paneel | Orange-Streifen parallel zur Kragenstirn; Schrift rechts auf dem Unterteil |
| Bedienung (Orange) | Ladeschalter in der Daumenrampe | Schildschalter, Zellenhalter |

Familien-DNA für Nahkampf: Es gelten Materialrollen und Zweiton, Paneele mit Schrauben, Fugen, Schichtung, Radienstufen, genau ein
Blickfang, die Budgets (Leuchten, Grafik, Schrift, Orange-Bedienung), Negativraum, mehrstufige Front und das Dreiecksbudget. Es
entfallen Visier, Visierlinie und Magazinschnittstelle, weil Nahkampfwaffen keines davon haben: BASIC-16/17 tragen weder Visier noch
Magazin, Formgen v1 legt für Schwert und Glefe „kein Visier und keine Visierschiene“ fest (`wtypes.MELEE`), und die Glefe schießt aus
der Hüfte. Die Glefe nutzt statt eines Magazins die Energiezelle BEC-1 und den Griff BGM-1 als Familienschnittstellen. Ego-Griffe
und Hülsenauswurf fehlen wie bei BASIC-16/17 (`EGO_GRIPS = {}`, kein `EJECT`).

### Prüfung

`tests/test_extended_nahkampf.py` prüft beide Modelle: Felder, Baugruppen und Anker wie der BASIC-Typ, `variant.problems` als Orakel,
kein Visier- und kein Magazinteil (Gegenprobe EXTENDED-01), Budgets, Zusammenhang, Seiten-IoU gegen den BASIC-Typ und jedes andere
EXTENDED-Modell, die Absetzung Schwert ↔ Glefe (Klingen- und Schaftanteil, Einhandgriff, Stufen gegen Keil), Negativraum als
abgeschlossene Lücke der Seitensilhouette (Gegenproben ohne Bügel und ohne Fenster), Schrift auf der Trägerfläche, Schildflügel
spiegelgleich mit deckungsgleichem Fenster, Länge, Blatt-IDs, Quellhash ohne BASIC-Modul und die Renderzusätze.
Eine Testzuordnung (`test_map.json`) führt dieses Repo nicht; `./check` findet die Datei über `unittest discover`.
