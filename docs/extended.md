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
| `e06` | EXTENDED-06 „Wishbone“ | `EA06` | `formgen/models/extended/e06_wishbone.py` | Maschinenpistole |
| `e15` | EXTENDED-15 „Flywheel“ | `EA15` | `formgen/models/extended/e15_flywheel.py` | Maschinengewehr |
| `e08` | EXTENDED-08 „Brace“ | `EA08` | `formgen/models/extended/e08_brace.py` | Schrotflinte |
| `e13` | EXTENDED-13 „Mantlet“ | `EA13` | `formgen/models/extended/e13_mantlet.py` | Granatwerfer |
| `e09` | EXTENDED-09 „Theodolite“ | `EA09` | `formgen/models/extended/e09_theodolite.py` | Scharfschützengewehr |
| `e14` | EXTENDED-14 „Keelson“ | `EA14` | `formgen/models/extended/e14_keelson.py` | Raketenwerfer |

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
Ausgabe `vergleich_ref_<Ordner>.png`, getrennt von `vergleich_BA<NN>.png` aus `--basic`), und `DETAIL` je Modell legt Ausschnitte für lange, schmale Formen an (`detail_<n>_<Ansicht>.png`).
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

## EXTENDED-06 „Wishbone“ und EXTENDED-15 „Flywheel“ (Dauerfeuer, 0.22 „Torrent“)

Beide Typen sind Dauerfeuerwaffen und entstanden in einer Sitzung, damit sie sich gezielt voneinander absetzen: Die Maschinenpistole ist
kompakt und wendig (0,42 m), ihre Form entsteht aus zwei gespreizten Schenkeln unter einem kurzen Gehäuse. Das Maschinengewehr ist schwer
(0,98 m) und trägt seine große Munitionsversorgung als Rad unter dem Gehäuse. Keine Form der Welle 1 kehrt wieder: kein Parallelogramm,
kein Sechseck, keine Rohrlinie, kein Trichter, keine Chevrons, kein Takt aus Schlitzen, Platten oder Kragen.

### Formideen

Je vier Seitensilhouetten mit Griff BGM-1 und Visier (`~/Library/Caches/CubeEscapeFormgen2/0.22/belege/skizzen/skizzen_v1.png`), IoU im
Rahmen aus den Hüllen beider Modelle; „max EA“ ist der höchste Wert gegen die neun Modelle der Welle 1.

| Idee | Architektur | IoU BASIC | max EA | Urteil |
|---|---|---|---|---|
| **E06-A Gabelbein** | Magazinschacht als Vordergriff, 24° nach vorn gespreizt; Griff und Schacht bilden ein Λ | 0,53 | 0,49 (EA10) | **gewählt**: eine Geste, die nur eine kompakte Waffe tragen kann |
| E06-B Tiefachse | hoher Block hinten, Lauf tief auf Handhöhe | 0,46 | 0,48 (EA10) | liest sich als Kamera oder Werkzeug; tiefe Achse ist EXTENDED-05 |
| E06-C Kreuz | Magazin quer links, flacher Kasten | 0,57 | 0,45 (EA10) | in der Seite beliebig, das Merkmal liegt nur in Draufsicht und Front |
| E06-D Oberdeck | Magazin längs auf dem Gehäuse | 0,60 | 0,51 (EA10) | zwei Decks übereinander wie EXTENDED-05 |
| **E15-A Schwungrad** | große Trommel quer unter dem Gehäuse, langer Mantel | 0,65 | 0,62 (EA01) | **gewählt**: der Kreis ist in der Seite einzigartig und zeigt die Munitionsmenge |
| E15-B Kielwanne | tiefer Kastenbauch vom Griff bis zum Handschutz | 0,62 | 0,55 (EA01) | schwer, aber derselbe Kasten vor dem Griff wie BASIC-15 |
| E15-C Buckel | hoher Munitionsturm auf dem Gehäuse, Visier hinten | 0,60 | 0,57 (EA01) | der Turm verdeckt die Visierlinie, das Visier muss nach hinten |
| E15-D Kastenschaft | Munitionskasten als Schaft, dünner langer Lauf | 0,65 | 0,63 (EA02) | Magazin hinter dem Griff ist EXTENDED-02 (Bullpup) |

A trägt bei der MP die Spreizung als einzige große Geste: Der Schacht ist zugleich Vordergriff, also entsteht die Form aus der
Funktion. B–D wiederholen Motive der Welle 1 oder lesen sich nur aus einer Richtung. Beim MG zeigt nur A die große Munitionsversorgung
als eigene Form, statt sie in einen Kasten zu packen. Beide Wahlen setzen sich zueinander ab: Winkel gegen Kreis, kompakt gegen lang.

### Formsprache

| | EXTENDED-06 „Wishbone“ (Maschinenpistole) | EXTENDED-15 „Flywheel“ (Maschinengewehr) |
|---|---|---|
| Leitmotiv | Gabelbein: Schacht als Vordergriff 24° nach vorn, Griff 15° nach hinten; Kinnstirn und Λ-Fenster folgen den Schenkeln | Schwungrad: Gurttrommel Ø 156 quer unter dem Gehäuse, fünf Speichen, offene Nabe |
| Silhouette | kurz (0,42 m), Λ unter einem kurzen Gehäuse, Wangenstufe hinter dem Visierturm | lang (0,98 m), gerade Oberlinie, Rad zwischen Griff und Stützhand, gerippter Mantel |
| Querschnitt | T: Creme-Deck 48 mm kragt 6 mm je Seite über den Graphit-Rumpf (36 mm), Rückenleiste oben | Kreuz: Kühlmantel mit vier Rippen (Hochrippen Creme, Seitenrippen Graphit) um den runden Kern; Gehäuse 56 mm breit |
| Blickfang | Λ-Fenster links am Deck: dreieckige Munitionsanzeige, Seiten 15° und 24° | Leuchtspeiche links an der Trommel: Füllstand hinter Glas im blanken Rahmen |
| Negativraum | Gabelzwickel: Abzugsraum zwischen Griff, Schacht, Rumpf und Bügel; darunter öffnet sich das Λ | offene Nabe Ø 36 quer durch die Trommel; Luft zwischen den Mantelrippen |
| Front | Kinnstirn 24° mit Stirnplatte → Laufbuchse → runder Kompensator mit Seitenports → Krone | gefaste Rippenenden → Mantelkragen → runde Bremse mit Kreuzports → Krone |
| Zweiton | Creme-Deck über Graphit-Rumpf und Graphit-Schacht; Magazin Creme | Creme-Gehäuse, -Deckel, -Mantelträger, -Kolben, -Trommelscheiben über Graphit (Unteres Gehäuse, Handschutz, Kranz, Kiel) |
| Grafik, Schrift | Orange-Längsstreifen links vorn am Deck; „BASIC  EX-06“ rechts am Deck | Orange-Querband am Kolben; „BASIC  EX-15“ rechts am Gehäuse |
| Bedienung (Orange) | Ladehebel, Magazinhalter, Feuerwahlhebel | Ladehebel, Deckelriegel, Feuerwahlhebel |
| Familie | BGM-1, BMW-R (gerades Magazin im Schachtgriff), BMZ-15, BRI-22, Holovisier H2 „Pille“ wie BASIC-06 | BGM-1, BAB-1 (Einhängeplatte), BMZ-15, BRI-22, Holovisier H6 „Achteck“ L wie BASIC-15 |

