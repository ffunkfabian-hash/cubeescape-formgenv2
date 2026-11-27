# Serie DaVinci

Eigene Serie neben BASIC und EXTENDED (Nutzerentscheid 27.11.2026): seltene, exklusive Spitzenmodelle der BASIC-Familie, je Modell mit
eigenem Signature-Skin. Reine Spiel-Assets für Cube Escape / KYBOS; „Funktion“ heißt Lesbarkeit im Spiel. Erstes Modell: **DaVinci-01
„Linea“**, Automatikgewehr, Blatt `DA01`, Skin **Sfumato** (0.52 „Atelier“, [Bericht](versions/0.52.md)).

## Register und Befehle

- Modelle unter `formgen/models/davinci/`, Register `formgen/davinci.py` (`MODELS`, `SHEETS`, `SKINS`). Blatt-ID `D<Linie><NN>`:
  Linie A = Grundform, NN = BALLON-Typ wie bei BA/EA (DA01 = Automatikgewehr, Klasse Langwaffe im Kanon). IDs sind ewig.
- Vokabular und Familienbausteine wie EXTENDED ([Modellsprache](modellsprache.md), [Design-Kanon](design-kanon.md)); nicht im
  EXTENDED-Register, nicht in den Linien EB–EN und nicht im Messblock des Kanons (der misst BASIC und EA).
- `~/Claude/cubeescape-nexogen/ce lock blender -- sh -c "cd $PWD && .venv/bin/python -m formgen.davinci preview d01 [--out <Ordner>] [--force]"` –
  Rastervorschau (CPU-Rasterizer, Sperre wie AGENTS.md › Befehle) aller Ansichten in Clay und im Skin, gleicher Maßstab,
  dazu ein Bogen `DA01_vorschau.png`. Ohne Blender, etwa 30 s; nur bei neuem Stempel `preview.json`, `--force` baut neu.
- `~/Claude/cubeescape-nexogen/ce lock blender -- sh -c "cd $PWD && .venv/bin/python -m formgen.davinci export d01"` – GLB, .blend und spec.json über
  BALLONs unverändertes `tools/blender_build.main` **ohne Ansichten** (kein Render). Der Wrapper setzt Farben und `finish` des Skins in
  `kit.MATERIALS` und benennt die Materialien `DA01_sfumato_<Rolle>`. Ziel `~/Library/Caches/CubeEscapeFormgen2/0.52/davinci/DA01/`;
  nur bei geändertem Stempel (`export.json`: Datensatz, Quellhash, Kit, Skinwerte, Wrapper), `--force` baut neu.
- Messzeile gegen die Familie: `formgen.kanon.measure_model(davinci.load("d01"), "DA01")` (etwa 90 s); Tests `tests/test_davinci.py`.

## DaVinci-01 „Linea“

### Auswahl unter drei Blockouts

Drei einfache Blockouts mit gleichem Griff, Magazin und Visier (Familienschnittstellen), Unterschiede nur in Silhouette, Hauptvolumen und
Linienführung; neutral (Clay) verglichen, gemessen mit `formgen.kanon` gegen BASIC A und EA01–EA17. Bilder und Quellen liegen außerhalb des
Repos (Bericht).

| | K1 Linea | K2 Arco | K3 Mandorla |
|---|---|---|---|
| Idee | gerade Oberlinie Kolben → Stirn, Daumenlochschaft, Nase steigt | Brückenbogen über dem Gehäuse trägt das Visier, freier Kühlmantel, Rahmenschaft | Gehäuse als Spitzoval (Linse), Balkenschaft |
| größte Seiten-IoU (G) | EA12/EA01 0,72 | EA01 0,74 | BA01/EA01 0,77 |
| Klarheit Achsen / Richtungen (G) | 0,51 / 0,82 | 0,57 / 0,81 | 0,40 / 0,78 |
| Eigenständigkeit | 4 | 3 | 4 |
| Zugehörigkeit zur Familie | 4 | 4 | 3 |
| Erkennbar als Automatikgewehr | 5 | 5 | 3 |
| Harmonie | 4 | 3 | 4 |
| Exklusive Wirkung | 5 | 3 | 4 |
| Summe | **22** | 18 | 18 |

