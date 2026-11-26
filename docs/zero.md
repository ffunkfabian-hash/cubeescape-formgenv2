# ZERO-Reihe

Seit 0.46 „Zero“. Ein ZERO-Modell ist wie ein EXTENDED-Modell eine eigenständige Waffe der BASIC-Familie, gebaut im Vokabular des
BALLON-Kits (Modellsprache wie [EXTENDED](extended.md)). Auftrag: die gestalterische Eigenart von Formgen v1 mit der Modellierung und
Detailtiefe von Formgen v2 verbinden. Gleiche Familie, neue Form. Referenzen sind nur BASIC-01, EXTENDED-01, Formgen v1 (Archiv, nur
gelesen) und Formgen v2. Das Modell ist ein reines Spiel-Asset für Cube Escape und kein realer Nachbau; „Funktion“ heißt Lesbarkeit im
Spiel.

| Kurzname | ID | Blatt-ID | Modul | Typ |
|---|---|---|---|---|
| `z01` | ZERO-01 „Crosshair“ | `ZA01` | `formgen/models/zero/z01_crosshair.py` | Automatikgewehr |

IDs sind ewig. Die Blatt-ID folgt dem Schema `Z<Linie><NN>` analog zu `EA01`: Linie A ist die Grundform. Das Muster
`extended.SHEET_PATTERN` nimmt seit 0.46 die Reihen E und Z an; die Kollisionsprüfung gegen Waffen-, Roboter- und EXTENDED-Blätter gilt
weiter. Ein Linienregister, einen Blattweg über `formgen.pipeline` und die Website-Aufnahme hat ZERO noch nicht.

## Werkzeuge

- `formgen/extended.py` lädt auch ZERO: `PACKAGES` ordnet einem Kurznamen das Unterpaket unter `formgen/models` zu (`z01` → `zero`, sonst
  `extended`). Die Quellhashes der EA-Modelle bleiben bytegleich (Schlüssel `formgen/models/extended/<datei>`).
- `tools/extended_render.py z01` rendert die Grundform. Bis 0.46 bildete `subject()` die Blatt-ID über das EXTENDED-Linienregister; für
  `z01` wurde daraus still `EA01`, und Blender baute EXTENDED-01 unter dem Titel ZERO-01. Jetzt rendert ein Modell ohne Linienregister seine
  Grundform; `--line` mit einer anderen Linie als A bricht für ZERO ab (`tests/test_zero.py` › `TestRenderSubject`).

```bash
W=$PWD; ./ce lock gpu -- $W/.venv/bin/python $W/tools/extended_render.py z01 --tag r2 --res 1600 --gpu --extra
```

## ZERO-01 „Crosshair“

### Quellen

- **BASIC-01 (Pilot v2.1):** Zweiton Creme über Graphit, Paneele in Mulden, Deckplatte mit Munitionsanzeige, Chevronband, Holovisier auf
  BRI-22, Griff BGM-1, Magazin BMW-R, Achtkant-Kompensator. Übernommen werden nur genormte Schnittstellen aus `basic.common`.