Gleich wie der BASIC-Typ bleiben Baugruppen, Anker, Weltpunkte und Aktionen (`fire_auto`, `reload_empty` bzw. `reload` mit Deckel und
Trommel). Die Trommel ist eine Gurttrommel: Der Gurt läuft im geschlossenen Zuführhals links ins Gehäuse, Glieder und Hülsen fliegen
rechts aus wie bei BASIC-15.

### Nachbesserung

Belege: `~/Library/Caches/CubeEscapeFormgen2/0.22/belege/e06/r1–r5` und `…/e15/r1–r5`, je mit Kontaktbogen, Clay, Explosion und
`vergleich_BA06.png` bzw. `vergleich_BA15.png` (Pilot im selben AAA-Weg unter `e06/BA06`, `e15/BA15`).

| Typ | Runde | gesehen | geändert |
|---|---|---|---|
| E06 | r1 → r2 | Körper ein glatter Kasten, Kolben ohne Form; Schiene über das ganze Deck wie BASIC-01; Ladehebel drängt sich neben das Λ-Fenster; Kompensator klein; T-Überstand kaum zu sehen | Wangenstufe hinter dem Visierturm, Kolbenkappe so breit wie das Deck; Schiene nur unter dem Visier; Ladehebel hinten links; Kompensator Ø 27 mit drei Ports; Deck 48 mm (Überstand 6 mm) |
| E06 | r2 → r3 | Heck so hoch wie die Front, die MP wirkt wie eine Pistole mit langem Heck | Rumpfunterkante steigt zum Kolben (u 40 → 68), der Kolben verjüngt sich; Paneele mitgeführt |
| E06 | r3 → r4 | Rahmen des Λ-Fensters ragt über die Deckkante; Wangenstufe zaghaft; Draufsicht eine glatte Fläche | Fenster tiefer, Rahmen oben gekappt; Wangenstufe 12 mm; Rückenleiste 20 mm breit (zuerst als Schnitt) |
| E06 | r4 → r5 | Schnitt der Rückenleiste gibt Schattierungsfehler quer über die Deckflanke, das Fenster wirkt grau | Rückenleiste als eigenes Teil auf dem Deck; Fenster und Leuchtdreieck wieder klar |
| E15 | r1 → r2 | langer dünner Stab mit Rad; Mantel liest sich als Schiene mit Schlitz; Kolbenpaneele wirken wie Fenster; Bremse klein | Mantel 288 → 242 mm, Kern Ø 44, Rippen r 40 × 10, Seitenrippen Graphit (Kreuz lesbar); Kolben mit Graphit-Kiel statt Paneelen, 180 mm; Bremse Ø 36 |
| E15 | r2 → r3 | Wangenauflage ein dunkles Rechteck wie ein Loch; Zuführhals eine flache dunkle Platte; Trommelgriff ein Klotz | Wangenauflage entfernt; Zuführhals verjüngt sich zur Trommel, drei Schrauben; Trommelgriff 24 statt 34 mm |
| E15 | r3 → r5 | 34 876 Dreiecke (Ziel 20 k, Grenze 50 k) | Segmente der Rundteile gesenkt (Trommel 48, Nabe, Kern, Kragen 32, Bremse 24): 30 436 Dreiecke |

### Motivzeilen (für die Familie)

| Typ | Leitmotiv | Silhouette | Querschnitt | Blickfang | Negativraum | Front |
|---|---|---|---|---|---|---|
| EA06 MP „Wishbone“ | Gabelbein: Schachtgriff 24° vorn, Griff 15° hinten | kurz 0,42 m, Λ unter kurzem Gehäuse, Wangenstufe | T (Deck kragt über Rumpf), Rückenleiste | Λ-Fenster (Dreieck 15°/24°) links am Deck | geschlossener Gabelzwickel | Kinnstirn 24° mit Stirnplatte, runder Kompensator mit Seitenports |
| EA15 MG „Flywheel“ | Schwungrad: Gurttrommel Ø 156 quer unter dem Gehäuse | lang 0,98 m, gerade Oberlinie, Rad zwischen Griff und Stützhand | Kreuz (Kühlmantel mit vier Rippen) | Leuchtspeiche links an der Trommel | offene Nabe Ø 36 | gefaste Rippenenden, Mantelkragen, runde Bremse mit Kreuzports |

### Prüfung

`tests/test_extended_dauerfeuer.py` prüft beide Modelle: Felder, Typ und Feuerart wie BASIC-NN, Blatt-IDs, Anker, Weltpunkte und Aktionen
(`variant.problems` als Orakel), Familienschnittstellen, Budgets (genau ein Blickfang links außerhalb des Visiers, ≤ 3 Akzent-Bedienfunktionen,
eine Schrift, ein Grafikelement), Visierlinie 60–80 mm, Schrift auf der freien Seitenfläche, Seiten-IoU < 0,85 gegen BASIC-NN und jedes
andere EXTENDED-Modell sowie < 0,70 im Paar (Rahmen aus den Hüllen beider Modelle wie `test_extended_fusion`), die Leitmotive (Spreizung
24° gegen Griff, Magazin, Kinnstirn und Λ-Fenster auf den Schenkeln; Gabelzwickel als geschlossene Lücke der Seitensilhouette; T-Überstand
≥ 5 mm; Trommel quer, Ø ≥ 140, zwischen Griff und Stützhand, Nabe quer durch alle Trommelteile und in der Seite frei; vier Mantelrippen
≥ 8 mm), kompakt gegen schwer, Zusammenhang, Länge und Quellhash ohne BASIC-Piloten. Jede Regelprüfung hat eine Gegenprobe (z. B. senkrechter
Schacht, Abzugsbügel entfernt, bündiges Deck, Achse in der Nabe, Sackloch, zarte Rippen, Glefe im Standardrahmen). Ausnahme beim
Zusammenhang: Kontur, Glas und Absehen des Holovisiers H2 stehen frei vor dem Emitter, beim Piloten BASIC-06 genauso (der Test belegt es).

