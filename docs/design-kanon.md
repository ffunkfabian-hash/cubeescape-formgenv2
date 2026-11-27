# Design-Kanon BASIC / EXTENDED (0.42 „Canon“)

Wozu: Ein anderes Modell oder eine neue Sitzung soll eine weitere Waffen-Generation im Stil der Familie entwerfen, ohne 1 500 Zeilen
Verlauf zu lesen. Dieser Kanon bündelt die Designsprache von BASIC (17 Typen aus BALLONs Kit, 12 Formlinien A–M) und EXTENDED (EA01–EA17,
12 Linien EB–EN). Er ist der Systemprompt der Entwurfssitzung; das Paket dazu baut `python -m formgen.kanon paket --out <Ordner>`.

Herkunft: Die Abschnitte 1–7 sind ein Destillat der Doku mit Fundstelle je Aussage (25.11.2026). Die Zahlen im Messblock misst
`formgen.kanon` an den Modellen selbst; `tests/test_kanon.py` meldet, wenn der Block veraltet. Der Kanon führt nichts Neues ein, er ordnet nur.

Fundstellen: X = docs/extended.md · AF = docs/auftrag-extended-familie.md · U = docs/uebergabe-0.15-spearhead.md · L = docs/LESSONS.md ·
G = docs/generator.md · M = docs/modellsprache.md · MP = docs/masterprompt.md · E = docs/ENTSCHEIDUNGEN.md · V0.nn = docs/versions/0.nn.md ·
VT = data/variants.toml · EL = data/extended_lines.toml · SK = skins.toml · AG = AGENTS.md · T_x = tests/test_extended_x.py (T_ = test_extended.py).
Zeilenangaben gelten für den Stand von 0.42; bei langen Absätzen zeigen sie auf den Anfang der Aussage.

## 1. Grundsätze

1. Eine Familie, je Typ ein eigener Charakter. Gemeinsam: Materialrollen, Zweiton, Paneele, Fugen, Schichtung, Radienstufen, Budgets. Je Typ
   neu: Silhouette, Gehäusearchitektur, Proportion, Querschnitt, Leitmotiv (AF:42–47, AF:19).
2. Silhouette zuerst: mindestens drei Formideen als Seitenskizze mit Griff, Visier und eingezeichneter Visierlinie; IoU gegen BASIC-NN und alle EA
   messen, dann wählen (AF:71–72, V0.23:38, V0.25:59).
3. Eine mutige Gesamtarchitektur, eine einzige starke Geste je Waffe (U:30, X:72, X:161, X:582).
4. Die Form entsteht aus der Funktion: Streuung wird Glocke, Bündelung Käfig, Munitionsmenge Rad, Schacht Vordergriff (X:282, X:285, X:383, X:388).
5. „Nicht beliebig, nicht übertrieben futuristisch“; geometrisch neu, kein BASIC-Umbau, keine angesetzten Zusatzteile (AF:12–13).
6. Schlicht zuerst, drei Detailebenen 60/30/10; hochwertige Hauptformen, harmonische Übergänge, Hard-Surface-Details (U:29, AF:14).
7. Lesbar im Spiel: genau ein Blickfang, mindestens eine Negativraum-Zone, mehrstufige Front, Akzente kameranah (Visier, Verschluss, linke
   Seite) (AF:44–45).
8. Konstruktion vor Dekor: Konstruktion → Positionierung → Proportion → Verbindungen → Silhouette → Stil → Material → Dekor (MP:477–486). Keine
   schwebenden Teile, nicht „übermäßig viele einfache Quader“ (MP:40, MP:266).
9. Der Typ bleibt spielbar: Baugruppen, Anker, Weltpunkte, Aktionen und Feuerart wie BASIC-NN. Genormte Schnittstellen (BGM-1, BRI-22, BMZ-15,
   BMW-R, BEC-1, Visierbausteine) gelten als Familie, nicht als Umbau (AF:46–47, X:5–6, X:407).
10. Jede Zahl hat eine Herkunft (V Vorgabe / G gemessen / A Annahme), dazu ein Docstring mit Formsprache-Checkliste (AF:57–58, U:62–63, AG:42).

## 2. Silhouette und Proportion

Qualitativ:
- Seite, Draufsicht und Front geben je ein eigenes Bild (X:209); Front- und Rückansicht gehören in jede Runde (L:38).
- Faustwaffen trennt erst die Lage der Laufachse über dem Griff (X:243, V0.18:24–25).
- Volumen dorthin, wo es die Sicht nicht stört, beim Werfer unter die Achse (X:579–582).
- Teilung eher 70:30, nie 50:50 (AF:42, X:226); bewusste Ausnahme EA04 „dunkles Fahrgestell mit zwei hellen Massen“ (X:226).
- Eigene Körper stehen deutlich heraus: Trommel Ø 92 statt Ø 80 bei 88 mm Gehäuse (V0.19:30–31).
- Paare gezielt gegeneinander setzen: kurz/lang, rund/kantig, Winkel/Kreis (X:270, X:315, X:390).
- Kompakte Waffe: Heck nicht so hoch wie die Front (X:419).

Vorgaben:
- Visierlinie 60–80 mm über der Laufachse (X:106, G:180); Kimme/Korn ≤ 4 mm anders als BASIC-08 (X:540); Z3/H3 66 ± 4 mm (X:638, X:749);
  Pinvisier B1 69,5 mm über dem Pfeil (X:749).
- Sichtfreiheit: Seitenvisier – in Achshöhe vor dem Auge nichts näher als 20 mm an der Visierlinie (X:580, X:638); Spurgewehr – vor dem Visier
  nichts höher als 24 mm unter der Visierlinie (X:694).
