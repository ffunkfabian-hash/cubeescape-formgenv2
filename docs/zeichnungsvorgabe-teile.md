# Zeichnungsvorgabe R02-Einzelteile (Bildgenerator → Meshy → Blender)

Stand 27.10.2026. Optionaler Weg neben dem Standardbau: Kein Modul unter `formgen/` liest diese Bilder oder Netze.

## Schablonen

`python tools/r02_part_templates.py` (mit `.venv/bin/python`, braucht `rsvg-convert`) schreibt nach
`~/Library/Caches/CubeEscapeFormgen/refs-r02/part-templates/` je Teil `<teil>.svg`, `<teil>.png` (4000 × 4000 px, mit Unterlage),
`<teil>-ohne-unterlage.png`, dazu `contact.png` und `manifest.json`. Ohne `--force` werden nur geänderte PNGs neu gerendert.
Ein zweiter Lauf ist bytegleich. `--only kopf,arm` baut nur einzelne Teile.

| Teil | u (mm) | Gelenkmarken | Seite |
|---|---|---|---|
| `kopf` | 1760–2000 | Hals | Mitte |
| `oberkoerper` (Brust/Bauch) | 1265–1760 | Hals, Taille, Schultern | Mitte |
| `becken` mit Gürtel | 975–1265 | Taille, Hüften | Mitte |
| `schulterpolster` | 1470–1745 | Schulter | links |
| `arm` (Oberarm bis Unterarm) | 1036–1560 | Schulter, Ellbogen, Handgelenk | links |
| `hand` | 860–1036 | Handgelenk | links |
| `bein` (Oberschenkel bis Unterschenkel) | 169–1060 | Hüfte, Knie, Knöchel | links |
| `fuss` | 0–169 | Knöchel | links |

- **Ansichten:** Front (anatomisch links → Bild rechts), Seite von links (vorn → Bild links, wie Profil B), Rücken und
  Draufsicht (vorn = unten, unter der Front und in x fluchtend). Alle Ansichten eines Blatts haben einen gemeinsamen Maßstab.
  Es gibt zwei feste Klassen: **2 px/mm** für Oberkörper, Becken, Arm und Bein, **4 px/mm** für Kopf, Schulterpolster, Hand
  und Fuß (genau doppelt). So bleiben die Teile untereinander vergleichbar, und kleine Teile sind trotzdem groß genug.
  Breite Teile stehen im 2×2-Raster.
- **Gelb:** gemessene Rahmenkanten und die gestrichelte Kontur des Masterblatts. Die Front ist verbindlich, der Rücken-Rahmen ist die gespiegelte Front.
  **Orange gestrichelt:** Rahmenkante aus einer Annahme, weil die Fläche im Masterblatt verdeckt ist. Dazu gehören Rumpf- und
  Beckenrücken, die Vorderkanten von Arm und Polster, die Polster-Innenkante und die Handtiefe. Dort ist die Form frei, sie
  soll aber bis an den Rahmen reichen. Die Werte stehen mit Quelle unter `assumed_edges` im Manifest.
  **Magenta:** Gelenklinie, Gelenkmitte (+) und Anschlussdurchmesser. Er erscheint als Balken mit der Länge Ø und in der Draufsicht als Kreis.
- **Herkunft:** Jede Zahl steht mit Quelle (gemessen/Annahme) im `manifest.json`. Gelenkhöhen kommen aus
  [herkunft-r02.md](herkunft-r02.md), Hüllmaße aus `tools/r02_measure.py`. Die Pixelabbildung je Ansicht (`views.*`) führt Bildpixel
  zurück in mm, sowohl für Blender als auch zum Nachmessen fertiger Konzeptbilder.