Gemessen (Spec der letzten Runde): EA06 0,415 m, 20 418 Dreiecke (r5); EA15 0,978 m, 30 436 Dreiecke (r5, über dem Ziel 20 k, unter der
Grenze 50 k: Trommel, Nabe und Mantel sind Rundkörper).

## EXTENDED-08 „Brace“ und EXTENDED-13 „Mantlet“ (Streuung, 0.23 „Breacher“)

Beide Typen haben ein großes Kaliber und entstanden in einer Sitzung, damit sie sich gezielt voneinander absetzen: Die Schrotflinte ist
eine Nahkampfwaffe mit Pumpe, flach und lang, und zeigt die Streuung als Breite – zwei Läufe nebeneinander statt eines Trichters. Der
Granatwerfer verschießt schwere Einzelgeschosse im Bogen; er ist kurz und gedrungen, eine Helmwölbung liegt über dem Verschluss, und die
Munition sitzt in einem Kastenmagazin vor dem Griff statt in einer Trommel (BASIC-13 längs, EA15 quer). Keine Form der Motivtabelle kehrt
wieder: kein Trichter, keine Glocke, keine Streuscheibe, keine Rohrlinie, kein Doppeldeck übereinander, keine Chevrons, kein Takt.

### Formideen

Je vier Seitensilhouetten mit Griff BGM-1 und Visier (`~/Library/Caches/CubeEscapeFormgen2/0.23/belege/skizzen/skizzen_v1.png`), IoU im
Rahmen aus den Hüllen beider Modelle; „max EA“ ist der höchste Wert gegen die elf EXTENDED-Modelle der Welle 1 und von „Dauerfeuer“.

| Idee | Architektur | IoU BASIC | max EA | Urteil |
|---|---|---|---|---|
| **E08-A Zwilling (Brille)** | zwei Läufe nebeneinander, flacher Mantel, Joch | 0,63 | 0,68 (EA03) | **gewählt**, zusammen mit B |
| **E08-B Schiebemantel** | große Pumpe als Mantel um die Läufe, freie Läufe davor | 0,63 | 0,62 (EA03) | **gewählt**: der Mantel trägt die Brille |
| E08-C Kielpumpe | Pumpe als tiefer Kiel unter dem Lauf | 0,63 | 0,60 (EA03) | Kiel unter dem Lauf liegt bei EA06 (Schachtgriff) und EA15 |
| E08-D Unterhebel | Hebelrepetierer mit Bügel um die Hand | 0,60 | 0,65 (EA03) | Handraum im Bügel ist EA16 |
| E13-A Ladewanne | offene Wanne zeigt die nächste Granate | 0,66 | 0,58 (EA02) | Oberlinie hoch-tief-hoch wie EA04, Granate im Fenster wie BASIC-13 |
| **E13-B Buckelhaube** | Haube über dem Verschluss, Kastenmagazin, dicker Lauf | 0,60 | 0,55 (EA10) | **gewählt**: eine Geste, die nur der Werfer trägt |
| E13-C Knickschaft | Schaft stark abgewinkelt, dicker Lauf | 0,58 | 0,58 (EA02) | ein Holovisier 60–80 mm über dem Lauf braucht einen hohen Kamm |
| E13-D Querleiste | Kammerleiste quer durchs Gehäuse (Harmonika) | 0,69 | 0,61 (EA02) | in der Seite beliebig, die Rolle wie die Trommel (Kammerträger) |

A und B der Schrotflinte ergänzen sich: Zwei Läufe zeigen die Streuung als Breite, ohne Trichter, und der Schiebemantel ist die Pumpe,
die den Typ trägt. Beim Werfer zeigte der Bau, dass eine hohe Kuppel mit dem Visiervertrag kollidiert: Das Visier muss 60–80 mm über der
Laufachse sitzen, darüber darf die Haube nicht stehen. Die Haube wurde deshalb zum Helm mit Visiergasse – die Flanken reichen bis an die
Visierlinie, das Visier blickt durch einen Kanal in der Wölbung, vorn kragt ein Schirm über die Stirn.

### Formsprache

| | EXTENDED-08 „Brace“ (Schrotflinte) | EXTENDED-13 „Mantlet“ (Granatwerfer) |
|---|---|---|
| Leitmotiv | Brille: zwei Läufe nebeneinander, eine Pumpe als Schiebemantel repetiert beide Kammern | Panzerhaube: Helmwölbung über dem Verschluss, Schirm über der Stirn, aus der der dicke Lauf tritt |
| Silhouette | flach und lang (0,79 m), gerade Oberlinie vom Kolben bis zum Joch; der Mantel ist die große Masse vor dem Gehäuse, davor laufen die Läufe frei | kurz und gedrungen (0,65 m): Wölbung steigt 52 mm vom Kolben zum Scheitel, fällt 26 mm in den Schirm; großes Kastenmagazin vor dem Griff |
| Querschnitt | Brille: zwei Wülste über den Läufen in Gehäuse (mit Mittelsteg), Mantel, Joch und Kolbenhals; 66–72 mm breit; Flankenfeld 2,4 mm unter den Wülsten | U: zwei Haubenflanken beiderseits der 34 mm breiten Visiergasse, blanke Gassenkanten; Lauf rund Ø 54 |
| Blickfang | Zwillingsauge links am Gehäuse: zwei runde Kammeranzeigen in einer Achter-Fassung | Ladeanzeige links an der Haube: Leuchtfenster in Geschossform (Spitzbogen nach vorn) |
| Negativraum | Brillenspalt 12 mm zwischen den freien Läufen vom Mantel bis zum Joch; Kolbenspalt 12 mm zwischen den Wangen; Hubspalt zwischen Gehäuse und Mantel | Visiergasse als Kanal durch die Wölbung vom Visiersitz bis vor den Schirm; Schatten unter dem Schirm über dem Lauf |
| Front | Brillenjoch mit zwei blanken Kronen und Kornsockel → Brillenspalt → Mantelstirn mit Handstopp | gefaster Mündungsring mit Krone → Lauf über dem Handschutzkiel → Blendenkragen → Stirn unter dem Schirm |
| Zweiton | Creme-Gehäuse und Kammkappen über Graphit (Unteres Gehäuse, Kolbenhals und -wangen, Mantel); Joch, Mantelstirn und -kragen eloxiert | die Creme-Haube ist die einzige helle Masse über einem Graphit-Fahrgestell (Magazin, Lauf, Kolben, Unteres Gehäuse) |
| Kolben (Runde 9/12) | Spaltkolben: ein Graphit-Hals nimmt die Wülste auf, verjüngt sich und teilt sich in zwei Wangen mit Creme-Kammkappen; dazwischen der offene Kolbenspalt, quer durch beide Wangen das Brillenfenster (zwei verschmolzene Kreise, blank gefasst); Schaftkappe zurückgeneigt | Nackenschutz als Fortsetzung der Haube: drei Creme-Schalen im Querschnitt der Haube (Schultern r 10, Kammrinne, eingezogene Unterkante), jede 3 mm tiefer und 4 mm schmaler und 6 mm in der vorigen; die Haube verjüngt sich hinten auf die erste Schale; kein Kern darunter |
| Grafik, Schrift | zwei Orange-Querstreifen vorn am Gehäuse; „BASIC  EX-08“ rechts, dunkel auf Creme | Orange-Bogenstreifen parallel zur Wölbung; „BASIC  EX-13“ rechts hinten an der Haube |
| Bedienung (Orange) | Pumpenriegel, Laufwähler (oben hinten, wie der Schieber einer Doppelflinte) | Magazinhalter, Ladehebel |
| Familie | BGM-1, Kimme/Korn K2 „Hörner“ (Kimme auf kurzer Schiene BRI-22, Korn auf dem Joch), Visierlinie 39 mm über der Laufachse wie BASIC-08 | BGM-1, W1 „D-Linse“ auf BRI-22 wie BASIC-13, Visierlinie 74 mm |

