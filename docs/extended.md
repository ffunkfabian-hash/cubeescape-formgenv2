# EXTENDED-Modelle

Seit 0.15 „Spearhead“. Ein EXTENDED-Modell ist eine eigenständige Waffe der BASIC-Familie: eigene Silhouette, eigene Proportionen
und eigene Formarchitektur, gebaut im Vokabular des BALLON-Kits. Es ist kein Generatorlauf über einer BASIC-Grundform und kein
Umbau eines Piloten. Aus `basic.common` kommen nur die genormten Familienschnittstellen: Griffmodul BGM-1, Holovisier H0 auf der
Schiene BRI-22, Feuerwahlhebel und Ladehebel-Form, Schraubenköpfe sowie die Hilfen `rot`, `cut_box` und `mirror`.

| Kurzname | ID | Blatt-ID | Modul | Typ |
|---|---|---|---|---|
| `e01` | EXTENDED-01 „Spearhead“ | `EA01` | `formgen/models/extended/e01_spearhead.py` | Automatikgewehr |
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
Die e01-Ansichten und -Stempel bleiben unverändert.

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