- **Draufsicht:** Draufsicht und Untersicht des Masterblatts sind perspektivisch. Die Hände erscheinen dort etwa 350 mm vor dem Rumpf,
  laut Profil hängen sie bei f ≈ +25. Für Kopf, Oberkörper, Schulterpolster, Hand und Fuß (Sohle aus der Untersicht, gespiegelt)
  ist deshalb nur der **Umriss** anisotrop in den gemessenen Rahmen eingepasst. Er ist ein Formhinweis und nicht maßhaltig.
  Becken, Arm und Bein haben keine Draufsicht-Unterlage, weil Polster und Rumpf sie verdecken.
- **Ebenen:** `underlay` (blasser Blattausschnitt, 35 %, Form- und Stilanker),
  `frame`, `markers`, `swatches`. In Affinity die Ebenen `frame`, `markers` und `swatches` sperren und das Teil auf einer neuen Ebene `art` zeichnen.

## Stufen

1. **Form (jetzt):** nur Geometrie für Meshy. Zwei Töne genügen: Panzerplatten hell (`frost_shell`), Unterbau und Gelenke dunkel
   (`frost_frame`). Kristallfelder werden als eigene geschlossene Platten gezeichnet, flach hellblau und ohne Facettenlinien.
   Keine Decals, Lichter oder Beschriftungen. Die Silhouette muss das Masterblatt nicht exakt treffen: Innerhalb der Rahmen
   und an den Gelenken soll sie stimmen, Details dürfen vereinfacht werden.
2. **Farbe/Material (später):** alle sieben Farbfelder und Kristallfacetten, auf derselben Form.

## Regeln für die Teilbilder

1. **Vier Ansichten, rein orthografisch:** keine Perspektive, keine Verkürzung und keine Fluchtpunkte.
   Front, Seite, Rücken und Draufsicht zeigen dasselbe Teil an derselben Stelle der Schablone.
2. **Innerhalb der Hülle:** Das Teil füllt den gelben Rahmen und geht nicht über die Gelenkmarken hinaus.
   Am Anschluss endet es mit einem Querschnitt in der Größe des magenta Balkens bzw. Kreises.
3. **Geschlossene Flächen je Platte:** Jede Panzerplatte ist eine geschlossene Fläche mit durchgehender Umrisslinie.
   Keine offenen Striche, Schraffuren oder Lücken zwischen Platte und Unterbau.
4. **Eine Farbe je Material:** Nur die sieben Farbfelder (`frost_shell`, `frost_frame`, `frost_slate`, `frost_joint`,
   `frost_crystal`, `frost_core`, `frost_visor`) verwenden, flach gefüllt. Keine Verläufe, Glanzlichter, Schatten, Schattierung,
   Glow- oder Bloom-Effekte. Facettenlinien im Kristall sind erlaubt, wenn sie als Linien gezeichnet sind.
5. **Einheitliche Linienstärke:** Konturen in `frost_frame`, etwa 2 mm im Modellmaß (bei 3 px/mm ≈ 6 px), überall gleich.
   Keine dünneren Detailstriche.
6. **Innenseiten zeigen:** Flächen, die im Masterblatt verdeckt sind, vollständig ausführen. Dazu gehören die Rumpfflanken und der Rücken unter
   den Armen, der Oberarm unter dem Polster, der Oberschenkel unter dem Becken, die Handfläche und die Anschlussflächen.
   Hohle Rückseiten und angeschnittene Platten sind nicht erlaubt.