- Funktionsteile mindestens Ø 12 mm; Ausnahmen Sehne, Pfeil, Visierbaustein (L:39, X:754–755). Sehne Ø ≥ 4, Mittelwicklung Ø ≥ 6,5 (X:754).
- Seiten-IoU < 0,85 gegen BASIC-NN und jedes EA gleicher Größenklasse (AF:64), im Paar < 0,70 (X:186).
- Budgets: 1 Blickfang, ≤ 3 Leuchtfunktionen, 1 Grafikband, 1 Schrift, ≤ 3 Orange-Bedienfunktionen (AF:44); BASIC-Linien max(3, Grundform) (G:177–179).
- Fuge 1 mm (`SEAM`), Schichtung 2–3 mm (AF:43); Radien R_BODY 5, R_MID 3, R_SMALL 1,5, R_FINE 0,8, R_SOFT 6,5 nur am Griff (U:40–41, AF:44).
- Dreiecke Ziel 20 k, Grenze 50 k (AF:45); EA15 begründet bei 30 436 (X:445–446).
- Gestalteter Querschnitt: Breite ändert sich über die Höhe, oder Fasen-/Einzugsschnitt mit Radius ≥ R_MID (X:546–547). Detaildichte:
  Einzelformen ≥ 90 % des Piloten, blanke Teile ≥ Pilot (T_streuung:581–590).
- Leitmotiv-Schwellen der Familie: T-Überstand ≥ 5, Trommel Ø ≥ 140, Mantelrippen ≥ 8 (X:440); Brillenspalt ≥ 10, Helmwölbung ≥ 40 (X:542–543);
  Sohle ≥ 8 dick und unten ≥ 10 breiter (X:644); Visierkonsole Wurzel ≥ 30, Querschnitt ≥ 1200 mm², Spitze ≥ 12 (X:645); Luft um die Spule ≥ 3
  (X:757); Wurfarme ≤ 15°, Spanne < 0,85 × BASIC-07 (X:753).
- Vielfalt der Linien: min IoU (Seite, oben) ≤ 0,98 (G:187, X:812); Serien ≤ 0,95, Serienpaar ≤ 0,97 (G:193–194); EXTENDED-Linienpaar ≤ 0,998 (X:813).
- Gesamtlänge ist keine Regel; die gemessenen Werte stehen im Messblock.

### Messblock (gemessen, `python -m formgen.kanon messen`)

Länge, Höhe, Breite: Hülle des Netzes ohne Booleans und Fasen. L/H: Streckung der Seite. Füllgrad: Anteil der Seitensilhouette an ihrem
Rechteck (klein = luftig, Fenster und Bügel; groß = geschlossener Block). Visierlinie aus dem Designvertrag (– = keine; 0 bei den
Schulterwaffen). Nachbar: Modell mit der größten Seiten-IoU in der ganzen Familie (gemeinsamer Ursprung am Griff). BASIC = Linie A (BALLON-Pilot).
Detaildichte (Patch kanon-detail): Teile und Formen aus `PARTS` (`multi` zählt jedes Element), Rundkörper und Quader als Anteil der Formen,
Zahl der Materialrollen, blanke Kanten (Rolle `trim`). Proportionen allein fangen Blockigkeit nicht: eine Waffe aus zehn Platten kann in
allen Proportionsbändern liegen. `python -m formgen.kanon zeile <Kurzname>` (oder `formgen.kanon.outside`) nennt jeden Wert außerhalb des
Bands der Klasse, die Detaildichte nur auf der blockigen Seite (zu wenig Teile, Formen, Rundkörper, Rollen, Kanten; zu viele Quader).
Klarheit (Patch kanon-klarheit, `kanon.clarity`): Kanten der Seitenprofile ab 8 mm, nach Länge gewichtet; Achsen = Anteil waagerecht oder
senkrecht (± 2°), Richtungen = Anteil der sechs häufigsten Richtungen in 5°-Klassen. Klar heißt: lange waagerechte Leitlinien (Oberkante,
Laufachse, Visierlinie), senkrechte Abschlüsse, wenige wiederkehrende Schrägen. Achsen zählen gegen das untere Quartil der Klasse, weil das
Minimum bewusste Schrägen setzen (EA01 Speerspitze, Bogen); so melden auch zehn Familienmodelle mit schrägem Leitmotiv (BA02, BA03, BA06,
EA01, EA02, EA06, EA07, EA12, EA14, EA16) – dort ist das Leitmotiv der Grund. Die HORIZON-Skizzen (0.43) lagen alle darunter
(Achsen 0,23–0,52, Richtungen 0,57–0,77).

Für die Klarheit zählen die Seitenprofilkanten ab 8 mm, auch in zusammengesetzten Teilen. Jede Kante erhält ihr Gewicht nach Länge.
**Achsen** misst den Anteil innerhalb von weniger als 2° zur Waagerechten oder Senkrechten. **Richtungen** misst den Anteil der sechs
häufigsten Richtungen in 5°-Gruppen. Die Untergrenze für Achsen ist das untere Quartil der Vergleichsklasse, bei Richtungen ihr Minimum.
Die Einzelmessung für VA01 läuft über `python -m formgen.kanon zeile VA01`. Eine neue Waffe verändert die BASIC-/EXTENDED-Referenz nicht.