Gleich wie der BASIC-Typ bleiben Baugruppen, Anker, Weltpunkte und Aktionen (`fire_pump`/`load_shell` bzw. `fire`/`reload`). Der Werfer
ist ein Halbautomat mit Kastenmagazin: Die Hülse fällt je Schuss rechts aus dem Auswurffenster, nicht erst beim Nachladen wie bei der
Trommel von BASIC-13; `Socket_LoadingGate` liegt am Magazinboden.

### Nachbesserung

Belege: `~/Library/Caches/CubeEscapeFormgen2/0.23/belege/e08/r1–r14` und `…/e13/r1–r13`, je mit Kontaktbogen, Clay und Explosion; e08/r7, e13/r8, e08/r10, e13/r11, e13/r13 und e08/r14
als AAA-Lauf (1600 px, 96 Samples) mit `vergleich_BA08.png` bzw. `vergleich_BA13.png` (Pilot im selben AAA-Weg unter `e08/BA08`, `e13/BA13`).

| Typ | Runde | gesehen | geändert |
|---|---|---|---|
| E08 | r1 → r2 | Gehäuse, Mantel und Kolben glatte Kästen; die Brille nur am Joch lesbar | Brillen-Querschnitt (zwei Wülste) für Gehäuse, Mantel und Joch; Paneel rechts; Kolben neu |
| E08 | r2 → r3 | Facettenstreifen auf dem Mantel; Gehäusewülste unter der breiten Schiene unsichtbar; Kolben ein Creme-Kasten | 16 Segmente je Wulst; Mittelsteg 12 mm; Kolben mit gerundetem Kamm |
| E08 | r3 → r4 | Kolben weiter kastig, Gehäuseflanke leer | Kolben 46 mm breit, Kiel höher, obere Kanten gerundet; Schulterfuge entlang der Wülste |
| E08 | r4 → r5 | lange dunkle Schiene deckt die Wülste; Waffe 0,83 m lang | Schiene nur unter der Kimme, Creme-Steg trägt die Linie; Mantel 220 mm, freie Läufe 78 mm, Kolben 158 mm (0,78 m) |
| E08 | r5 → r6 | Gehäuse und Kolben lesen sich als ein Creme-Balken; Wangenpolster wirkt von oben wie ein Loch | Kolben Graphit mit Creme-Kammkappe, Polster entfernt |
| E08 | r6 → r7 | (Test) Schrift lief über die Zwillingsstreifen; Senke im Joch nur 4 mm | Streifen 5 mm nach vorn, Schrift 4,4; Jochsteg tiefer (Senke 10 mm), Gehäusesteg 16 mm |
| E13 | r1 → r2 | Haube liest sich als Kasten, der Kolben verdeckt die Wölbung; Ladeanzeige unsichtbar (Mulde 0,9 mm, Leuchte darunter) | Scheitel 12 mm höher, Visiergasse durch die Wölbung; Mulde 6 mm; Kolben schmaler |
| E13 | r2 → r3 | Oberseite weiter flach; der Kamm auf der Haube wirkt wie eine Schiene | Helmkontur mit Schirm über der Stirn; Kamm durch blanke Gassenkanten ersetzt |
| E13 | r3 → r4 | Schirm läuft spitz aus wie ein Schnabel (zu zart); Kolben ein Kasten | Schirmstirn 12 mm; Kolben ganz Graphit |
| E13 | r4 → r5 | (Test) Magazin ragte in den Abzugsbügel (f 64 gegen Bügel bis 83) | Magazin ab f 90, Front 20 mm nach vorn |
| E13 | r5 → r6 | Ringspalt r 40 schnitt seitlich durch die 64 mm breite Haube; Lauf mit Gummimanschette und vier Ringen wirkte wie ein Kameraobjektiv | Lauf Ø 54 mit Blendenkragen statt Spalt; Handschutzkiel statt Manschette; ein gefaster Mündungsring |
| E13 | r6 → r7 | vorn fiel die Wölbung nur 16 mm; Daumenmulde im Kolben wirkt wie ein Fenster | Scheitel nach vorn (f 30), Schirm 10 mm tiefer (Fall 26 mm); Kolben ohne Mulde |
| E08 | r7 (Bewegung) | (Richter R2) beim vollen Hub lief der Mantel 4 mm in die Laufkragen | Hub 62 → 56 mm; der Test fegt den Hub gegen alle festen Teile; Bewegungsbeleg `e08/pumpe/pumpe_hub56.mp4` (Ruhelage unverändert) |
| E13 | r7 → r8 | (Richter R1) Profil der Gassenkanten selbstschneidend: beide Hälften liefen vorwärts | Umkehr entfernt; Test `test_profiles_simple` prüft alle Profile beider Modelle |
| E08 | r7 → r9 | (Nutzer „Erst nachbessern“, Koordination) Kolben eine schlichte Platte wie bei E13; Gehäuse und Mantel Kästen ohne Struktur; weniger Detail als BASIC-08 | Spaltkolben mit Hals aus den Wülsten; Flankenfeld 2,4 mm (Schulterstufe) mit Paneelen links und rechts, Querbolzen; Mantel mit Stirn (2,5 mm) und Hinterkante (1,5 mm) eloxiert, drei Griffrippen je Flanke, Mittelleiste, Kragenschrauben |
| E08 | r9 → r10 | Wangen unten gerade, der Kolben wirkt von der Seite als Platte | Unterlinie mit steigendem Hals vor dem Abfall zur Kolbenspitze |
| E13 | r8 → r9 | (Koordination) Schirm wirkt wie ein aufgelegtes Blech; Kolben fast gleich dem von E08; Detail unter BASIC-13 | Schirm wächst mit einer Kehle aus der Stirn (22 mm stark, 12 mm an der Spitze), Nase, Fase unter den Kanten, gerundete Ecken; Lamellenkolben; Auswurfklappe mit Scharnier, Nut des Ladehebels, Magazinplatten mit Schrauben, Kielschrauben; Gassenkanten bis zum Schirm |
| E13 | r9 → r10 | Lamellen lesen sich als drei Klötze | Lamellen als Schindeln: schräge Hinterkante, Oberkante fällt, größere Rundung |
| E08 | r10 → r12 | (Nutzer „Noch eine Runde“, Koordination) Kolben von der Seite eine graue Platte mit stumpfer Kante; Hauptkörper Quader mit Details; Rückansicht nur Rechtecke | Brillenfenster quer durch beide Wangen mit blanker Fassung, Unterlinie gerade fallend mit gerundeter Spitze, Schaftkappe zurückgeneigt (R_BODY); Mantel, Kragen und Joch unten 4–5 mm eingezogen; Unteres Gehäuse nach unten 6,5 mm eingezogen, R_BODY; Kragenschrauben der Kammkappen entfallen |
| E08 | r12 → r13 | 33 150 Dreiecke (Koordination: nicht wachsen) | 12 statt 16 Segmente je Wulst, 14 je Fensterkreis: 31 228 |
| E08 | r13 → r14 | (Richter R7) die Fensterkreise berührten sich nur (Abstand = 2 r), das Schnittprofil hatte einen Berührpunkt und einen doppelten Schlusspunkt | Kreise 20 mm auseinander (Taille 17 mm), doppelte Punkte entfernt; `test_profiles_simple` prüft jetzt auch Schnittprofile und Berührpunkte |
| E13 | r11 → r12 | (Koordination) Lamellen wirken wie Klötze auf der alten Kolbenplatte, ein angesetztes Teil; Unterbau, Magazin und Kiel Quader | Kolben als drei Creme-Schalen im Querschnitt der Haube, ohne Graphit-Kern, die Haube verjüngt sich hinten auf die erste Schale und endet auf Kammhöhe; Haubenunterkante, Unteres Gehäuse und Kiel eingezogen (R_BODY), Magazin mit gefasten Vorderkanten und eingezogenem Boden, Schachtlippe gefast |
| E13 | r12 → r13 | Kolbenhals unter der Haube zu hoch (Schale bis u 54) | Unterlinie beginnt bei u 66 und fällt zur Schulter; Unteres Gehäuse hinten passend angehoben |
| E13 | r10 → r11 | (Richter R5) die neue Auswurfklappe bewegte sich im Schussablauf nicht und deckte beim Auswurf das Fenster | Auswurfschieber gleitet in zwei Leisten 64 mm nach vorn, öffnet vor dem Auswurf (Frame 5) und schließt danach; Test mit Gegenproben; Bewegungsbeleg `e13/schieber/schieber.mp4` |

