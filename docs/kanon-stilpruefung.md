# Stilprüfung einer neuen Waffe gegen den Design-Kanon (Vorlage, 0.42 „Canon“)

Prompt für ein **zweites** Modell, das die Waffe nicht gebaut hat (Gegenstück zum Richter mit `pruefung.md`: der Richter liest den Code,
die Stilprüfung sieht nur Bilder). Sie ersetzt nicht die Sichtung durch den Nutzer, sie filtert vorher.

## Eingabe

1. [Design-Kanon](design-kanon.md) vollständig, mit Messtabelle und „Nie wieder“.
2. Übersicht der Familie: BASIC (17 × 12) und EXTENDED (17 × 13) als Rastervorschau, aus `python -m formgen.kanon paket --bilder …`.
3. Die neue Waffe: Rasteransichten `iso`, `side_left`, `top`, `front`, `rear`; AAA-Bilder nur, wenn der Nutzer sie freigegeben hat.
4. Ihre Messzeile: `python -m formgen.kanon zeile <Kurzname>` für ein Modell im Register von `formgen.extended`, sonst
   `formgen.kanon.measure_model(modell, blatt)` (Länge, Höhe, Breite, L/H, Füllgrad, Visierlinie, Akzente, Hände, Rollen, Nachbar;
   Detaildichte: Teile, Formen, Rundkörper, Quader, Materialrollen, blanke Kanten) und `formgen.kanon.outside(zeile, familie)`.
5. Konzeptzeilen des Entwurfs: Rolle, Leitmotiv, Silhouette (drei Sätze).

## Prüfpunkte

| Nr | Kriterium | Frage |
|---|---|---|
| 1 | Familie | Gehört die Waffe erkennbar zu BASIC/EXTENDED (Grundsätze, Formvokabular, Materialrollen)? Welche drei Merkmale belegen das? |
| 2 | Neuheit | Ist das Leitmotiv neu gegenüber der Motivtabelle? Nennt der Nachbar (Seiten-IoU) ein Modell, dem sie zu nah kommt? |
| 3 | Klasse | Liegen die Messwerte im Band ihrer Klasse? Jede Abweichung braucht einen Grund aus dem Konzept; Detaildichte unter dem Band (Teile, Formen, Rundkörper) ist mindestens `hoch`. |
| 4 | Nie wieder | Trifft ein Punkt der Liste „Nie wieder“ zu (kastig, Stifte unter Ø 12 mm, loses Visier, schwebende Teile, geschertes Magazin …)? |
| 5 | Lesbarkeit | Liest sich die Waffenart aus der Seitensilhouette allein, auch klein (etwa 64 px breit)? |
| 6 | Funktion | Sind Griff, Stützhand, Visier, Munition und Mündung sichtbar und plausibel verbunden? |
| 7 | Rollen | Tragen Schale, Graphit und Akzent die Form, bleibt die Leuchtrolle Blickfang (Rollentest)? |
| 8 | Ansichten | Sind Front-, Rück- und Draufsicht so durchgeformt wie die Seite (Lehre „kastig fällt erst im Bild auf“)? |

## Ausgabe

Genau eine Tabelle `| Nr | Ansicht | Schwere (blocker/hoch/niedrig/ok) | Befund | Vorschlag |`, je Prüfpunkt mindestens eine Zeile, danach
die Schlusszeile `Freigabe` oder `Nachbessern: Nr. …`. Befunde beziehen sich auf sichtbare Stellen („side_left, vorderes Drittel unten“),
nicht auf Vermutungen über den Code. Kein Lob, keine Gesamtnote.
