# Vorschlag an Sightline: Bausteine für mehr Formvielfalt (aus Formgen v2 0.4 „Mosaic“)

Stand 02.11.2026. BALLON wurde nicht geändert; dies ist nur ein Vorschlag (Regel: Vorschläge an BALLON nur unter `docs/`).

## Ausgangslage

Formgen v2 baut seit 0.4 acht Linien × 17 Typen nur aus BALLON-Vokabular: Längen (vorn, hinten, Wurfarme, Magazin, Mündung),
Tausch genormter Bausteine (Visier-Baukasten v3, Schaft S1/S2, Griff v2.1), Leuchtstreifen, v2.1-Pilot als zweite Grundform,
acht Skins. Gemessen weicht jede Linie sichtbar ab (Silhouetten-IoU gegen die Baseline ≤ 0,973, Median 0,872), aber die
**Gehäusekontur** jedes Typs bleibt dieselbe. Formgen v1 hatte je Linie eine eigene, von Hand modellierte Formsprache
(Gehäuse, Handschutz, Schaftlinie). Das lässt sich aus Parametern nicht erzeugen, ohne eigene Grundgeometrie zu erfinden.

## Vorschlag

1. **Gehäusefamilien als Bausteine** in `basic/common.py`, gleiche Schnittstellen wie heute (Laufachse, Gehäuseende für BST-1/2,
   Schienenhöhe BRI-22, Griffaufnahme BGM-1, Schacht BMW-R): je Familie 2–3 Oberteil-Konturen (kantig, gestuft, gerundet),
   parametrisiert nur über Länge und Höhe. Formgen v2 tauscht sie wie heute das Visier.
2. **Handschutz-Varianten** (geschlossen, gelocht, Rippen, Schiene unten) als Baustein mit Socket_SupportHand an fester Stelle.
3. **Mündungsteile** als benannte Bausteine (Bremse, Kompensator, Dämpfer) mit BMZ-15 statt nur Länge/Radius.
4. **Schaft S3** (Skelett/Klappschaft) für die Linie „Skeleton“; heute kürzt v2 nur S1.

## Befunde zum Designvertrag (gemessen, pinned `dcdda603`)

- Visierlinie über der Laufachse außerhalb 60–80 mm in den Standardmodulen 11 (88 mm), 14 (98 mm), 15 (95 mm).
- v2.1-Piloten: 3–5 verschiedene Akzent-Bedienfunktionen (Klemmhebel des Visiers, Höhenturm, Ladehebel, Feuerwahl,
  Magazinhalter …); entweder nennt der Vertrag Visier-Bedienelemente als Ausnahme oder die Piloten entfärben einen Teil.
- BALLONs GLBs in `~/Library/Caches/CubeEscapeBallon/out/BASIC-03-v2.1` und `BASIC-06-v2.1` sind neuer als der gepinnte Spec
  (Maße und Baugruppen geändert); ein neuer Pin in Formgen v2 übernimmt das automatisch per Quellhash.