### Motivzeilen (für die Familie)

| Typ | Leitmotiv | Silhouette | Querschnitt | Blickfang | Negativraum | Front |
|---|---|---|---|---|---|---|
| EA08 Schrotflinte „Brace“ | Brille: zwei Läufe nebeneinander, Pumpe als Schiebemantel | flach und lang 0,79 m, gerade Oberlinie, freie Läufe vor dem Mantel | Brille (zwei Wülste) in Gehäuse, Mantel und Joch | Zwillingsauge (zwei runde Kammeranzeigen) links | Brillenspalt zwischen den freien Läufen, Kolbenspalt und Brillenfenster im Kolben | Brillenjoch mit zwei Kronen und Kornsockel; Kolben: Spaltkolben mit Brillenfenster |
| EA13 Granatwerfer „Mantlet“ | Panzerhaube: Helmwölbung über dem Verschluss, Schirm über der Stirn | kurz und gedrungen 0,65 m, Wölbung über großem Kastenmagazin, dicker Lauf | U: Haubenflanken beiderseits der Visiergasse | Ladeanzeige in Geschossform links | Visiergasse durch die Wölbung, Kehle unter dem Schirm | Mündungsring → Lauf über Handschutzkiel → Blendenkragen → Stirn unter dem gefasten Schirm; Kolben: Schalen als Fortsetzung der Haube |

### Prüfung

`tests/test_extended_streuung.py` prüft beide Modelle: Felder, Typ und Feuerart wie BASIC-NN, Blatt-IDs, Anker, Weltpunkte und Aktionen
(`variant.problems` als Orakel), Familienschnittstellen, Budgets (genau ein Blickfang links außerhalb des Visiers, ≤ 3 Akzent-Bedienfunktionen,
eine Schrift, ein Grafikelement), Visierlinie (Kimme/Korn höchstens 4 mm anders als BASIC-08, D-Linse im Vertrag 60–80 mm), Schrift auf der
freien Seitenfläche, Seiten-IoU < 0,85 gegen BASIC-NN und jedes andere EXTENDED-Modell sowie < 0,70 im Paar (Rahmen aus den Hüllen beider
Modelle), die Leitmotive (zwei Läufe mit offenem Brillenspalt ≥ 10 mm; Wülste im Querschnitt von Gehäuse, Mantel und Joch; Mantel trifft
beim Hub kein festes Teil, Verschluss läuft mit; Zwillingsauge; Helmwölbung ≥ 40 mm Anstieg und Schirm über der Stirn; Sichtkanal vor dem Glas frei;
Visiergasse ≥ 10 mm tief bis vor den Schirm; Kastenmagazin vor dem Abzugsbügel, keine Trommel; Ladeanzeige mit einer Spitze vorn),
seit Runde 9 Flankenfeld (2–3 mm), Mantelstirn und -kragen, Griffrippen, offener Kolbenspalt, Schirmstärke mit Fase und Ecken, gestufte
und überlappte Lamellen, Detaildichte mindestens wie der BASIC-Pilot, seit Runde 12 gestaltete Querschnitte der Hauptkörper (Breite ändert sich über die
Höhe oder Einzugs-/Fasenschnitte mit Radius ≥ R_MID) und ein Kolben ohne angesetzten Kern, bündig aus der Haube, Flinte gegen Werfer (Länge, Bohrung, Pumpe gegen Magazin, gedrungen), Zusammenhang, Länge und Quellhash ohne BASIC-Piloten. Jede
Regelprüfung hat eine Gegenprobe (z. B. Steg im Brillenspalt, volle Wange im Kolbenspalt, Blech statt Schirm, glatte Lamellen, ohne blanke Teile, abgeflachter Mantel, doppelter Hub, flacher Deckel, Gasse zu, Pfosten im
Sichtkanal, Rille statt Gasse, Sackgasse). Der Magazintest fand in Runde 4 ein Magazin im Abzugsbügel, das im Render nicht auffiel.

