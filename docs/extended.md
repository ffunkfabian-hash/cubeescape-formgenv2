# EXTENDED-Modelle

Seit 0.15 „Spearhead“. Ein EXTENDED-Modell ist eine eigenständige Waffe der BASIC-Familie: eigene Silhouette, eigene Proportionen
und eigene Formarchitektur, gebaut im Vokabular des BALLON-Kits. Es ist kein Generatorlauf über einer BASIC-Grundform und kein
Umbau eines Piloten. Aus `basic.common` kommen nur die genormten Familienschnittstellen: Griffmodul BGM-1, Holovisier H0 auf der
Schiene BRI-22, Feuerwahlhebel und Ladehebel-Form, Schraubenköpfe sowie die Hilfen `rot`, `cut_box` und `mirror`.

| Kurzname | ID | Blatt-ID | Modul | Typ |
|---|---|---|---|---|
| `e01` | EXTENDED-01 „Spearhead“ | `EA01` | `formgen/models/extended/e01_spearhead.py` | Automatikgewehr |
| `e04` | EXTENDED-04 „Sledge“ | `EA04` | `formgen/models/extended/e04_sledge.py` | Handfeuerwaffe (Handkanone) |
| `e05` | EXTENDED-05 „Duplex“ | `EA05` | `formgen/models/extended/e05_duplex.py` | Pistole (Seitenwaffe) |

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