<!-- kanon:messung:anfang -->
| Blatt | Name | Art | Länge mm | Höhe mm | Breite mm | L/H | Füllgrad | Visierlinie mm | Akzente | Hände | größte Rollen | Nachbar (Seiten-IoU) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BA01 | Formstudie 01 v2.1 | Automatikgewehr | 915 | 260 | 52 | 3.5 | 0.32 | 63 | 5 | rubber/graphite | shell 38% graphite 31% | EA01 0.83 |
| BA02 | Impuls v2.1 | Impulsgewehr | 816 | 255 | 51 | 3.2 | 0.35 | 64 | 4 | rubber/graphite | graphite 49% shell 31% | BA10 0.80 |
| BA03 | Fernblick v2.1 | Scout-Gewehr | 1023 | 259 | 47 | 3.9 | 0.26 | 65 | 4 | rubber/graphite | shell 37% graphite 34% | EA03 0.77 |
| BA04 | Trommel v2.1 | Handfeuerwaffe | 307 | 184 | 45 | 1.7 | 0.39 | 32 | 2 | rubber/rubber | shell 43% rubber 19% | EA04 0.82 |
| BA05 | Seitenwaffe v2.1 | Pistole | 239 | 190 | 34 | 1.3 | 0.39 | 29 | 3 | rubber/rubber | shell 39% rubber 25% | BA04 0.71 |
| BA06 | Kurzläufer v2.1 | Maschinenpistole | 547 | 291 | 47 | 1.9 | 0.29 | 65 | 4 | rubber/graphite | graphite 38% shell 35% | EA10 0.61 |
| BA07 | Sehnenzug v2.1 | Bogen | 733 | 1016 | 69 | 0.7 | 0.07 | 69.5 | 2 | rubber/string | shell 42% graphite 33% | EA07 0.26 |
| BA08 | Streuer v2.1 | Schrotflinte | 869 | 222 | 52 | 3.9 | 0.35 | 39 | 4 | rubber/graphite | shell 24% graphite 22% | EA08 0.66 |
| BA09 | Weitschuss v2.1 | Scharfschützengewehr | 1135 | 268 | 72 | 4.2 | 0.26 | 66 | 3 | rubber/graphite | shell 46% graphite 27% | BA03 0.68 |
| BA10 | Glutkern v2.1 | Fusionsgewehr | 701 | 254 | 47 | 2.8 | 0.35 | 66 | 2 | rubber/graphite | graphite 44% shell 25% | BA02 0.80 |
| BA11 | Schienenlicht v2.1 | Lineares Fusionsgewehr | 1098 | 256 | 50 | 4.3 | 0.31 | 66 | 3 | rubber/graphite | shell 38% graphite 35% | EA11 0.75 |
| BA12 | Leitstrahl v2.1 | Spurgewehr | 777 | 254 | 49 | 3.1 | 0.35 | 66 | 2 | rubber/rubber | shell 57% graphite 20% | BA02 0.79 |
| BA13 | Trommel v2.1 | Granatwerfer (Trommel) | 670 | 269 | 142 | 2.5 | 0.39 | 66 | 3 | rubber/graphite | graphite 38% shell 23% | EA13 0.71 |
| BA14 | Schulterrohr v2.1 | Raketenwerfer | 910 | 241 | 131 | 3.8 | 0.41 | 0 | 2 | rubber/graphite | graphite 52% shell 20% | EA01 0.60 |
| BA15 | Dauerlauf v2.1 | Maschinengewehr | 983 | 266 | 129 | 3.7 | 0.29 | 66 | 3 | rubber/graphite | shell 42% graphite 22% | BA02 0.69 |
| BA16 | Klingenlauf | Schwert | 1194 | 76 | 96 | 15.7 | 0.67 | – | 1 | graphite/graphite | dark_metal 46% metal 23% | EA16 0.40 |
| BA17 | Schildwacht | Glefe | 1424 | 152 | 53 | 9.4 | 0.32 | – | 0 | graphite/graphite | shell 40% graphite 26% | EA17 0.49 |
| EA01 | Spearhead | Automatikgewehr | 901 | 267 | 51 | 3.4 | 0.34 | 70 | 4 | rubber/graphite | shell 47% graphite 30% | BA01 0.83 |
| EA02 | Cadence | Impulsgewehr | 704 | 255 | 51 | 2.8 | 0.39 | 64 | 4 | rubber/graphite | shell 46% graphite 32% | BA02 0.66 |
| EA03 | Meridian | Scout-Gewehr | 915 | 258 | 54 | 3.5 | 0.28 | 64 | 5 | rubber/graphite | shell 41% graphite 36% | BA03 0.77 |
| EA04 | Sledge | Handfeuerwaffe | 300 | 190 | 48 | 1.6 | 0.38 | 38 | 2 | rubber/rubber | graphite 29% shell 25% | BA04 0.82 |
| EA05 | Duplex | Pistole | 197 | 176 | 34 | 1.1 | 0.4 | 47 | 3 | rubber/rubber | rubber 32% shell 30% | BA05 0.66 |
| EA06 | Wishbone | Maschinenpistole | 415 | 281 | 54 | 1.5 | 0.34 | 72 | 4 | rubber/graphite | graphite 37% shell 33% | BA06 0.56 |
| EA07 | Caliper | Bogen | 711 | 796 | 75 | 0.9 | 0.11 | 69.5 | 2 | rubber/string | shell 44% graphite 26% | BA07 0.26 |
| EA08 | Brace | Schrotflinte | 788 | 222 | 75 | 3.5 | 0.31 | 39 | 5 | rubber/graphite | graphite 38% shell 23% | BA08 0.66 |
| EA09 | Theodolite | Scharfschützengewehr | 1177 | 264 | 70 | 4.5 | 0.44 | 66 | 3 | rubber/rubber | graphite 59% shell 26% | EA12 0.69 |
| EA10 | Bellmouth | Fusionsgewehr | 564 | 254 | 105 | 2.2 | 0.41 | 66 | 2 | rubber/graphite | graphite 37% shell 29% | BA10 0.74 |
| EA11 | Collimator | Lineares Fusionsgewehr | 1126 | 256 | 66 | 4.4 | 0.27 | 66 | 3 | rubber/graphite | shell 31% graphite 27% | BA11 0.75 |
| EA12 | Shuttle | Spurgewehr | 806 | 248 | 62 | 3.2 | 0.48 | 66 | 2 | rubber/rubber | shell 86% rubber 7% | EA09 0.69 |
| EA13 | Mantlet | Granatwerfer | 648 | 267 | 71 | 2.4 | 0.46 | 74 | 4 | rubber/graphite | shell 57% graphite 25% | BA13 0.71 |
| EA14 | Keelson | Raketenwerfer | 922 | 270 | 131 | 3.4 | 0.58 | 0 | 3 | rubber/rubber | graphite 66% shell 28% | EA09 0.55 |
| EA15 | Flywheel | Maschinengewehr | 978 | 294 | 80 | 3.3 | 0.36 | 74 | 4 | rubber/rubber | shell 50% graphite 31% | BA15 0.66 |
| EA16 | Sweepguard | Schwert | 1039 | 149 | 39 | 7.0 | 0.32 | – | 1 | rubber/shell | metal 37% shell 26% | BA16 0.40 |
| EA17 | Gorget | Glefe | 1595 | 181 | 56 | 8.8 | 0.26 | – | 2 | rubber/rubber | shell 32% graphite 23% | BA17 0.49 |

Detaildichte (Teile und Formen aus `PARTS`, `multi` je Element; Rundkörper und Quader als Anteil der Formen; blanke Kanten =
Teile mit Rolle `trim`; Achsen und Richtungen = Klarheit der Seitenprofile nach Kantenlänge, siehe `kanon.clarity`):

