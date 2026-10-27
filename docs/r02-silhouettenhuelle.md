# R02-Teilbild → Silhouettenhülle (Prototyp, 27.10.2026)

Optionaler Formweg ohne Meshy. Aus einem abgelegten KI-Teilbild entsteht ein deterministisches, maßhaltiges Netz.
Kein Modul unter `formgen/` liest es, und kein Standardbau hängt davon ab.

## Verfahren

`python tools/r02_part_hull.py <ablage> [--modus schnitt|loft] [--tol-mm 0.5] [--views front,side,top] [--force]`

1. **Silhouette je Quadrant** (`record.json` › `quadranten_px`): Vordergrund gegen den Grund mit derselben Regel wie
   `r02_part_check` (Abstand > 40 zur Eckfarbe). Löcher werden gefüllt, es bleibt die größte Komponente.
2. **Polygon:** Die Zeilenläufe werden als Rechtecke vereinigt (manifold `CrossSection`) und mit `--tol-mm` vereinfacht
   (Annahme: 0,5 mm). Danach wird das Polygon **anisotrop auf `frame_mm`** eingepasst. Die Draufsicht liegt in (x, f), vorn ist unten.
3. **Schnitt:** Die Front (x,u) wird entlang f extrudiert, die Seite (f,u) entlang x und die Draufsicht (x,f) entlang u. Die Hülle
   ist der Schnitt dieser drei Körper, also `prism2` aus [modellsprache.md](modellsprache.md), erweitert um die Draufsicht.
   **Loft** (`--modus loft`) schneidet zusätzlich einen vierten Körper ein: Die Draufsicht wird je Höhe (2 mm, Annahme) auf die
   Front-Breite und Seiten-Tiefe dieser Höhe skaliert.
4. **Ablage** `part-generations/<teil>/<variante>/<bild-sha12>/hull[-loft…]/`: `hull.glb` und `hull.obj` (Meter, Y oben,
   Blender-Import ergibt X = x, Y = −f, Z = u), `hull.json` (Eingabe-SHAs, Parameter, Messung, Profilpolygone in mm) und `contact.png`.
   Die Rückansicht baut nicht mit, sie dient als unabhängige Gegenprobe.

## Messung Kopf `kopf/a-blatt/4fb623f7ab66`

| | Schnitt (`hull/`) | Loft (`hull-loft/`) |
|---|---|---|
| Rahmenabweichung x/f/u | 0,0 / 0,0 / 0,0 mm | ≤ 0,09 mm |
| Netz | 2 082 Dreiecke, Genus 0, 9,59 l | 47 750 Dreiecke, Genus 0, 8,46 l |
| Quader-Füllgrad | 0,60 | 0,53 |
| IoU Hülle ↔ Quelle Front / Seite / Draufsicht | 0,995 / 0,998 / 0,997 | 0,995 / 0,998 / 0,994 |
| Gegenprobe Rücken (nicht extrudiert) | 0,958 | 0,958 |
| IoU Masterkontur Front / Seite / Rücken (Hülle) | 0,920 / 0,892 / 0,924 | gleich |
| zum Vergleich: Quellbild, rahmen-eingepasst | 0,915 / 0,888 / 0,895 | |
| Hals-Querschnitt u = 1775 (Soll Ø 163,2) | 145 × 216 mm, Mitte innen | gleich |
| Laufzeit | 0,9 s | 6 s |

- **Toleranz:** Vorgegeben sind 0,5 mm. Gemessen weicht das Polygon um höchstens 0,74 mm (≈ 1,5 px) von der Pixelkante ab.
  Ein Bildpixel entspricht 0,44–0,52 mm. Polygon-IoU gegen die Maske ≥ 0,996.
- **Blender 5.2.2 Import** (GLB und OBJ): Ausdehnung x −116,2…121,1, Y −159,0…121,0 (= −f), Z 1760…2000 mm. Das Volumen ist positiv
  (Normalen außen), es gibt 0 nicht-mannigfaltige Kanten.
- **Reproduzierbar:** Ein zweiter Lauf mit `--force` ist bytegleich (GLB, OBJ, JSON, PNG). Ohne `--force` meldet das Werkzeug
  „aktuell“, wenn Bild-SHA, Quadranten, Teil-Manifest, Parameter und `VERSION` gleich sind.
- **Synthetische Prüfung** (`tests/test_r02_part_hull.py`): Eine Kugel ist in jedem Quadranten mit anderem Pixelmaß gezeichnet.
  Der Schnitt trifft das Tricylinder-Volumen 8(2−√2)·r³ auf 0,999, der Loft das Kugelvolumen auf 1,000.
