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