K1 gewählt: Die gerade Linie über die ganze Länge ist sofort wiederzuerkennen, auch einfarbig und von weitem. Die Schaftschleife gibt den
Negativraum und erinnert an feine Sportwaffen. Es bleibt ein Gewehr der Familie (Griff, Schacht, Visier, mehrstufige Front). K2 wirkte wie ein
klassischer Tragegriff mit dünnem Rohr davor, K3 wie eine Gondel und am wenigsten wie ein Gewehr. Die Linse von K3 lebt als Schlossplatte
weiter. Die niedrige Klarheit von K1 lag an der frei gesetzten Unterlinie; im Ausbau gibt es nur noch einen Winkel (18°).

### Form

- **Linea (Leitmerkmal 1):** eine gerade Oberlinie u = 138 von der Schaftkappe bis zur Stirn, 806 mm, betont durch die Rückenleiste aus
  dunklem Titan und eine feine Goldlinie darunter. Darunter genau ein Schrägwinkel, 18°, gespiegelt um den Griff: Die Schaftstrebe steigt
  vom Griffboden nach hinten, die Nase des Vorderschafts nach vorn, das Unterteil hinten im selben Winkel. Alle übrigen langen Kanten sind
  waagerecht oder senkrecht (Test `test_linea`).
- **Vesica (Leitmerkmal 2):** Schlossplatte als Spitzoval (Schnitt zweier Kreise), 140 × 28 mm, auf beiden Gehäuseseiten als Intarsie ohne
  sichtbare Schrauben. Links sitzt der runde Energiekern (Oculus) als Schmuckstein über der vorderen Spitze: blanker Champagnerring, Glas,
  Leuchtring um eine dunkle Nabe. Er ist der eine Blickfang. Runde 1 hatte den Kern in der Mitte; Platte und Kern lasen sich dort als Auge.
- **Negativraum:** Der Daumenlochschaft ist eine geschlossene Schleife aus Kamm, Kolbenrücken und Strebe, die am Griffboden endet; der
  eingeschlossene Fläche misst rund 21 800 mm² (Test: > 8 000).
- **Hierarchie 60/30/10:** große Körper (Schale mit Schaft, Fahrgestell), mittlere (Schlossplatten, Nasenkappe, Rückenleiste, Magazin,
  Schaftkappe), kleine (Kern, Bedienteile, Riemenaufnahmen, Schrauben, Goldlinie, Schrift). Ruhige Flächen: Vorderschaftflanken und die Schale
  vor dem Kern bleiben frei.
- **Querschnitte:** Schulterfasen 7 × 10 mm an Schale und Schaft über die ganze Länge, Kielfasen an Unterteil und Vorderschaft, Draufsicht-
  Verjüngung der Front 46 → 38 mm, Seitenmulde im Vorderschaft parallel zur Nase.
- **Netz:** 25 928 Dreiecke im Export (G, BALLON-Kit mit Fasen; Ziel 20 k, Grenze 50 k wie EA15 mit 30 436 begründet): Der runde
  Kompensator mit drei Ringnuten und Ports trägt allein rund 4 000, die Schrift 1 600. Runde 4 senkte von 29 712 durch 24 statt 40 Segmente
  an Kompensator und Krone und 16 an den Riemenaufnahmen.
- **Familie:** Laufachse 106 und Visierlinie 68,5 mm wie BASIC-01, Griff BGM-1, Magazin BMW-R vor dem Bügel, Holovisier H0 auf BRI-22,
  Kompensator BMZ-15, Schichtung 2,5 mm, Radien R_BODY/R_MID/R_SMALL/R_FINE, Fuge waagerecht, Budgets (1 Blickfang, 2 Leuchten,
  1 Grafikband, 1 Schrift, 3 Akzent-Bedienfunktionen).