7. **Paarige Teile:** Gezeichnet wird die linke Seite (x > 0). Die rechte entsteht in Blender durch Spiegeln an x = 0, es gibt kein eigenes Bild.
8. **Konstruktionsfarben** (Gelb #FFD400, Magenta #FF00FF, Grund #808080) kommen im Teil nicht vor. Für die Abgabe an Meshy
   werden `underlay`, `frame`, `markers` und `swatches` ausgeblendet. Exportiert wird je Ansicht ein Ausschnitt oder das ganze Blatt als PNG 4000 px.
9. **Benennung:** Datei und Ebene heißen wie das Teil (`arm`, `arm-front`, `arm-seite` …), die Zeichnungsebene heißt `art`.
   Die Ebenen der Schablone behalten ihre Namen.

## Prompts und Varianten (reproduzierbar)

- **Quelle:** [r02-teile/varianten.toml](r02-teile/varianten.toml) enthält Vorlage, Teilbeschreibungen und Varianten. Die Varianten sind
  `a-blatt` (nah am Blatt), `b-kantig`, `c-glatt` und `d-schwer`. Neue Varianten bekommen eine neue, stabile `id`.
- **Erzeugt:** `tools/r02_part_templates.py` schreibt deterministisch [r02-teile/prompts.json](r02-teile/prompts.json) (8 Teile × 4 Varianten,
  je Prompt ein SHA256) und Kopien zum Einfügen unter `part-templates/prompts/<teil>--<variante>.txt`. Jeder Prompt nennt Breite,
  Tiefe und Höhe in mm, die Seitenverhältnisse je Ansicht, die Gelenke mit Lage und Ø, die verdeckten Flächen und das feste
  2×2-Layout (Front | Seite von links / Draufsicht | Rücken). Farben kommen aus `skins.toml`.
- **Bildreferenzen:** Bild 1 ist die Schablone `<teil>.png`, Bild 2 das Masterblatt `r02-sheet-9803.png`. Der Generator übernimmt die
  Positionen der Schablone nicht (Kopf-Probe 27.10.2026). Deshalb verlangt der Prompt nur das feste 2×2-Layout im gemeinsamen
  Maßstab, und das Prüfwerkzeug sucht die Ansichten selbst.
- **Ablegen und prüfen:** `python tools/r02_part_check.py BILD --part kopf --variant a-blatt --generator "…" [--prompt-file …] [--seed …]`.
  Das Werkzeug misst die Ansichten (Konsistenz, Proportionen, IoU gegen die Kontur) und legt sie unter
  `refs-r02/part-generations/<teil>/<variante>/<bild-sha12>/` ab: `source.png`, Meshy-Einzelansichten `front|side|back|top.png` (1024²),
  `prompt.txt` und `record.json` mit Bild-SHA, Prompt-SHA, Generator, Seed, Urteil und `blender_skalierung`. `index.json` listet alle Ablagen.
- **Reproduzierbarkeit:** Bildgeneratoren sind nicht deterministisch. Reproduzierbar ist deshalb die Kette aus Prompt-SHA,
  Schablonen-SHA, abgelegtem Bild-SHA und Messung. Formgen v2 und Blender verwenden immer ein abgelegtes Bild oder Netz und
  generieren nie neu. Eine Variante ist durch `teil/variante/bild-sha12` eindeutig benannt. Der Standardbau hängt davon nicht ab.
- **Meshy → Blender:** In Meshy die Ansichten Front, Seite und Rücken als Multi-View-Eingabe verwenden, die Draufsicht nur zur Kontrolle.
  Das Netz danach mit `blender_skalierung` (x/f/u) auf `frame_mm` bringen und an den Gelenkmitten aus `joints` ausrichten.

Kopf-Probe 27.10.2026 (Codex gpt-6-luna, älterer Prompt ohne Maßangaben): Ansichten untereinander konsistent (Höhe 1,5 %,
Breite 3,7 %, Tiefe 4,7 %). Das Bild ist zu schmal und zu flach (Breite 0,91, Tiefe 0,87). IoU rahmen-eingepasst 0,89–0,92,
Urteil „tauglich“, Blender-Skalierung x 1,10 und f 1,15. Abgelegt unter `part-generations/kopf/a-blatt/4fb623f7ab66`.

**Ohne Meshy:** `tools/r02_part_hull.py <ablage>` baut aus derselben Ablage eine deterministische, maßhaltige Silhouettenhülle
(GLB/OBJ, Modus `schnitt` oder `loft`), siehe [r02-silhouettenhuelle.md](r02-silhouettenhuelle.md).
