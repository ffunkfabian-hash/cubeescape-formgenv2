# Website

Einstieg ist `out/index.html`, offline per `file://`, ohne node, ohne Netz, ohne Verbindung zu Critic. Quelle: `formgen/web/` und die Stufe `viewer` (`formgen/viewer.py` → `formgen/web/site.py`).

| Datei | Inhalt |
| --- | --- |
| `index.html` | Start mit Navigation und Einstieg in beide Bereiche |
| `waffen.html` | Waffen nach BASIC-Typ, Suche und Variantenfilter; je Karte Blatt und 3D |
| `roboter.html` | Roboter nach Linie (`line`), Maße, Baugruppen; heute RA01 und RA02 |
| `3d.html?id=<ID>` | Eine Seite für alle 3D-Ansichten, optional `&baugruppe=<id>` (Baugruppe oder Einzelteil) |
| `web/` | CSS, Skripte, `catalog.js`, Three.js und Lizenz |
| `models3d/<ID>.js` | GLB als Base64, je Blatt per `<script>` nachgeladen |

Es erscheinen nur Blätter mit Vorschau und Spec-Format `formgenv2/weapon-sheet-spec` oder `formgenv2/robot-sheet-spec`. R01, R02, W01, KG02, VS02 fehlen bewusst; die Blätter selbst bleiben unverändert. Neuere Spec-Versionen brechen den Bau ab.

## Bau

`python -m formgen.viewer --out out` oder die Pipeline-Stufe `viewer`; beide laufen über `viewer.build(out, cache, force=…)`. Jede Datei ist ein Artefakt aus `formgen/cache.py`: ohne `--force` entsteht nur Fehlendes. Schlüssel: `VIEWER` und `SITE` (`formgen/web/site.py`), Seiten zusätzlich der Hash von `site.py` und der Blattliste, Webdateien ihr Dateihash, `models3d` Hash von GLB und Teilenamen. Bei Änderung am Modellskript `SITE` erhöhen. Die Module liegen außerhalb der Code-Closure der Bildstufen; `viewer.py` und `site.py` zu ändern baut keine Blätter neu (Test).

## Teile und Baugruppen

Die Markierung liest je Treffer die Node-Extras `basic_part`, `basic_assembly` und beim Roboter `basic_group`; `?baugruppe=` nimmt Baugruppe oder Einzelteil, in der Datei steht immer das Einzelteil (`assembly`). Gelesen wird ausgehend vom Mesh nach oben. Ohne Extras gilt: Teil = Node-Name, sonst `mesh_<n>`; Baugruppe = `source_segment`, sonst Name des übergeordneten Nodes. Deutsche Namen kommen aus Spec `parts` und `assemblies`.

## Änderungsdatei

Format `formgen/change-request` v1, Schema [change-request-1](schemas/change-request-1.schema.json): `model` (`id`, `kind` weapon oder robot, `name`, `asset`, `asset_sha256`), `requested_change`, `markings` mit `tool`, `comment`, `diameter_mm` und `samples`. Jede Probe trägt `part`, `assembly` und die Lage `location` (Node, Dreieck, Baryzentrik, Punkt im Node- und Modellraum; `local_formgen_fux_mm` nur beim Roboter).

Altdateien `formgen/robot-change-request` v1 (ein Punkt) und v2 (Markierungen, [Schema](schemas/change-request-legacy.schema.json)) bleiben lesbar, im Editor (`web/change-request.js`) und in Python:

```
python -m formgen.change_request <Datei>     # prüft und migriert auf stdout
```

`RoboterBasic-01` wird zu RA01. Migrierte Dateien tragen `migrated_from`; `change_request.downgrade` führt sie verlustfrei zurück (Inhalt, nicht Schlüsselreihenfolge). v1 kannte keinen Durchmesser: `diameter_mm` bleibt `null`, nur die Anzeige setzt einen Wert. Altfelder ohne eigenen Platz stehen unverändert in `source`. Der Editor schreibt nur das neue Format.

Öffnen: Eine andere Modell-ID wird abgelehnt. Bei anderem `asset_sha256` wird jede Probe einzeln geprüft: Liegt sie noch auf ihrem Dreieck, bleibt sie genau, sonst steht sie ungefähr auf ihrem Teil. Beim Speichern nennt die Datei weiter das Asset ihrer Herkunft, `migrated_from` bleibt erhalten.

## Three.js

Version 0.186.1 wie in der Lockdatei der Sicherung, Herkunft und Hashes in `formgen/web/vendor/three.json`, Lizenz daneben. Das npm-Paket liefert keine `.min.js` mehr, und ES-Module laden unter `file://` nicht; `formgen/web/vendor/pack_three.py` packt darum Kern, Renderer, `GLTFLoader`, `OrbitControls` und `RoomEnvironment` aus dem Tarball in ein klassisches Skript (1,3 MB, 260 KB gzip) ohne fremdes Werkzeug. Nur beim Versionswechsel von Hand aufrufen; der Bau liest allein das Ergebnis, ein Test prüft den SHA-256.

## Release

Das Hauptzip (`python -m formgen.release_assets`) folgt den Links von `index.html` und enthält Seiten, Blätter und `web/`. Die 3D-Daten kommen als eigenes Zip (0.9: 62 MiB gepackt, 205 MiB ausgepackt): `python -m formgen.release_assets --models3d`. Beide in denselben Ordner auspacken. Ohne 3D-Zip meldet die 3D-Seite die fehlende Datei.

Altnamen werden zugeordnet (`pauldron_l_338` → `pauldron_l`, `Crown_62` → `helmet_crown`); der Status nennt, wie viele Proben ungefähr stehen oder kein Teil mehr haben. Die Dateidaten bleiben unverändert.