Messzeile (G, `formgen.kanon`, Klasse Langwaffe): Länge 905, Höhe 266, Breite 53 mm, L/H 3,4, Füllgrad 0,46, Visierlinie 68,5, 56 Teile,
121 Formen, Rundkörper 0,23, Quader 0,07, 14 Materialrollen, 10 blanke Teile, Klarheit Achsen 0,77 / Richtungen 0,90; kein Wert außerhalb des
Bands. Nachbar EA01 mit Seiten-IoU 0,70, BA01 0,64 (Kanon-Maß; `extended.side_iou` gegen BA01: 0,71).

### Skin „Sfumato“

Benannt nach Leonardos weichem Übergang von Licht in Schatten: ein tiefes, fast schwarzes Petrol, aus dem helle Elfenbeinflächen und wenige
Champagnerkanten auftauchen. Farben nur in `skins.toml` (`[skins.sfumato]`, `formgen = true`, auch als Finish für EXTENDED wählbar).

| Rolle | Farbe | Oberfläche (`finish`) | trägt |
|---|---|---|---|
| shell | Nachtpetrol `#173D46` (Hauptfarbe, 61 % der Seite) | seidenmatt beschichtet, rauh 0,45 | Schale, Schaft, Magazin |
| graphite | Elfenbein `#E4D9C3` (Sekundär, 19 %, mit den Platten 22 %) | Keramik seidenmatt, rauh 0,45 | Unterteil, Vorderschaft, Wangenpolster |
| anodized | Elfenbein `#E4D9C3` | Keramik, rauh 0,38 | Schlossplatten, Abzugsbügel, Griffboden, Anzeigenrahmen |
| dark_metal / sight_anod | dunkles Titan `#3D4247` / `#2E3236` | Rolle (Metall 0,8 / 0,6) | Nasenkappe, Rückenleiste, Schaftverbindung, Kompensator, Visier |
| trim | gebürsteter Champagner `#CDB68C` | Metall 1,0, rauh 0,28, anisotrop | Kernring, Laufbuchse, Krone, Schachtlippe, Zwischenlage, Schrauben, Leistenkappe |
| decal | Champagner `#CDB68C` (Druck) | Rolle (matt, rauh 0,5) | Goldlinie, Schrift |
| accent | Champagnergold `#C9A05C` | Metall 0,6, rauh 0,35 | nur Bedienung: Feuerwahlhebel, Magazinhalter, Ladehebel |
| rubber | warmes Schwarz `#1E2124` | Rolle | Griff, Schaftkappe, Griffpolster |
| energy | Bernsteinweiß `#FFD7A0` | leuchtend | Oculus, Munitionsanzeige, Absehen |

- Verteilung folgt der Architektur: Petrol trägt die Linea als ein Körper von Kolben bis Nase, Elfenbein das Fahrgestell darunter (der
  Familien-Zweiton umgekehrt: dunkel über hell, die Fuge bleibt waagerecht) und die Schlossplatten. Champagner nur an Kanten und am Kern.
- Kontraste (G, `extended_lines.delta_e`): Petrol/Elfenbein ΔE 68, Leuchte/Petrol 79, Petrol/Gummi 16. Nächste Familienskins nach der
  Schalenfarbe: Eisgrau 11, Carbon 12, Nachtwache 12 (alle neutralgrau; Petrol ist der einzige farbige dunkle Ton).
- Kennzeichnung: Schrift „DAVINCI-01  ED.I“ rechts am Vorderschaft (Editionsmarke), Goldlinie als einziges Grafikband. Gebrauchsspuren
  `wear = 0.25` (gepflegtes Sammlerstück), kein Schmutz.
- Grenzen: am Raster gewählt, nicht am AAA-Licht abgenommen. AgX bleicht helle und warme Töne (LESSONS); vor einem AAA-Render das Petrol und
  das Champagner am Cycles-Bild prüfen. Der Raster kennt `finish` nicht (Rauheit wirkt erst im GLB und in Blender).

## Grenzen

- Keine Linien (EB–EN-Entsprechung) und keine Website-Aufnahme; beides wäre eine eigene Version.
- Der Kanon-Messblock misst nur BASIC und EA; DA01 steht dort nicht, damit der Block für die Familie bleibt, wie er ist.
- Export ohne AAA-Bake und ohne Ansichten aus Blender; Prüfung der Form nur am Raster.