## EXTENDED-09 „Theodolite“ und EXTENDED-14 „Keelson“ (Schulter, 0.25 „Pauldron“)

Beide Typen liegen an der Schulter und sind lang. Deshalb entstanden sie in einer Sitzung und setzen sich gezielt voneinander ab. Das
Scharfschützengewehr ist ein Messinstrument: ein schlanker Rautenrumpf, der auf drei Stützen steht und dazwischen frei spannt. Der
Raketenwerfer ist ein großvolumiger Rumpf: Das Startrohr liegt als Deck auf einem tiefen Kiel mit Tropfenquerschnitt. Keine Form der
Motivtabelle kehrt wieder: keine Rohrlinie und keine parallelen Linien wie EA03, kein Käfig wie EA11, keine Speerspitze wie EA01. Es
gibt keinen Trichter, keine Glocke, keine Krone auf einer runden Rohrstirn und keine Helmhaube, auch keine Chevrons und keinen Takt.

### Formideen

Seitensilhouetten mit Griff BGM-1, Visier und eingezeichneter Visierlinie (`~/Library/Caches/CubeEscapeFormgen2/0.25/belege/skizzen/skizzen_v1.png`,
`skizzen_v2.png`). Die IoU steht im Rahmen aus den Hüllen beider Modelle; „max EA“ ist der höchste Wert gegen die 13 vorhandenen EXTENDED-Modelle.

| Idee | Architektur | IoU BASIC | max EA | Urteil |
|---|---|---|---|---|
| **E09-A Stativ (Theodolit)** | Rautenrumpf auf drei Stützen: Magazin, Zweibeinpylon, Einbein; offene Spannweite | 0,64 | 0,57 (EA03) | **gewählt** |
| E09-B Nadel | kompakte Masse hinten, sehr langer freier Lauf, Vordergriff | 0,59 | 0,55 (EA13) | 1,25 m lang; Stützhand ohne Halt, wirkt wie ein Stab mit Klotz |
| E09-C Kielrumpf | ein langer Rumpf mit gewölbtem Bauch | 0,70 | 0,59 (EA03) | nah an BASIC-09 (Haube mit tiefem Vorderschaft) |
| E09-D Ausleger-Deck | hohes Deck über freiem Lauf mit Spalt | 0,61 | 0,58 (EA03) | Doppeldeck wie EA05 |
| W-A Spindel | Rohr dick in der Mitte, dünn zu Mündung und Heck | 0,90 | 0,55 (EA01) | zu nah an BASIC-14; dicke Mitte vor dem Seitenvisier verdeckt die Sicht |
| W-B Schultersattel | gerades Rohr, großer Sattel unter dem Heck | 0,82 | 0,52 (EA01) | nah an BASIC-14 |
| W-C Kanister auf Rückgrat | Wechselrohr auf einem Graphit-Rückgrat | 0,81 | 0,55 (EA01) | nah an BASIC-14 |
| W-D Kielrohr | Rohr mit flachem Kiel unter dem Vorderteil | 0,84 | 0,54 (EA01) | knapp unter der Schwelle |
| W-E Rumpf (Achse u 112) | Rohr auf tiefem Kiel, Achse wie BASIC | 0,81 | 0,55 (EA15) | Idee trägt, Lage wie BASIC |
| W-F Spindel lang | längere Spindel, Visier 70 mm | 0,83 | 0,56 (EA15) | wie W-A |
| **W-G Rumpf hoch** | Startrohr als Deck auf tiefem Kiel, Achse u 140 | 0,58 | 0,47 (EA13) | **gewählt** |
| W-H Spindel hoch | Spindel mit Achse u 140 | 0,54 | 0,42 (EA01) | Bauch reicht bis 10 mm an die Visierlinie |

Die Skizzen zeigten für den Werfer eine Zwangsbedingung. Neben dem Seitenvisier (66 mm links auf Achshöhe) und neben dem Kopf darf das
Rohr nicht dicker werden als bei BASIC, sonst ragt die Rohrwand näher als 20 mm an die Visierlinie (Stilhandbuch). Jede Idee mit dem
Volumen um die Achse blieb deshalb bei IoU 0,81–0,90 gegen BASIC-14. Erst der Rumpf legt das Volumen **unter** die Achse, wo es die Sicht
nicht stört. Zugleich hebt er die Achse auf u 140, und der Kiel füllt den Raum bis zum Griff. Das Gewehr wählt das Stativ: eine einzige
Geste, die nur ein Präzisionsgewehr trägt. Aus D kam nichts dazu, aus C die Idee einer durchgehenden Rumpflinie vom Kolben bis zur Stirn.

### Formsprache