| Blatt | Teile | Formen | Rundkörper | Quader | Materialrollen | blanke Kanten | Achsen | Richtungen |
|---|---|---|---|---|---|---|---|---|
| BA01 | 72 | 158 | 0.33 | 0.1 | 14 | 13 | 0.67 | 0.83 |
| BA02 | 57 | 137 | 0.31 | 0.12 | 14 | 9 | 0.64 | 0.87 |
| BA03 | 58 | 85 | 0.52 | 0.14 | 14 | 9 | 0.66 | 0.85 |
| BA04 | 20 | 29 | 0.21 | 0.31 | 10 | 1 | 0.72 | 0.82 |
| BA05 | 25 | 33 | 0.15 | 0.39 | 11 | 1 | 0.66 | 0.9 |
| BA06 | 49 | 119 | 0.23 | 0.09 | 15 | 4 | 0.62 | 0.86 |
| BA07 | 41 | 47 | 0.38 | 0.15 | 11 | 6 | 0.28 | 0.61 |
| BA08 | 36 | 41 | 0.22 | 0.37 | 11 | 1 | 0.8 | 0.9 |
| BA09 | 47 | 54 | 0.39 | 0.15 | 12 | 5 | 0.83 | 0.9 |
| BA10 | 45 | 78 | 0.42 | 0.1 | 14 | 10 | 0.81 | 0.92 |
| BA11 | 53 | 82 | 0.52 | 0.13 | 14 | 9 | 0.86 | 0.92 |
| BA12 | 50 | 125 | 0.34 | 0.06 | 13 | 11 | 0.77 | 0.87 |
| BA13 | 56 | 141 | 0.43 | 0.07 | 15 | 9 | 0.74 | 0.9 |
| BA14 | 49 | 115 | 0.26 | 0.13 | 14 | 6 | 0.63 | 0.82 |
| BA15 | 73 | 164 | 0.35 | 0.15 | 14 | 15 | 0.85 | 0.94 |
| BA16 | 9 | 9 | 0.33 | 0.33 | 6 | 0 | 0.92 | 0.99 |
| BA17 | 13 | 13 | 0.31 | 0.23 | 5 | 0 | 0.51 | 0.9 |
| EA01 | 62 | 148 | 0.34 | 0.08 | 14 | 12 | 0.36 | 0.82 |
| EA02 | 57 | 126 | 0.26 | 0.06 | 15 | 10 | 0.61 | 0.95 |
| EA03 | 61 | 90 | 0.62 | 0.08 | 14 | 10 | 0.71 | 0.86 |
| EA04 | 29 | 45 | 0.38 | 0.2 | 12 | 4 | 0.66 | 0.82 |
| EA05 | 27 | 37 | 0.19 | 0.3 | 11 | 3 | 0.63 | 0.87 |
| EA06 | 51 | 123 | 0.26 | 0.06 | 16 | 7 | 0.61 | 0.94 |
| EA07 | 51 | 71 | 0.46 | 0.06 | 11 | 10 | 0.17 | 0.61 |
| EA08 | 46 | 88 | 0.45 | 0.2 | 12 | 7 | 0.74 | 0.89 |
| EA09 | 58 | 86 | 0.55 | 0.13 | 14 | 12 | 0.79 | 0.93 |
| EA10 | 52 | 84 | 0.51 | 0.1 | 14 | 12 | 0.79 | 0.9 |
| EA11 | 60 | 98 | 0.51 | 0.15 | 14 | 11 | 0.74 | 0.91 |
| EA12 | 48 | 130 | 0.38 | 0.03 | 12 | 12 | 0.46 | 0.67 |
| EA13 | 53 | 132 | 0.24 | 0.12 | 13 | 10 | 0.6 | 0.85 |
| EA14 | 55 | 153 | 0.33 | 0.1 | 13 | 9 | 0.36 | 0.75 |
| EA15 | 66 | 149 | 0.28 | 0.06 | 14 | 16 | 0.73 | 0.86 |
| EA16 | 20 | 39 | 0.49 | 0.03 | 10 | 5 | 0.25 | 0.87 |
| EA17 | 34 | 56 | 0.52 | 0.14 | 10 | 5 | 0.66 | 0.95 |

Bänder je Klasse über BASIC und EXTENDED (min / Median / max):

- **Langwaffe** (18): Länge mm 564 / 908 / 1177 · Höhe mm 222 / 256 / 294 · Breite mm 47 / 53 / 129 · L/H 2.2 / 3.5 / 4.5 · Füllgrad 0.26 / 0.345 / 0.48 · Visierlinie mm 39 / 66 / 74 · Akzente 2 / 3.5 / 5 · Teile 36 / 57 / 73 · Formen 41 / 94 / 164 · Rundkörper 0.22 / 0.385 / 0.62 · Quader 0.03 / 0.11 / 0.37 · Materialrollen 11 / 14 / 15 · blanke Kanten 1 / 10.5 / 16 · Achsen 0.36 / 0.74 / 0.86 · Richtungen 0.67 / 0.895 / 0.95 · Grenze Achsen (unteres Quartil) 0.66
- **Kompakt** (6): Länge mm 197 / 303.5 / 547 · Höhe mm 176 / 190 / 291 · Breite mm 34 / 46 / 54 · L/H 1.1 / 1.55 / 1.9 · Füllgrad 0.29 / 0.385 / 0.4 · Visierlinie mm 29 / 42.5 / 72 · Akzente 2 / 3 / 4 · Teile 20 / 28 / 51 · Formen 29 / 41 / 123 · Rundkörper 0.15 / 0.22 / 0.38 · Quader 0.06 / 0.25 / 0.39 · Materialrollen 10 / 11.5 / 16 · blanke Kanten 1 / 3.5 / 7 · Achsen 0.61 / 0.645 / 0.72 · Richtungen 0.82 / 0.865 / 0.94 · Grenze Achsen (unteres Quartil) 0.62
- **Werfer** (4): Länge mm 648 / 790 / 922 · Höhe mm 241 / 268 / 270 · Breite mm 71 / 131 / 142 · L/H 2.4 / 2.95 / 3.8 · Füllgrad 0.39 / 0.435 / 0.58 · Visierlinie mm 0 / 33 / 74 · Akzente 2 / 3 / 4 · Teile 49 / 54 / 56 · Formen 115 / 136.5 / 153 · Rundkörper 0.24 / 0.295 / 0.43 · Quader 0.07 / 0.11 / 0.13 · Materialrollen 13 / 13.5 / 15 · blanke Kanten 6 / 9 / 10 · Achsen 0.36 / 0.615 / 0.74 · Richtungen 0.75 / 0.835 / 0.9 · Grenze Achsen (unteres Quartil) 0.54
- **Bogen** (2, nur zwei Modelle: Spanne statt Band): Länge mm 711 / 722 / 733 · Höhe mm 796 / 906 / 1016 · Breite mm 69 / 72 / 75 · L/H 0.7 / 0.8 / 0.9 · Füllgrad 0.07 / 0.09 / 0.11 · Visierlinie mm 69.5 / 69.5 / 69.5 · Akzente 2 / 2 / 2 · Teile 41 / 46 / 51 · Formen 47 / 59 / 71 · Rundkörper 0.38 / 0.42 / 0.46 · Quader 0.06 / 0.105 / 0.15 · Materialrollen 11 / 11 / 11 · blanke Kanten 6 / 8 / 10 · Achsen 0.17 / 0.225 / 0.28 · Richtungen 0.61 / 0.61 / 0.61
- **Nahkampf** (4): Länge mm 1039 / 1309 / 1595 · Höhe mm 76 / 150.5 / 181 · Breite mm 39 / 54.5 / 96 · L/H 7 / 9.1 / 15.7 · Füllgrad 0.26 / 0.32 / 0.67 · Visierlinie mm – · Akzente 0 / 1 / 2 · Teile 9 / 16.5 / 34 · Formen 9 / 26 / 56 · Rundkörper 0.31 / 0.41 / 0.52 · Quader 0.03 / 0.185 / 0.33 · Materialrollen 5 / 8 / 10 · blanke Kanten 0 / 2.5 / 5 · Achsen 0.25 / 0.585 / 0.92 · Richtungen 0.87 / 0.925 / 0.99 · Grenze Achsen (unteres Quartil) 0.45
<!-- kanon:messung:ende -->

