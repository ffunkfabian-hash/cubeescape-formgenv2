# Vorschlag: native Formgen-Verträge im Toolgen-Abnehmer

Nicht implementiert; Toolgen ist im geltenden Auftrag ausdrücklich nur Lesereferenz.
Stand 27.10.2026, Abnehmer `28216d534b1d`, Produzentencheckpoint `20f3b04`.
Die folgenden Anforderungen beruhen auf echten Exportbytes und dem unveränderten
`scripts/tool_assets/concept_spec.py`, nicht allein auf Schemaprüfungen.
Prüfrecord: `~/Library/Caches/CubeEscapeFormgen/evidence/toolgen-consumer-2026-10-27.json`.

## Tatsächliches Verhalten

| Eingang | Echter Toolgen-Abnehmer |
|---|---|
| KG02 Legacy-Geo und WeaponSpec2 | akzeptiert, 29 geplante Netze, vier Paletten |
| W01 WeaponSpec2 | geladen; der dabei gefundene Produzentenfehler in `other_colors` wird mit SPEC4 behoben |
| W01 `cubeescape-formgen/geometry-spec` 1 | `load()` verweigert den Namespace |
| R01 `cubeescape-formgen/figure-geo` 1 | `load()` verweigert den Namespace |
| R01 `cubeescape-formgen/figure-spec` 1 | `weapon_spec()` verweigert erwartungsgemäß den Figurenvertrag |

W01s Zusatzfarben müssen den unveränderten Spec2-Vertrag verwenden: dominante
Kanalfarbe nach Netzoberfläche, weitere Farben als `[{color, share}]`. Ein
Dictionary mit pNN-Schlüsseln wird von `palettes()` als Liste von IDs gelesen.
Die einzelnen Teile behalten ihre Rollenfarbe in `parts[].color`.

## Anforderungen an eine separate Abnehmeränderung

1. Die nativen Namespaces ausdrücklich unterscheiden. W01 behält seine ID;
   Figuren benötigen einen eigenen Importpfad statt `sheet.kind == weapon`.
   Provenienz und tatsächliche Datei-SHAs bleiben zwingend.
2. Bereits geschlossene indizierte Netze präzisionserhaltend übernehmen.
   Toolgens `weld()` rundet Legacy-Koordinaten auf fünf Dezimalstellen in Metern.
   Damit beschädigt es aktuell `p28/sight_clamp` (40 → 38 Vertices, vier
   kollabierte Dreiecke) und `p31/sight_frame` (108 → 94 Vertices, acht
   kollabierte Dreiecke). Beide Ausgangsnetze sind geschlossen. Bei p28 liegen
   die kollabierten Vertexpaare nur 2,227 µm auseinander. Topologie nach jeder
   zulässigen Zusammenführung prüfen; keine Flächen entfernen, um Fehler zu verdecken.
3. Vorhandene Fasen ausdrücklich kennzeichnen und respektieren. `plan()` setzt
   für nichtleuchtende Legacy-Netze erneut `bevel_m`; `concept_kit.py` wendet
   darauf eine Blender-Fase und Bereinigung an. Dies darf native bereits
   ausgewertete Netze nicht nochmals verändern.
4. Optionale Autorenangaben als solche behandeln. W01 besitzt keinen belegten
   Schwerpunkt, keine vollständige Griff-/Stützhandmessung und keinen als
   solchen deklarierten Visier-Rückpunkt. `sockets()` setzt aktuell
   `socket_sight_rear_m` und nichtnullbare Schwerpunktwerte voraus; `hold()`
   setzt `grip` voraus. Solche Angaben dürfen beim Import nicht erfunden werden.
5. `author_move` von einer geprüften Animationsknoten-Zuordnung unterscheiden.
   `toolgen_node: null` ist keine Freigabe eines Bewegungsclips.
6. Prüfberichtfelder gemeinsam spezifizieren. `plan()` erwartet zusätzlich
   `checks.decals_outside_part`; native Ergebnisse besitzen dieses Legacy-Feld
   nicht. Ein leerer Default darf erst nach vereinbartem Prüfverhalten als
   Erfolg interpretiert werden.

Die direkte Diagnose über `plan(export_dict)` scheitert schon an p28;
`sockets(export_dict)` an `socket_sight_rear_m`, `hold(export_dict)` an
`grip: null`. Diese Helferaufrufe sind keine Importabnahme und ändern keinen
Namespace. Ein bloßes Allowlisting der Formate erfüllt den Vertrag nicht.

## Erforderliche Abnahme der separaten Änderung

Echte W01-/R01-Fixtures samt Specs und SHA-Provenienz verwenden, ohne sie in
Legacy-IDs umzubenennen. Vorher/nachher Teil-IDs, Koordinaten, Topologie,
Anker und vorhandene Fasen prüfen. Den Legacy-KG02-Pfad unverändert testen.
Figuren behalten Baugruppen, Elternteile, Rollen und Posen; fehlende
Waffenangaben bleiben unbestimmt. Die Mindestversion des Toolgen-Abnehmers
kann erst nach Implementierung und eigenständiger Prüfung genannt werden.