| | EXTENDED-09 „Theodolite“ (Scharfschützengewehr) | EXTENDED-14 „Keelson“ (Raketenwerfer) |
|---|---|---|
| Leitmotiv | Stativ: ein Messinstrument auf drei Stützen – Griff mit Magazin, Pylon und Kolbenbein; Pylon und Kolbenbein stehen auf Gummisohlen (Runde 5) | Rumpf: das Startrohr als Deck auf einem tiefen Kiel; ein zweiter, kleiner Kiel ist der Schultersattel |
| Silhouette | lang (1,18 m), gerade Decklinie, hinten zum Wangenkamm gestuft; unten Spannweite (Magazin → Pylon) und Kolbenbogen (Griff → Kolbenbein) offen; langer freier Lauf | 0,92 m: gerade Decklinie vom Kegel bis zur Stirn, darunter ein flacher Bauch, der nach vorn zur Tropfenstirn und nach hinten als Kielhacke zum Abgasrohr steigt; Abgasrohr mit Sattel über der Schulter |
| Querschnitt | Raute mit Gürtel: Oberschale und Kiel laufen schräg zu Deck (22–33 mm) und Kiel (12 mm), dazwischen ein senkrechter Gürtel 13 mm hoch mit der Fuge; derselbe Querschnitt bildet Kolben, Pylon und Schaftkappe | Tropfen: Kreis r 46 um die Bohrung, Flanken 18° zum Kiel; Kielschale 1,5 mm unter der Rumpfschale; Sattel und Stirnplatte im selben Tropfen |
| Blickfang | Libelle links unter dem Zielfernrohr: leuchtendes Röhrchen mit blanker Blase, Kappen und drei Teilstrichen | Zielerfassungsraute links vor der Visierkonsole, leuchtet bei Bereitschaft |
| Negativraum | Spannweite unter dem Rumpf zwischen Magazin und Pylon; Kolbenbogen zwischen Griff und Kolbenbein; J-Kammerbahn links | Schulterbucht unter dem Abgasrohr zwischen Kielhacke und Sattel; Sattelbogen über der Schulter; Ladeschacht unter der Klappe |
| Front | Mündungsbremse mit zwei Kammern und Krone → freier kannelierter Lauf → Laufbuchse → Stirnplatte in Raute → Pylon darunter | Tropfenstirn: eloxierte Stirnplatte → blanker Bohrungsring → dunkles Futterrohr; darunter das Fenster des Entfernungsmessers; Rückansicht ebenfalls Tropfen |
| Kolben | Kolben aus dem Rumpf: Oberschale und Kiel laufen als ein Teil bis zur Schaftkappe, der Kolbenbogen öffnet ihn, das Kolbenbein steht auf einer Gummisohle; Schaftkappe im Rautenquerschnitt | Schultersattel aus dem Leitmotiv: ein kleiner Tropfenkiel unter dem Abgasrohr, oben offen und mit zwei Spannbändern gehalten, unten ein Bogen über der Schulter, Enden als Keil |
| Zweiton | Creme-Oberschale über Graphit-Kiel, Teilung an der Gürtelfuge vom Butt bis zur Stirn; Magazin Graphit | Creme-Rumpfschale über Graphit-Kiel; Abgasrohr, Sattel und Griff Graphit |
| Grafik, Schrift | Gratstreifen auf dem Gürtel beidseitig; „BASIC  EX-09“ rechts auf dem Gürtel | orange Wasserlinie auf beiden Kielflanken; „BASIC  EX-14“ rechts auf der Schale in Achshöhe |
| Bedienung (Orange) | Magazinhalter | Klappenknopf, Sicherung |
| Stützen, Befestigung (Runde 5) | Pylon und Kolbenbein enden in einer eloxierten Fußplatte (je zwei blanke Schrauben) und einer Gummisohle, die sich nach unten um 7 mm je Seite verbreitert und in der Draufsicht gerundet ist; keine Stifte | Visierkonsole aus Rumpfschale und Kiel: Wurzel in der Flanke, schräge Strebe unten, Kehle oben ins Deck, 60 mm lang; Schiene BRI-22 zwischen zwei eloxierten Klemmleisten mit vier blanken Schrauben, zwei Bolzen an der Wurzel |
| Stützhand | am Pylon (Griffpolster) | unter dem Bauch (Griffkiel). Kein Vordergriff wie BASIC-14: Der Bauch reicht bis u 16 hinab und ist selbst die Griffzone; ein hängender Griff bräche die Bauchlinie und wiederholte die Stützen von E09 |
| Familie | BGM-1, BMW-R, BMZ-15, Zielfernrohr Z3 „Lang“ auf zwei Schienen BRI-22, Visierhöhe 66 mm, Kammerstängel links wie BASIC-09 | BGM-1, W2 „Entfernung“ mit `side_mount` 66 mm links auf Achshöhe auf BRI-22, Ladeschacht oben, hülsenlose Rakete wie BASIC-14 |

Gleich wie der BASIC-Typ bleiben Baugruppen, Anker, Weltpunkte und Aktionen (`fire_cycle`/`reload_empty` bzw. `fire`/`reload`). Der
Werfer behält das Funktionsprinzip von BASIC-14: Die Rakete wird von oben in den Schacht gesenkt, die Klappe schwenkt nach rechts. Die
Stützhand liegt unter dem Bauch statt an einem Vordergriff. Die Rohrwand bleibt in Achshöhe vor dem Auge höchstens 46 mm links der
Achse, wie bei BASIC-14 also 20 mm neben der Visierlinie.

### Nachbesserung

Belege: `~/Library/Caches/CubeEscapeFormgen2/0.25/belege/e09/r1–r5` und `…/e14/r1–r6`, je mit sieben Ansichten, Clay, Explosion und
Kontaktbogen; e09/r4–r5 und e14/r4–r6 (r5 nach Richter R1, e09/r5 und e14/r6 nach der Sichtung) als AAA-Lauf (1600 px, 96 Samples) mit `vergleich_BA09.png` bzw. `vergleich_BA14.png` (Piloten im selben AAA-Weg unter `e09/BA09`, `e14/BA14`).

| Typ | Runde | gesehen | geändert |
|---|---|---|---|
| E09 | r1 → r2 | Der Kolben ist eine große Graphit-Keilplatte vom Wangenkamm bis zur Spitze (von der Seite ein Klotz); das Deck liest sich als langer glatter Balken | Kolbenbogen: Der Kiel steigt hinter dem Griff zu einem Bogen (u 64) und fällt ins Kolbenbein mit dem Einbein; der Kolben spannt wie der Rumpf zwischen zwei Stützen; eloxierte Deckleiste mit vier Schrauben |
| E09 | r2 → r3 | Creme-Magazin unter dem Graphit-Kiel bricht den Zweiton; Zweibeinholme kaum zu sehen | Magazin Graphit (Creme nur über der Gratlinie); Holme Ø 6,4, Füße Ø 11 |
| E09 | r3 → r4 | (Test) Stirnplatte als Rechteck-Querschnitt | Stirnplatte in der Raute des Rumpfs |
| E14 | r1 → r2 | Das Kielheck über dem Griff endet als senkrechte Kastenfläche; die Rumpfschale endet hinten mit einer flachen Scheibe; der Sattel wirkt wie ein angesetzter Block | Kielhacke: Das Heck läuft als S-Kurve in die Unterseite des Abgasrohrs; Kegel 84 mm statt 48 mm; Bauch 6 mm tiefer; Sattelenden als Keil |
| E14 | r2 → r3 | Das Messfenster sitzt in der Bohrung (u 112–126 bei Bohrung ab u 112); der Sattel umschließt das Rohr ganz und wirkt wie eine Muffe | Fenster unter die Bohrung (u 90–101), Kiel vorn tiefer; Sattel als Wiege unter dem Rohr, oben offen, mit zwei eloxierten Spannbändern |
| E14 | r3 → r4 | (Test) Rakete ragt 4 mm über den Schacht hinaus (f 84–240 gegen 80–236); Schrift 0,7 mm vor der gewölbten Schale; Tropfenflanken unter u −9 gekreuzt | Rakete f 84–232; Schrift in Achshöhe; Kielspitze u 8 |
| E14 | r4 → r5 | (Richter R1) Leuchtfläche der Raute auf dem Muldenboden, verdeckt | Raute auf Achshöhe, Mulde unter der engsten Schalenstelle, Freilagetest |
| E09 | r4 → r5 | (Nutzer nach der Sichtung) „die zwei dünnen Pinner vorne und den Pinn am Schaft verstehe ich nicht“: Zweibeinholme Ø 6 und Einbein Ø 11 lesen sich als Fremdkörper und sind auf Spielabstand zu zart | Stifte, Riegel und Stellring entfernt; Pylon und Kolbenbein enden in Fußplatte und Gummisohle im Rautenquerschnitt, die sich zur Auflage verbreitert. Das Stativ trägt ohne Stifte: Rumpf auf Magazin, Pylon und Kolbenbein. Entscheidung gegen ein sichtbares Klappzweibein: Holme mit Gelenk unter dem Pylon füllten die Spannweite, den Negativraum des Leitmotivs |
| E14 | r5 → r6 | (Nutzer) „Am Raketenwerfer muss das Visier noch ‚richtig‘ befestigt werden“: dünner eloxierter Winkel neben dem Rohr, wirkt nicht befestigt | Visierkonsole aus Schale und Kiel (Wurzel 42 mm in der Flanke, schräge Strebe, Kehle ins Deck, 60 mm lang), Schiene über die ganze Länge zwischen zwei Klemmleisten mit vier blanken Schrauben, zwei Bolzen an der Wurzel; Prüfung des Zusammenhangs und des Mindestquerschnitts |