## 3. Formvokabular

Bausteine (Kit):
- Koordinaten in mm: f vorn, u oben, x links; Socket_Hand = (0, 0, 0) (M:19, U:35–36). Pflichtfelder META, ASSEMBLIES, PARTS, ANCHORS, POINTS,
  ACTIONS (U:44–46).
- `prof`: Seitenprofil (f, u) mit Breite w, Grundkörper der meisten Gehäuse (M:22, U:37). `plan`: Draufsicht (f, x) u0..u1, als Schneidkörper
  für die Draufsicht-Verjüngung (M:26, X:72–73); Laufrichtung einheitlich im Uhrzeigersinn über `cw()` (X:731, X:775–776).
- `xprof`: Querprofil (x, u) entlang f für Schrägen, Wülste, Raute, Tropfen, Oval; Löcher als `cuts` (M:36, U:38). Das Seitenmaß zeichnet es als
  volles Rechteck (L:36).
- `cyl`: axis, r, r1 = Kegel, r_in = hohl, segs – Läufe, Trommeln, Ringe, Kronen (M:25). Weitere: `box`, `xbox`, `frame`, `multi`, `tube`,
  `text`, `hull`, `loft`, `surface`, `prism2` (M:24–35).
- `cuts` = Boolesche Differenz; `bevel` = Fase als Rücksprung in mm, 2 Segmente, Winkelgrenze 30° (M:38, U:39–40). `mesh_plan`: beide
  Laufrichtungen schneiden, die frühere Lehre ist widerlegt (X:768–776, L:37).
- Familienbausteine: `grip_v21` (BGM-1), Visierbaukasten v3 (`reflex_sight_v21` …), `rifle_mag`, `selector`, `charging_handle`, `rail` (BRI-22),
  `screws`, `mirror`, `cut_box`, `rot`, `glow`, `side_mount` für Seitenschienen (U:42–44, G:90, L:19).

Formgriffe (je wofür):
- Fuller-Schlitz: quer ganz durch, zeigt Lauf und Kühlringe, Negativraum in einer Klinge (X:82, V0.15:24–25).
- Draufsicht-Verjüngung: Seitenprofil plus plan-Schnitt, damit Spitze oder Spindel auch von oben lesen (X:72–73, X:703).
- Chevrons / Grafikband: das einzige Grafikelement, zeigt die Richtung (X:89).
- Fenster mit Schacht: Leuchte hinter Glas im blanken Rahmen, Schacht durch die Schale (X:141, V0.17:26).
- Käfig: offene Stäbe zeigen den Kern (X:293, X:297). Speerspitze: fallende Ober-, steigende Unterlinie (X:80).
- Takt: Schlitze, Platten oder Kragen in Reihe (X:140, X:293, X:339); seit Welle 2 gesperrt (X:370).
- Schichtung: Deckplatte 2–3 mm über dem Körper, Paneele in Mulden, Unterteil je Seite 1 mm schmaler (X:87–88, X:142).
- Mehrstufige Front: Fase → Buchse → freier Lauf → Kompensator → blanke Krone (X:90–91, X:298, X:401).
- Negativraum aus der Funktion: Handraum im Korbbügel, Gabelzwickel, offene Nabe, Spannweite (X:343, X:400, X:593).
- Trichter aus zwei Kegeln (flacher Hals, steiler Mund) in Emitterfarbe (V0.19:29).
- Zweiton-Fuge folgt der Form, als Bogen statt Gerade (X:732, V0.28:53).
- Stufe als eigenes aufgesetztes Teil, nicht als xprof-Schnitt (V0.22:29–30); Rahmen an spitzen Ecken kappen (V0.22:27–28).
- Kolben setzt Rumpf oder Haube fort, ohne angesetzten Kern (X:488, X:595, X:647).
- Visier über Konsole oder Schlitten mit tragendem Querschnitt am Gehäuse (X:599, X:711, L:39).

Linien: BASIC A–M ändern Längen, Bausteine, Leuchten und Skin, J–M als Verkleidung über dem Piloten (G:196–197; Ideen VT:13–169). EXTENDED
EB–EN nur mit silhouettenerhaltenden Eingriffen (sight, mag, muzzle, muzzle_r, glow, drop, front, rear, limbs), ohne series, stock, grip
(X:790–792; Ideen EL:12–161).

