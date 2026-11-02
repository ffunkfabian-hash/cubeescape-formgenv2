
## Richter (gpt-6.1-sol high, Basis origin/claude/formgenv2-0.2-anvil, HEAD 849b9df)

| Nr | Datei:Zeile | Schwere (blocker/hoch/niedrig/ok) | Befund | Vorschlag |
|---|---|---|---|---|
| 1 | docs/generator.md:158 | niedrig | Blatt-Spec v2 mit Migration, Fixture und Migrationstest vorhanden; Mindestversion von Viewer und Release-Abnehmer fehlt. | Mindestversion für beide Abnehmer ausdrücklich nennen. |
| 2 | data/variants.toml:22; formgen/variants.py:101 | ok | Bestehende Blatt-IDs und Namen bleiben erhalten; neue Linien und deterministische Seeds kommen hinzu. | — |
| 3 | — | ok | Entfällt: Python-Projekt ohne Unity. | — |
| 4 | tests/test_variety.py:1; docs/versions/0.4.md:60 | niedrig | Tests ergänzt, keine erkennbare Abschwächung; Golden-Änderungen begründet. Kein Eintrag in `test_map.json` im Diff. | Neue Verhaltensprüfungen in der Testzuordnung ergänzen. |
| 5 | formgen/generator.py:486; formgen/generator.py:488; formgen/generator.py:506 | niedrig | Neue Geometriemaße ohne dokumentierte Herkunft: Mindestlänge 30, Randabstand 3, Streifenbreite 1 und Oberflächenversatz 0,2 mm. | Benannte Konstanten mit Herkunft als Vorgabe, Messung oder Annahme ergänzen. |
| 6 | CHANGELOG.md:3; docs/generator.md:1; docs/versions/0.4.md:1 | ok | Systemdoku, Modellsprache, Changelog und Versionsbericht berücksichtigen die Verhaltensänderungen; keine Werkbank betroffen. | — |
| 7 | formgen/ballon.py:51 | ok | Im Diff keine verbotenen Git-Aktionen oder Löschung fremder Arbeitsstände erkennbar. | — |
| 8 | docs/versions/0.4.md:26 | ok | Umfang entspricht einer Version; Baukasten, Varianten und deren Prüfung bilden ein zusammenhängendes Ziel. Keine erkennbare fachfremde Änderung. | — |

Nachbessern: 1, 4, 5