- **Beleg:** `~/Library/Caches/CubeEscapeFormgen/refs-r02/part-generations/kopf/a-blatt/4fb623f7ab66/hull/contact.png` und
  `…/hull-loft/contact.png`. Oben stehen die Quellquadranten, unten die Hüllen-Orthos im Quellraster mit der Quellkontur in Gelb
  und eine 3/4-Ansicht.

## Was die Hülle kann

- **Maßhaltig per Konstruktion:** Die Rahmen aus `frame_mm` werden exakt getroffen. Gelenkmitten und Achsen entsprechen formgen,
  eine nachträgliche Blender-Skalierung entfällt.
- **Silhouettentreu:** Gegen die Masterkontur ist die Hülle so gut wie das Bild selbst (Abweichung ≤ +0,03). Der Weg verliert also
  nichts, die Grenze setzt das KI-Bild.
- **Reproduzierbar und billig:** Es gibt keine Zufallsquelle, und ein Lauf dauert unter einer Sekunde. Varianten sind entweder
  andere abgelegte Bilder (`teil/variante/bild-sha12`) oder andere Parameter (`--modus`, `--tol-mm`, `--views`), die in eigenen
  Ordnern mit sprechendem Namen liegen.
- **Prüft das Bild:** Die Rücken-Gegenprobe (0,958) misst, wie gut Front und Rücken des Generators zusammenpassen. Der Hals-Schnitt
  zeigt, dass das Bild am Anschluss schmaler und tiefer ist als der Ø 163.

## Was sie nicht kann

- **Hohlformen und Mulden:** Eine Silhouettenhülle ist die größte Form, die zu den Umrissen passt. Was in keiner Ansicht als Umriss
  erscheint, entsteht nicht: Visiermulde, Ohrscheibe, Kragenöffnung, Unterschnitte, Hohlräume. Rückseiten werden also immer voll.
- **Plattenfugen und Innenlinien:** Farben und Linien im Bild werden ignoriert, die Hülle ist ein einziger Körper ohne Fugen,
  Kristallfelder oder Visierfläche.
- **Diagonalen (nur Schnitt):** Jeder Querschnitt ist Rechteck ∩ Draufsicht. Die Kuppel wird deshalb zum Klostergewölbe mit Graten
  auf den Diagonalen, bei einer Kugel ergibt das +12 % Volumen. Der Loft rundet diese Grate, nimmt dafür aber an, dass die Draufsicht
  in jeder Höhe ähnlich aussieht. Das gilt nicht für Teile mit wechselndem Querschnitt (Visierkinn, Schulterpolster-Kante).
- **Proportionsfehler werden versteckt, nicht behoben:** Die anisotrope Einpassung streckt ein zu schmales Bild (Breite 0,91,
  Tiefe 0,87) auf den Rahmen. Damit werden auch Details um 10–15 % verzerrt.
- **Treppenstufen im Loft:** Die Breiten kommen aus Pixelzeilen, deshalb zeigt die flache Schattierung feine Bänder. Glätten wäre ein
  weiterer Parameter.

## Empfehlung

**Ja, als optionaler Teilbaukasten übernehmen, aber als Profil- und nicht als Bildquelle.** Vorschlag:

1. formgen v2 bekommt eine Form `hull3` (Front/Seite/Draufsicht wie `prism2`, optional `loft`). Sie liest **Profilpolygone in mm**
   (`hull.json` › `profile_mm`), keine Bilder. Die Profile werden einmal aus einer Ablage übernommen und mit Herkunft
   (`bild_sha256`, Werkzeugversion, Toleranz) als Spec-Daten eingecheckt. Der Standardbau bleibt dann ohne KI und ohne Cache baubar.
2. Diese Form nur als **Grundkörper** verwenden. Platten, Fugen, Visier und Mulden setzt weiter das ballon-Kit-Vokabular
   (Cuts/Decals, Fasen) darauf.
3. Bei Meshy-Netzen die Hülle als **Prüf- und Schnittkörper** nutzen, entweder als Meshy ∩ Hülle oder über die IoU je Ansicht.
   Damit bleibt das Meshy-Ergebnis maßhaltig.

Nicht empfohlen ist es, die Hülle unverändert als fertiges Teil zu verwenden: Ohne Mulden und Fugen bleibt sie ein Grobkörper.
Offene Entscheidung für den Nutzer: ob `hull3` in die Modellsprache aufgenommen wird. Das wäre eine Formatänderung unter
`formgen/` und damit eine eigene Version.
