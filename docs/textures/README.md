# Eingefrorener v1-Texturkatalog

`catalog.json` ist die bytegleiche Lesekopie aus
`cubeescape-formgen/docs/textures/catalog.json` vom26.10.2026,
SHA256 `3691845e6b1683861deb075bb6056a40c5e1f6a9457007d449f8a643dc7f8fb6`.
Sie enthält Finish-Tonleitern, Glanzstreifen- und Abnutzungsparameter für die
bereits aufgelösten, SHA-geprüften Legacy-Specs. Keine alten Modellmodule.

Neue Modelle beziehen ihre Farben weiterhin ausschließlich aus `skins.toml`.
Legacy-Farben und Flächenlagen bleiben Bestandteil ihres importierten Vertrags;
der Katalog ergänzt dessen gemeinsame Finish-Parameter. Quelle und Abweichungen
des Auswertungscodes stehen im Modul `formgen/legacy_surface.py`.