## 4. Motivtabelle

„Nicht wiederholen“ = von diesem Modell belegt. Eine neue Generation wählt Leitmotive außerhalb dieser Spalte.

| EA | Name | Waffenart | Leitmotiv | nicht wiederholen | Fundstelle |
|---|---|---|---|---|---|
| 01 | Spearhead | Automatikgewehr | Speerspitze, Draufsicht 44 → 20 mm | Speerspitze, Draufsicht-Verjüngung, Fuller-Schlitz, Sechseck-Kern, Fachwerkschaft mit Puffer, Sechskant-Kompensator | AF:49–50, AF:90, X:80–91 |
| 02 | Cadence | Impulsgewehr | Bullpup-Monoblock als Parallelogramm, alles 15° | Parallelogramm, Trapez mit Schulterfasen, Taktschlitze, Bullpup | AF:91, X:137–139, X:237, X:386 |
| 03 | Meridian | Spähergewehr | koaxiale Rohrlinie | Rohrlinie, parallele Ober-/Unterlinie, Kreis mit Rillen | AF:92, X:166, X:556 |
| 04 | Sledge | Handkanone | Hammerkopf mit Prallkammer, schlanker Hals | Oberlinie hoch-tief-hoch, Doppel-T, offene Kehle | AF:93, X:223, X:238 |
| 05 | Duplex | Pistole | Doppeldeck: Schlitten über tiefem Laufrohr | Doppeldeck mit Schlitz, tiefe Laufachse | AF:94, X:256, X:382, X:569 |
| 06 | Wishbone | Maschinenpistole | Gabelbein Λ (Schacht 24° vor, Griff 15° zurück) | Λ, T-Querschnitt, Kiel unter dem Lauf | AF:95, X:430, X:465 |
| 07 | Caliper | Kampfbogen | Klammer ⊐: Deflex-Bügel, Wurfarme fast parallel | Klammer, Keilrippe, Halbmond-Spannlicht | AF:96, X:739 |
| 08 | Brace | Schrotflinte | Brille: zwei Läufe nebeneinander, Schiebemantel | Brille/Wülste, Zwillingsauge, Spaltkolben | AF:97, X:533 |
| 09 | Theodolite | Scharfschützengewehr | Stativ: Rautenrumpf auf drei Stützen | Stativ, Raute mit Gürtel, Libelle | AF:98, X:629 |
| 10 | Bellmouth | Fusionsgewehr | Glocke: Ladetrommel und Streutrichter | Trichter, Glocke, Streuscheibe, Glutring | AF:99, X:250, X:453–454 |
| 11 | Collimator | Lin. Fusionsgewehr | offener Stabkäfig mit Fokusplatten | Käfig, Quadrat, Plattentakt | AF:100, X:556, X:666 |
| 12 | Shuttle | Spurgewehr | Weberschiffchen: Spindel mit Auge und Spule | Spindel mit Auge, stehendes Oval, Bogenfuge | AF:101, X:740 |
| 13 | Mantlet | Granatwerfer | Panzerhaube mit Schirm | Helmhaube, Visiergasse, U-Querschnitt | AF:102, X:534, X:557 |
| 14 | Keelson | Raketenwerfer | Rumpf: Startrohr als Deck auf tiefem Kiel | Tropfen-Kiel, Schultersattel | AF:103, X:630, X:667 |
| 15 | Flywheel | Maschinengewehr | Schwungrad: Gurttrommel quer | Rad quer, Kreuz-Kühlmantel, offene Nabe | AF:104, X:431, X:666–667 |
| 16 | Sweepguard | Schwert | Säbelbogen mit Korbbügel | Säbelbogen, Handraum im Bügel | AF:105, X:339, X:466 |
| 17 | Gorget | Glefe | Ringkragen im Takt auf Rundschaft | Kragentakt, Laterne | AF:106, X:339 |

ZERO-Reihe (0.46, [ZERO](zero.md)): ZA01 „Crosshair“ (Automatikgewehr) belegt den Nullrahmen (quer offenes Rahmengehäuse), das Fadenkreuz
im Rahmen (Achse, Zuführsäule, Steg) und den L-Schaft mit Keilbalken und 45°-Innenfase. ZA02 „Facet“ (Automatikgewehr) belegt den
Sechskant-Facettenquerschnitt mit senkrechtem Mittelband, die Leuchtkante in der Facettenkante und den steigenden Keilschaft mit
waagerechtem Schlitz. ZA03 „Cascade“ (Impulsgewehr, 0.49) belegt die Staffel (Deck → Handschutz → Nase fallen in 45°-Stufen und
werden schmaler), die drei Leuchtnuten in Schaftfuge und Stufenflächen als Salvenanzeige und den bündigen Daumenloch-Schaft mit schräger Strebe.

Serie DaVinci (0.52, [DaVinci](davinci.md)): DA01 Linea belegt gerade Oberlinie Kolben → Stirn, Daumenlochschaft-Schleife, Vesica-Schlossplatte mit Oculus.

Ebenfalls gesperrt: Serien J–M als Leitmotiv (AF:50–51), Lamellen, die sich als Zähne lesen (X:284), v1 KF18 „Gabelkrone“ (X:333), Haube über
dem Rohr wie BASIC-12 (X:667). Offen: ähnliche Plattenschäfte EA03/EA11 (AF:111), orange Chevrons auf EA01/04/05 (AF:111).

## 5. Materialrollen und Skins

- Rollen: shell (Creme, lackiert, SK:3–7), graphite (Griffpolymer, SK:9–15), rubber (SK:103), anodized (Paneele, SK:118), trim (blanke Kanten und
  Schrauben, SK:111), accent (Orange, nur Bedienelemente, SK:29–33), energy (Leuchte, SK:35–40), metal und dark_metal (SK:17–27), glass (SK:42),
  string (SK:97), brass (SK:124), decal (SK:130), Visier- und Ladekern-Rollen sight_anod … draw_light (SK:178–214).
- Creme `shell` über `graphite` (AF:42); die Hand ist graphite oder rubber (G:175); trim-Schrauben nur an Panzern und Paneelen (AF:43); accent nur
  für Bedienung, Grafikteile zählen nicht (G:170, G:177); genau ein Blickfang links (X:436, X:637); Schrift rechts und dunkel auf Creme (X:252).
