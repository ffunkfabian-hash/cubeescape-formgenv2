# FigureSpec 1 und Spec-/Prompt-Ausgabe

`formgen.spec.build(document)` verarbeitet die gemeinsame ausgewertete Geometrie. `figure` liefert
`cubeescape-formgen/figure-spec`, `format_version: 1`; keine Bildanalyse und keine automatische Größenanpassung.

- `figure`: vollständiges Autoren-INFO einschließlich Herkunft.
- `units: m`, `axes`: +X links, −Y vorn, +Z oben, unveränderter Autorenursprung.
- `dimensions_m`: Länge/Y, Höhe/Z, Breite/X und AABB aus allen Netzvertices.
- `assemblies`: unveränderte Baugruppen einschließlich vorhandener Explosionsversätze in Autorenmillimetern.
- `parts`: stabile Autoren-ID, Label, Baugruppe, Materialrolle, Elternteil, AABB/Maße, Oberfläche in m² und Herkunft.
- `anchors`: Autorenanker einschließlich `position_m` im gemeinsamen Weltraum und Quellen; `at` bleibt f/u/x in mm.
- `poses`: unveränderte deklarierte Posen, keine behauptete Animation oder mechanische Simulation.
- `measurement_source`: Netz-AABB und Summe tatsächlicher Dreiecksflächen; keine Masse-/Volumenschätzung.
- `source`, `warnings`: Quelldatei/Hash und sämtliche Geometriewarnungen. Ein Maß ist eine Netzmessung,
  seine Entwurfsgrundlage bleibt als Vorgabe oder Annahme im Herkunftsfeld sichtbar.

`formgen.prompts.build(document)` liefert `de`, `en`, Messwerte, Quellen und Warnungen.
Bauteilnamen stammen aus `label`/`en`; fehlende englische Übersetzungen behalten den gekennzeichneten Quellnamen.
Masterprompt-Wörter dienen als Darstellungsauftrag, nicht als Beleg für vorhandene Formdetails.

## Weapon-/Sight-Kompatibilität

SHA-geprüfte Original-Specs aus `geo.load` werden nach vollständiger JSON-Schema-Prüfung als unveränderte tiefe Kopie
weitergegeben. Ohne Original-Spec bricht ein Geo-Import ab: keine Rekonstruktion fehlender Toolgen-Felder.
KG02/VS02 behalten daher ihren Weapon-/Sight-Spec-2-Vertrag einschließlich Originalkoordinaten und IDs.

Neue Waffen (W01) erhalten Weapon-Spec 2 gemäß `docs/schemas/weapon-spec.schema.json`.
`part_id_map` ordnet Autoren-IDs in deklarierter PARTS-Reihenfolge `p00` … `p999` zu; `source_id` bleibt am Teil.
An bestehende Modelle Teile anhängen, nicht umsortieren, wenn pNN-Abnehmerreferenzen stabil bleiben müssen.
Netz-Bounds und Anker werden um den belegten `Socket_Hand` verschoben; die Transformation wird in `axes`
mit `origin_world_m` und `origin_source` offengelegt. Flächen sind aus ausgewerteten Dreiecken gemessen.
Unbekannte Anker bleiben null; insbesondere wird kein Schwerpunkt aus einer erfundenen Massedichte erzeugt.
`author_move` bewahrt Bewegungsdeklarationen in Autorenkoordinaten, ohne Toolgen-Bewegungsclips zu behaupten.

Pflichtpaletten kommen ausschließlich aus `skins.toml`: base=Rollenbasis, standard=standard,
arktis=polar, nacht=nacht. Kanalzusatzfarben werden pro pNN in `other_colors` ausgewiesen.
Materialrollen werden ausdrücklich auf erlaubte Toolgen-Kanäle und -Materialklassen abgebildet.
Texturmuster, Sichtfenstertyp und Waffen-Element bleiben unbestimmt, solange keine Autorenangabe vorliegt.
Die Schema-Prüfung bestätigt die Datenstruktur; sie ersetzt keinen Importtest im Toolgen-Abnehmer.