### Motivzeilen (für die Familie)

| Typ | Leitmotiv | Silhouette | Querschnitt | Blickfang | Negativraum | Front |
|---|---|---|---|---|---|---|
| EA09 Scharfschützengewehr „Theodolite“ | Stativ: Rautenrumpf auf drei Stützen (Magazin, Pylon und Kolbenbein auf Gummisohlen) | lang 1,18 m, gerade Decklinie mit Wangenkamm, unten drei Stützen mit offenen Feldern | Raute mit senkrechtem Gürtel (Creme oben, Graphit unten) | Libelle (Röhrchen mit Blase) links | Spannweite unter dem Rumpf, Kolbenbogen, J-Kammerbahn | Zweikammerbremse → freier Lauf → Laufbuchse → Rautenstirn mit Pylon; Kolben: Kolbenbein mit Gummisohle |
| EA14 Raketenwerfer „Keelson“ | Rumpf: Startrohr als Deck auf tiefem Kiel | 0,92 m, gerade Decklinie über flachem Bauch, Kielhacke, Abgasrohr mit Sattel | Tropfen (Kreis um die Bohrung, Flanken zum Kiel) | Zielerfassungsraute links | Schulterbucht, Sattelbogen, Ladeschacht | Tropfenstirn mit Bohrungsring und Messfenster darunter; Kolben: Schultersattel als kleiner Kiel |

### Prüfung

`tests/test_extended_schulter.py` prüft beide Modelle (25 Tests). Abgedeckt sind:

- Felder, Typ und Feuerart wie BASIC-NN, Blatt-IDs, Anker, Weltpunkte und Aktionen (`variant.problems` als Orakel).
- Familienschnittstellen und Budgets: genau ein Blickfang links, höchstens drei Akzent-Bedienfunktionen, eine Schrift, ein Grafikelement.
- Visierlinie: Z3 66 ± 4 mm über der Achse; W2 auf Achshöhe 66 ± 4 mm links. Vor dem Auge ragt in Achshöhe nichts näher als 20 mm an die Visierlinie.
- Die Schrift liegt auf der ebenen Fläche (Gürtel bzw. fast senkrechte Schale).
- Seiten-IoU < 0,85 gegen BASIC-NN und jedes andere EXTENDED-Modell und < 0,70 im Paar, im Standardmaß und im genauen Maß. Das genaue Maß
  rechnet ein Querprofil als Seitenprofil mit seinen Seitenschnitten; das Standardmaß zeichnet es als volles Rechteck und sieht weder
  Spannweite noch Kolbenbogen.
- Stativ: Pylon ≥ 40 mm unter der Spannweite, Kolbenfuß ≥ 60 mm unter dem Kolbenbogen, Spannweite und Kolbenbogen in der Silhouette leer;
  seit Runde 5 Gummisohlen ≥ 8 mm stark und unten ≥ 10 mm breiter, kein dünner Stift unter dem Rumpf (Gegenprobe: Einbein der Runden 1–4).
- Visierkonsole (Runde 5): Wurzel ≥ 30 mm in der Flanke, Querschnitt ≥ 1200 mm², Spitze ≥ 12 mm hoch, trägt die Schiene auf ganzer Länge,
  Klemmleisten mit blanken Schrauben, hängt mit Schale, Kiel und Visier zusammen (Gegenproben: dünner Winkel der Runden 1–4, stumpf angesetzte Konsole).
- Raute mit Gürtel, ein Teil vom Butt bis zur Stirn, kein angesetzter Kolbenkörper; Libelle mit sichtbarer Blase in der Mitte.
- Rumpf: Tropfen oben rund, Kiel unten schmal, Bauch ≥ 60 mm unter dem Rohr, Stirn und Kielhacke höher.
- Sattel als Wiege mit Bogen ≥ 15 mm hinter dem Auge; Rakete passt durch den Schacht.
- Blickfang frei (Richter R1): Leuchte vor dem Muldenboden, Glas davor, Rahmen unter der engsten Stelle der gewölbten Schale.
- Gestaltete Querschnitte, Detaildichte mindestens wie der Pilot, keine Selbstschnitte, Absetzung Gewehr/Werfer, Zusammenhang, Länge und Quellhash.

Eine Testzuordnung (`test_map.json`) führt dieses Repo nicht; `./check` findet die Datei über `unittest discover`.

Jede Regelprüfung hat eine Gegenprobe mit erwartetem Grund (z. B. durchgehender Vorderschaft, Keilkolben wie r1, Kasten statt Raute,
Blase am Rand, flacher Bauch, Kastenkiel, Muffe statt Wiege, Startrohr Ø 112 vor dem Visier, kürzerer Schacht). Die Tests fanden in r3
drei Fehler, die im Bild nicht auffielen: die Rakete länger als den Schacht, die Schrift vor der gewölbten Schale und die gekreuzten
Tropfenflanken unter dem abgeschnittenen Kiel.