- Farben nur in `skins.toml` (M:15, AG:42); Bilder mittelgrau, ohne Bloom (AG:34).
- Rollenkontrast: Creme-Magazin unter Graphit-Kiel bricht den Zweiton (X:616); Creme-Hals liest sich als Stiel (X:218); langer eloxierter Hals
  zeigt Kratzsprenkel, deshalb Graphit (X:219).
- Skins ändern nur Farben, nie die Form (G:101). Finish = jeder Waffen-Skin auf jedes Blatt, ohne neue ID (X:818–819, E:65). Linienskins: die zwei
  größten Rollen ≥ ΔE 10; Leuchtrolle in allen Finishes ≥ ΔE 25 zur Schale (X:840–844, E:66).
- AAA: AgX und Key-Licht bleichen, Orange wird lachsfarben – Palette am Cycles-Bild abnehmen (L:20, G:168); ein Lackrot bleibt lachsfarben,
  deshalb Signalrot als `metal_shell` (X:831–832, SK:388–395); Farbe nur im Inneren der Rollenmaske messen (L:28).

## 6. Nie wieder (Fehler → Regel → Fundstelle)

- Kastig (Plattenkolben, Quader-Querschnitte, glatte Kästen) → gestaltete Querschnitte, Front und Rück jede Runde → L:38, V0.23:47–48, X:504–525, AF:110
- Weniger Detail als der Pilot → Detaildichte ≥ Pilot → V0.23:44–45, X:518
- Blockig aus wenigen extrudierten Platten in eigener Geometrie (Astra-Formstudie EXTENDED-01, 22.11.: rund zehn Umrisse, eine Fase für alle,
  eigene Palette) → nur Modellsprache und Familienbausteine, Detaildichte im Band der Klasse → Messblock › Detaildichte, `test_kanon`
- Unruhige Konturen aus frei gesetzten Punkten, jede Kante mit eigenem Winkel (HORIZON-Skizzen 0.43, Nutzer: „klare Formen … garnicht“)
  → Leitlinien, 5-mm-Raster, wenige wiederkehrende Schrägen, Klarheit im Band → Messblock › Klarheit, `test_kanon`
- Dekor statt Konstruktion: ein fremdes Modell nannte die Waffen von sich aus „Requisiten“ und formte nur Zierlagen (HORIZON Runde 1–2)
  → im Auftrag ausdrücklich: reine Spiel-Assets, kein realer Nachbau, „Funktion“ = Lesbarkeit im Spiel; Leitmotiv als Hauptvolumen
  (Runde 3: alle neun im Band, Achsen 0,79–0,90) → `paket/auftrag-astra-runde3.md` (außerhalb des Repos), LESSONS
- Stifte unter Ø 12 mm (Zweibeinholme, Einbein) → Leitmotiv über Volumen, Sohlen statt Stifte → V0.25:44–46, X:622, L:39
- Visier am dünnen Winkel, „nicht richtig befestigt“ → Konsole aus Schale und Kiel, Schiene liegt ganz auf → X:623, V0.25:45, L:39
- Magazin im Abzugsbügel (fiel im Render nicht auf) → Magazin vor dem Bügel, Test → X:513, V0.23:39–40
- Schrift über Fuge oder Chevrons, vor gewölbter Schale, hell auf Creme → Länge ≈ 0,62 × Größe × Zeichen gegen die ebene Fläche, dunkel → L:34, X:107, X:620, X:509, X:252
- Schwebende Teile; geschlossene Lücke nur am Zusammenhang geprüft → Kontaktbogen gezoomt, Lücken an der Silhouette prüfen → X:110, L:33, L:35, V0.20:25–27
- Geteilte Schnittkörper (Finne an EH12); Schrägmagazin geschert (EF06); Mündungskrone wandert allein → Teil einzeln kopieren, Magazin starr, Rohr-Regel → X:803–811, L:40, V0.38:29
- Formgleiche Linien (nur Farbe; Stauchen endet am freien Raum) → Vielfaltsmaß, Längen staffeln, paarweise messen → L:15, L:41, X:796–798, E:38
- Verkleidung überdeckt die eigene Silhouette → kein series/stock/grip an EA → X:791–792, E:64
- Schlitz liest sich als Streifen → quer ganz durch, Mechanik dahinter, ≥ 8 mm → V0.15:24–25, X:250
- Leuchte im Vollmaterial oder verdeckt → Schacht durch die Schale, Freilage prüfen → V0.17:26–27, X:621, V0.25:64–65
- Stufe als xprof-Schnitt (Schattierungsfehler); Rahmen über spitzer Ecke → eigenes Teil; kappen → X:420–421, V0.22:27–30
- Gerade Zweiton-Fuge macht aus einem gewölbten Körper einen Balken → Fuge folgt der Form → X:732, V0.28:53
- Selbstschneidendes Profil; doppelte Teil-ID (`sight_clamp`, Schelle hing frei) → einfache Profile, ID-Test → X:517, X:524, X:727, V0.28:54–55
- Bewegung kollidiert (Pumpenhub 4 mm in die Kragen); Klappe deckt das Auswurffenster → ganzen Weg prüfen, Schieber öffnet vor dem Auswurf → X:516, X:527, V0.23:41–42
- Rakete länger als der Schacht; Haube über der Visierlinie → Funktionsräume messen, Visierlinie schon in der Skizze → X:619–620, X:473–475, V0.23:37–38
- Teil liest sich als etwas Fremdes (Werkzeugstiel X:217, Kameraobjektiv X:514, Megafon V0.19:29, Zähne X:284, Klötze X:521, Schnabel X:512,
  Muffe X:618) → umformen, bis es die Funktion zeigt
- Dunkle Mulde wirkt wie Loch; lange dunkle Schiene deckt die Form → entfernen oder umformen; Schiene nur unter dem Visier → X:418, X:422–423, X:507–508, X:515
- Zu zart (dünne Holme, Facetten durch zu wenige Segmente); zu viele Dreiecke (34 876) → X:505, X:728–729, X:424, X:523
- Zweiton gebrochen; fremder Querschnitt (Rechteck-Stirn im Rautenrumpf) → X:616–617
- Motiv der Geschwistersitzung wiederholt → Motivtabelle vor dem Bau lesen → V0.18:26–27, X:250
- Hero-Kamera ohne Blickfang → Kamera von links → X:726, X:728
- Ursache ungeprüft als Lehre (`mesh_plan`) → erst gegenprüfen → L:37

