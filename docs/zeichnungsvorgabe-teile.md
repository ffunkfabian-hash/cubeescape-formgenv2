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

## Prompt-Baustein Form (Englisch, Stufe 1)

Die Schablone (`<teil>.png`) und das Masterblatt `refs-r02/r02-sheet-9803.png` als Bildreferenzen mitgeben, `<PART>` ersetzen:

```text
Orthographic shape study of a single robot part: <PART> of the robot "Frost". Purpose: clean geometry for
image-to-3D, not a finished illustration. Use the attached master sheet only as shape reference (plate language,
proportions) and the attached template as exact layout: draw the part inside the yellow and orange bounding boxes in
all four views (front, left side, back, top), aligned to the magenta joint lines, ending at each joint with a
cross-section matching the magenta bar/circle. Orange dashed edges mark hidden areas: invent a simple, plausible
continuation of the armor that reaches the box edge. Strict orthographic projection, no perspective, no
foreshortening. Two flat tones only: light grey-white armor plates (#E2EAEE) and dark graphite frame and joints
(#262B33); ice crystal panels as separate closed plates in flat light blue (#A6DCF8) without facet lines. Every plate
is a closed shape with one uniform dark outline of constant width. No shading, no shadows, no gradients, no glow, no
texture, no decals, no text, no dimension lines. Simplify small details, keep the silhouette and plate breaks clear.
Show surfaces hidden on the master sheet fully modeled. Do not draw beyond the joint lines and no other body parts.
Neutral mid-grey background (#808080).
```

## Prompt-Baustein Farbe (Englisch, Stufe 2)

Wie oben, `<PART>` und `<VIEWS>` ersetzen:

```text
Orthographic technical concept sheet of a single robot part: <PART> of the robot "Frost" (white armor plates,
dark graphite frame, slate-blue straps, light-blue faceted ice crystals). Use the attached master sheet ONLY as
style reference (shapes, plate language, crystal panels) and the attached template as exact layout: draw the part
inside the yellow bounding boxes in all four views (front, left side, back, top), aligned to the magenta joint lines,
ending at each joint with a cross-section matching the magenta bar/circle. Strict orthographic projection, no
perspective, no foreshortening. Flat cel colors only, one solid color per material from these swatches:
#E2EAEE white shell, #262B33 dark frame, #4A5268 slate, #3A414B joint metal, #A6DCF8 ice crystal, #8FD3F7 core glow,
#4C7C9C visor. No gradients, no shading, no shadows, no glow, no bloom, no texture noise. Every armor plate is a closed
shape with one uniform dark outline of constant width. Show surfaces that are hidden on the master sheet (inner sides,
areas under the arms, connection faces) fully modeled. Do not draw beyond the joint lines, no other body parts,
no background objects, no text, no dimension lines. Neutral mid-grey background (#808080). <VIEWS>
```

Für Meshy (Bild zu 3D) nur eine Ansicht je Bild exportieren, zuerst die Front, dann die Seite; Draufsicht und Rücken dienen zur Kontrolle.
Das Netz in Blender mit `manifest.json` (`frame_mm`, `joints`) auf mm und die Gelenkmitten setzen (vgl. `tools/meshy_prepare.py`
auf Branch `claude/hungry-hertz-e30abc`).