- **EXTENDED-01 „Spearhead“:** Aufbau eines eigenständigen Moduls (Herkunft je Zahl, Tests, Renderweg), gerades 10°-Magazin mit Fenster.
  Gesperrt sind die Motive aus der [Motivtabelle](design-kanon.md#4-motivtabelle): Speerspitze, Draufsicht-Verjüngung, Fuller-Schlitz,
  Sechseck-Kern und Fachwerkschaft mit Puffer.
- **Formgen v1:** v1 wird eigenständig über Schaftformen (Keil, Daumenloch, Dreieck), Motive am Lauf (Dreizack, Nadel zwischen Schienen,
  Würfelkäfig) und Anordnungsideen (Bullpup, Quermagazin). Aus Black Ice KJ02 „Frostbite“ kommt der Keilschaft als Haltung, aus der
  Werkstatt-Serie H die sichtbare Konstruktion, aus Nadel KF08 der frei liegende Lauf zwischen Trägern. Kopiert wird nichts; v1 bleibt Archiv.
- **Formgen v2:** Modellsprache, [Design-Kanon](design-kanon.md) (Bänder, Klarheit, „Nie wieder“), Rasterskizze und AAA-Weg.

### Formideen

Es entstanden zehn Seitenskizzen mit Griff, Magazin und Visier der Familie, gerendert mit dem CPU-Raster (`extended_lines.author` →
`raster.render`, kein Blender). Die Spalte IoU ist die Seiten-IoU des Kanons (`kanon._side_iou`, gemeinsamer Ursprung am Griff). Der Bogen
liegt unter `~/Library/Caches/CubeEscapeFormgen2/0.46/belege/skizzen/skizzen_v1.png`.

| Idee | Architektur | IoU BA01 | IoU EA01 | Urteil |
|---|---|---|---|---|
| A Versatz | Creme-Rumpf vorn lang, Graphit-Schaft hinten tief, Z-Versatz | 0,78 | 0,83 | ruhig, aber vorn ein Block; Hülle wie EA01 |
| B Wiege | Lauf offen in einer Graphit-Wiege, Creme-Keil hinten | 0,79 | 0,81 | fällt nach vorn wie EA01 |
| C Bug | tiefer Keil-Vorderschaft, Dreieckschaft | 0,78 | 0,84 | Dreieckschaft = Fachwerk von EA01 |
| D Nullring | Ringschaft „0“ | 0,77 | 0,86 | starke Rückansicht, über der Kanon-Grenze 0,85 |
| E Joch | hoher Mittelpfeiler, schlanke Arme | 0,71 | 0,74 | eigen, aber ein Kasten mit Stäben |
| F Nullrahmen | Fenster im Gehäuse zeigt Kammer und Verschluss | 0,80 | 0,88 | Innenleben gut, Silhouette wie EA01 |
| G Versatz 2 | Kragnase über offenem Lauf | 0,79 | 0,82 | wie BASIC-01-Haube |
| H Pfeiler | Trapezgehäuse, Arme | 0,73 | 0,78 | eigen, Gehäuse leer |
| **I Fadenkreuz** | E + F: hoher, quer offener Rahmen, Achse und Zuführsäule als Fadenkreuz | 0,75 | 0,79 | **gewählt** |
| J Fadenkreuz | wie I mit Balkenschaft | 0,69 | 0,71 | Schaft zu dünn; L-Schaft im Modell |

Gewählt wurde I (Endstand r4: Seiten-IoU 0,75 gegen BA01, 0,77 gegen EA01; mit `extended.side_iou` 0,66 und 0,68). Die Idee hat eine einzige Geste, und die kommt aus der Funktion: Das offene Gehäuse zeigt Verschluss, Kammer und Zuführung
und ist zugleich die Auswurföffnung. Ihre Silhouette (Arm, Rahmen, Arm) setzt sich als einzige von allen Familien-Langwaffen ab, und
„nullen“ (einschießen) gibt dem Fadenkreuz im Rahmen einen Sinn. Aus D kommt die „0“, aus E die Massenverteilung, aus F das sichtbare
Innenleben. Der Keilschaft der Skizze I bildete mit seinem Durchbruch den Fachwerkschaft von EA01 nach. Er wurde deshalb zum geschlossenen
L-Schaft mit Keilbalken (Runde 2), seit Runde 4 zweiteilig mit Graphit-Fersenkeil.

### Formsprache

Die Herkunft jeder Zahl steht im Docstring und in den Kommentaren des Moduls.

- **Leitmerkmal Nullrahmen:** Das Gehäuse ist ein liegender Achteckrahmen, 312 × 104 mm groß und 62 mm breit, mit einer Öffnung von
  244 × 68 mm, die quer ganz durchgeht. Die Laufachse läuft durch beide Pfosten. Hinten liegt der Verschluss in der Führungsbuchse, vorn die
  leuchtende Kammer. Die Zuführsäule steigt aus dem Magazinschacht, ein Steg hängt die Kammerschelle am Bügel. Säule, Schelle und Steg
  stehen auf f 102, in der Mitte der Öffnung über dem Magazin, und bilden mit der Achse ein Fadenkreuz am hinteren Kammerende, also an
  der Zuführstelle. Säule und Steg sind blank (Rolle `metal`), damit das Kreuz auch in der Schrägsicht liest.
- **Silhouette Arm – Rahmen – Arm:** Der Rahmen ist die einzige Masse. Davor liegt ein schlanker Handschutz (58 mm hoch, 42 breit),
  dahinter ein L-Schaft aus Creme-Keilbalken (42–46 mm, 36 breit) über einem Graphit-Fersenkeil. In der Draufsicht und von vorn steht
  der Rahmen 10–13 mm je Seite über die Arme, seine senkrechten Ecken sind 45° gefast.
- **45° als Wiederholung:** Fasen am Rahmen außen (22) und an der Öffnung (16), die Haubenstufe, die Haubennase, die Innenfase des Schafts
  und die Kanteneinzüge im Querschnitt verwenden alle denselben Winkel. Die Klarheit liegt bei Achsen 0,77 und Richtungen 0,94.
- **Querschnitte:** Rahmenbügel, Haube (vor und hinter der Stufe), Schaft und Kappenfuß haben 45°-Einzüge (4–6 mm). Die Unterteile sind je
  Seite 1 mm schmaler als die Oberteile.
- **Zweiton:** Creme oben (Rahmenbügel, Haube, Schaft, Magazin) über Graphit unten (Rahmenwanne, Handschutz). Die Fuge liegt in den Pfosten
  (u 90) und am Handschutz (u 104).
- **Blickfang (genau einer):** die Kammer, ein Leuchtrohr unter Glas zwischen Kammerschelle und vorderer Kappe, von beiden Seiten durch den
  Rahmen sichtbar. Die Munitionsanzeige liegt oben zum Auge. Mit dem Visieremitter sind es 3 Leuchtfunktionen.
- **Schichten:** Deckplatte und Kammerdeckel stehen 2,5–3 mm über dem Bügel, die Haubenstufe 2,5 mm. Die Schaftleiste trägt 0,8 mm auf,
  Wannenpaneele und Kühlleisten liegen in Mulden. Die Rahmenkante besteht aus acht blanken Leisten.
- **Grafik und Schrift:** ein Chevronpaar an der Haubenwurzel, nach vorn zeigend. Die Schrift „BASIC  ZR-01“ steht rechts auf der ebenen
  Haubenflanke zwischen Chevrons und Stufe.
- **Front mehrstufig:** Haubennase mit Fase → blanke Laufbuchse → freier, kannelierter Lauf → Achtkant-Kompensator mit Seitenfenstern →
  blanke Krone. Dahinter steht der Rahmen als zweite, größere Kontur.
- **Ergonomie:** Griff BGM-1 unter der Wanne (Socket_Hand 0/0), Stützhand am Handschutz vor dem Handstopp, Ladehebel links am Bügel,
  Magazinhalter und Feuerwahlhebel links an der Wanne. Akzent-Bedienfunktionen: Ladehebel, Magazinhalter, Feuerwahlhebel (3).
- **Gleich wie BASIC-01:** Laufachse u 106, Visierlinie 74 mm darüber, Schnittstellen BGM-1, BMW-R, BMZ-15 und BRI-22, Baugruppen,
  Aktionen `fire_auto` (der Verschluss läuft sichtbar im Rahmen) und `reload_empty`.

### Messzeile (Kanon, `kanon.measure_model`)

| Länge | Höhe | Breite | L/H | Füllgrad | Visierlinie | Teile | Formen | Rundkörper | Quader | Rollen | blanke Kanten | Achsen | Richtungen | Nachbar |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 886 | 271 | 69 | 3.3 | 0.31 | 74 | 71 | 173 | 0.34 | 0.08 | 14 | 13 | 0.77 | 0.94 | EA01 0,77 |

`kanon.outside` meldet nichts: Proportionen und Klarheit liegen im Band der Langwaffen. Die Formen (173) liegen über dem Bandmaximum 164;
der Kanon prüft die Detaildichte nur auf der blockigen Seite, eine Obergrenze gibt es nicht. Der Messblock des Kanons bleibt BASIC und EXTENDED vorbehalten.

### Prüfung

`tests/test_zero.py` prüft jede Regel mit einer Gegenprobe:

- Felder, IDs und Blatt-ID ZA01. Gegenproben: ZI01, ZO01, ZA1 und XA01 passen nicht ins Muster.
- Weltpunkte mit `basic.variant.problems` als Orakel.
- Schnittstellen und Zweiton.
- Budgets, Gegenprobe mit zwei Leuchtteilen zu viel.
- Visierlinie im Vertrag und im Familienband.
- Seiten-IoU unter 0,85 gegen BASIC-01 und alle neun EXTENDED-Langwaffen, als Kanon-Maß (`kanon._side_iou` am ausgewerteten Netz) und als Näherung `extended.side_iou`. Gegenproben: das Modell gegen sich selbst 1,0, eine Linie ohne Mündung bleibt über der Schwelle.
- Keine schwebenden Teile. Gegenprobe: ein versetzter Kammersteg bildet eine eigene Gruppe.
- Leitmotiv:
  - Die geschlossene Lücke im Rahmen misst mehr als 3000 mm², an der Silhouette gemessen und auf die Öffnung begrenzt, damit der
    Abzugsbügel nicht mitzählt. Gegenprobe: ohne Öffnungsschnitt 0.
  - Fadenkreuz: Säule, Schelle und Steg liegen auf einer Achse und verbinden Wanne und Bügel. Gegenprobe: ein gekürzter Steg.
- Verschlussweg im Rahmen, Gegenprobe 160 mm Hub.
- Magazin vor dem Bügel.
- Gestaltete Querschnitte, Gegenprobe Einzug unter R_MID.
- Keine Stifte, Gegenprobe Führungsstange Ø 8.
- Schrift auf der ebenen Flanke. Gegenproben: über den Chevrons, über der Stufe, über dem Einzug.
- Einfache Profile.
- Quellhash ohne BASIC-01-Pilot und ohne EA01.
- Messzeile im Band der Familie ohne ZA01. Gegenproben: zehn Platten sowie Ausreißer in Länge, Breite und Füllgrad.
- Renderwerkzeug baut z01 und nicht EA01.

### Renders

AAA mit BALLONs unverändertem `tools/blender_build.main` (Cycles, mittelgrau, ohne Bloom), Ausgabe außerhalb des Repos unter
`~/Library/Caches/CubeEscapeFormgen2/0.15/belege/z01/<tag>/`. Rasterstände liegen unter `…/0.46/belege/raster/`, die Bewegungsbelege
(`fire_auto`, `reload_empty`; BALLONs `blender_build --motion` mit dem Datensatz, `./ce evidence clip`, 480p, ≤ 8 s) unter
`…/0.46/belege/bewegung/z01_fire_auto.mp4` und `z01_reload_empty.mp4`, dazu `ZERO-01/schluesselbilder.png`.

| Runde | Befund | Änderung |
|---|---|---|
| r1 | Rahmen und Kammer tragen. Die Arme sind Bretter, der Schaft wirkt als Klotz. Die Kammer liegt halb hinter Schelle und Kappe. Der Rahmen steht in der Draufsicht kaum vor. | L-Schaft mit Keil und 45°-Innenfase, Haubenstufe 45°, Fadenkreuz an die Zuführstelle, Rahmen 54 mm, Kammerdeckel |
| r2 | Arme geformt, Kammer frei, Rahmen steht vor. Im Hero blickt man in die Öffnung auf einen leeren, hellen Wannenboden, der wie eine Schale wirkt. | Bodenblech (dunkel) mit Verschlussbahn und Auswurframpe |
| r3 | Innenleben liest sich als Mechanik; Familienvergleich mit BA01: gleiche Palette, Griff, Magazin, Visier und Kompensator, eigene Silhouette. Stilprüfung (Opus): Fadenkreuz nur seitlich lesbar und aus der Mitte, Schaft als Plattenkolben, Draufsicht eine Folge gleich breiter Rechtecke | Rahmen 40 mm vor (Kreuz mittig), Säule und Steg blank, Kammer 100 mm, Rahmen 62 mm mit 45°-Ecken, Schaft zweiteilig, Anzeige auf den Schaft |
| r4 | Endstand | – |

Zuvor im Raster: Dunkle Paneele an Schaft und Pfosten lasen sich als Löcher (Kanon › 6), eine dunkle Haubenstufe als Schlitz. Sie wurden
durch Creme-Schichten ersetzt oder entfernt.

## Grenzen

- ZERO hat kein Linienregister, keinen Blattweg (`formgen.pipeline`) und keine Website-Aufnahme.
- Der Kanon-Messblock und `extended_lines.KEYS` umfassen weiter nur BASIC und EXTENDED.
- [Stilprüfung](kanon-stilpruefung.md) durch ein zweites Modell (Opus, high): Runde 1 Nachbessern (Nr. 2, 4, 8), Runde 2 Freigabe. Offen
  mit Schwere niedrig: In der Schrägsicht von oben verdeckt der Bügel den Steg, das Kreuz liest sich dort als umgedrehtes „T“. Der Einzug
  des Schaftbalkens ist flach. Das Kammerglas wirft im Cycles-Bild einen hellen Schleier auf den Wannenboden. Front und Rücken bleiben nahe
  an EA01, und der Fersenkeil verschwindet hinten im Graphit.
- Die Sichtung durch den Nutzer steht aus.