## 7. Prüfungen, die das absichern

Jede Regelprüfung hat eine Gegenprobe, die aus dem erwarteten Grund rot wird (X:265–266, L:18). Eine neue Generation übernimmt diese Tests für
ihre Modelle:

- Budgets `test_budgets` (T_:103 mit Gegenprobe :110, je Sitzungsdatei); Visierlinie `test_sight_line` (T_:144 …); Sichtfreiheit
  T_schulter `test_launcher_view_clear`:286, T_sonder `test_trace_view_clear`:230 und `test_bow_sight_cone`:193, T_streuung
  `test_mantlet_sight_channel`:398.
- Eigene Silhouette `test_own_silhouette` (alle Dateien); Absetzung im Paar (T_gewehre `test_distinct`:403, T_fusion `test_scatter_versus_focus`:209,
  T_dauerfeuer `test_compact_versus_heavy`:348 …); schwebende Teile `test_no_floating_parts` (T_:162 und je Datei).
- Negativraum (T_nahkampf `test_negative_space`:243, T_dauerfeuer `test_wishbone_gap_closed`:278, T_fusion `test_cage_shows_core`:233 …);
  Schrift auf ebener Fläche (`test_lettering_on_flat_face`, T_ `test_lettering_on_receiver`:135); Blickfang frei (T_gewehre `test_window_bars_visible`:274,
  T_schulter `test_beacon_exposed`:241).
- Kastig: `test_shaped_sections` (T_streuung:536, T_schulter:551, T_sonder:461) und Querschnittstests je Modell; Detaildichte `test_detail_density`
  (T_streuung:580, T_schulter:570, T_sonder:474).
- Stifte: T_sonder `test_no_thin_sticks`:334; Visier befestigt: T_schulter `test_keelson_sight_console`:499, T_sonder `test_caliper_sight_sled`:344,
  `test_shuttle_rail_saddle`:450; Magazin vor dem Bügel: T_streuung `test_mantlet_box_magazine`:447; Kolben nicht angesetzt: T_streuung
  `test_brace_body_and_stock`:476.
- Profile und Laufrichtung `test_profiles_simple`, `test_plan_winding` (T_sonder:499); doppelte IDs T_sonder `test_fields_and_ids`:95; Bewegung
  T_streuung `test_brace_pump_and_eye`:356, `test_port_opens_before_eject`:617.
- Linien: `tests/test_extended_lines.py` (Vielfalt, Paare, Zusammenhalt, Schnittkörper, starres Magazin, Vertrag, Rollenkontrast) und
  `tests/test_variety.py` (BASIC).
- Detaildichte im Band der Klasse: `formgen.kanon.outside`, Gegenprobe zehn Platten `test_counterproof_ten_slabs_fall_below_the_band`.
- Klarheit: `formgen.kanon.clarity`, Gegenprobe wellige Kontur `test_counterproof_wavy_contours_fall_below_the_clarity_floor`.
- Nicht maschinell geprüft: „liest sich als …“ (Abschnitt 6) und die offene Kastigkeit in Front und Draufsicht (AF:110) – dafür die
  [Stilprüfung](kanon-stilpruefung.md) und die Sichtung durch den Nutzer.

## 8. Ablauf für eine neue Generation

0. **Kontext in den Auftrag:** reine Spiel-Assets, kein realer Nachbau; „Funktion“ heißt Lesbarkeit im Spiel (Abschnitt 6, Dekor statt Konstruktion).
1. **Vorher festlegen (Version mit Register):** Name der Generation, Blattpräfix und eigener Seed-Raum; IDs sind ewig. Wie stark sie sich
   abhebt (eigene Leitmotive, eigene Skins). Welches Modell entwirft: erlaubte Modelle nach den globalen Regeln (Opus `high` für Entwurf); nur
   das dort gesperrte `gpt-6-astra` braucht vorher eine Regeländerung in Nexogen.
2. **Je Waffe:** drei Konzeptzeilen (Rolle, Leitmotiv außerhalb der Motivtabelle, Silhouette) → mindestens drei Seitenskizzen mit Visierlinie →
   Nutzer wählt → Modul nach Muster (Paket) mit Herkunft je Zahl → Tests dieses Kanons → Messzeile samt Detaildichte und Klarheit im Band der Klasse oder begründet → Stilprüfung →
   Sichtung durch den Nutzer → AAA nur auf sein Wort.
3. **Paket:** `python -m formgen.kanon paket --out <Ordner> [--bilder <Übersicht>]` bündelt diesen Kanon, die Stilprüfung, `modellsprache.md`,
   `skins.toml`, beide Linienregister und acht Musterlösungen (`formgen.kanon.EXAMPLES`): EA01 (Muster mit voller Checkliste, AF:55–56), EA04
   (kürzestes Modul, Faustwaffe), EA07 (Sonderform, begründete Ausnahme der 12-mm-Regel), EA09 (Stativ nach Nutzerkorrektur), EA12 (Bogenfuge,
   `cw()`), EA13 (gestaltete Querschnitte nach 13 Runden), EA14 (Visierkonsole nach Nutzerkorrektur), EA16 (Nahkampf, Negativraum im Bügel).
   Die Auswahl folgt dem dokumentierten Stand; die Codequalität ist nicht gemessen.

## Grenzen

- Das BALLON-Stilhandbuch (§1–4) liegt außerhalb dieses Repos und wird hier nur zitiert (AF:40–45, U:29); das Leitmerkmal je BASIC-Typ
  (Stilhandbuch §1) ist hier nicht dokumentiert.
- `test_shaped_sections` nennt im Docstring ≥ 3 mm Breitenänderung, wertet aber erst unter 1,5 mm als Quader (T_streuung:537 gegen :554, ebenso
  T_schulter:561, T_sonder:468). Der Kanon nennt beide; geklärt wird das in den Tests, nicht hier.
- Die Fundstellen sind Zeilen; verschiebt eine spätere Doku-Änderung sie, bleibt der Abschnittsname der Anker.
