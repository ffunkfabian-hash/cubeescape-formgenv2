# Lehren

Nur wiederkehrende Dauer-Fallen; alle übrigen Lehren stehen unverändert in [LESSONS-lang.md](LESSONS-lang.md).

- Bei Geo-Import Original-Specbytes erhalten, wenn Produzenten-Hashes weitergelten; kanonisches Neuschreiben verändert den SHA ohne semantische Änderung. [Geo](geo-export.md)
- Native Modell-ID nie als kollidierende Legacy-ID tarnen, um ein Schema zufriedenzustellen; Erweiterung als eigenen Vertrag kennzeichnen. [Geo](geo-export.md)
- Ein grüner Fixture-Release-Test ersetzt keinen Probelauf mit echten Artefakten: Schriften, verschachtelte Specs und absolute Pfade separat prüfen. [Geo](geo-export.md)
- Layoutcache darf Rasterversion ignorieren, muss aber tatsächlich verwendete PNG-Größe/Callouts/Skalierung hashen; sonst bleiben Beschriftungen nach Größenwechsel veraltet. [Cache](cache.md)
- Ein durchlässiges JSON-Schema beweist keine Abnehmersemantik: Spec2-Zusatzfarben als echte color/share-Listen prüfen, native Netze nicht durch Legacy-Weld und erneute Fasen verändern. [Vertragsbefund](vorschlag-toolgen-native-contract.md)
- Manifest nicht je Artefakt neu schreiben: bei ~1000 Treffern wurde der warme Lauf quadratisch (21,6 s → 3,2 s nach Bündelung je Stufe). [Generator](generator.md)
- Stufen-Closure am Ort des Builders messen: liegt der Builder in einem Sammelmodul, fehlen Geometrie-Imports im Schlüssel; Test prüft, dass geom/model in der Closure stehen. [Generator](generator.md)
- Fremde Werkzeuge ohne Datenschnittstelle nicht nachbauen: den erzeugten Datensatz nur für den Lauf als Modul einhängen und das unveränderte Werkzeug aufrufen; Baseline muss dann bytegleich sein. [Bericht](versions/0.5.md)
- Zufall für reproduzierbare Varianten je Parameter aus einem Inhaltshash ziehen, nicht aus einem gemeinsamen RNG-Strom: ein neuer Parameter verschiebt sonst alle späteren Ziehungen. [Generator](generator.md)
- Eine statische Import-Closure findet auch lazy Importe in Funktionen; ein erweiterter Snapshot ändert daher Quellhashes aller Typen, die das Modul importieren – Snapshot-Ordner an die Pfadliste binden. [Generator](generator.md)
- Ein Vielfaltsmaß gegen die Baseline deckt formgleiche Linien auf, die nur die Farbe wechseln (Bogen in B/C); Front-IoU allein taugt nicht, Langwaffen sind von vorn fast gleich. [Generator](generator.md)
- Asset- und Blattweg müssen dieselbe Grundform-Auflösung und denselben Variantenlauf teilen (`generator.vary`): 0.5 lud für GLBs stets die Formstudie ohne Bausteine – D/H und alle Baukasten-Linien wären falsch gewesen. [Bericht](versions/0.6.md)
- Für Punktregeln „wie Anker“ ist der Anker selbst das beste Orakel: je Anker einen Prüfpunkt-Zwilling in POINTS legen und nach jedem Eingriff Gleichheit fordern; Gegenprobe mit festen Punkten muss rot werden. [Tests](../tests/test_points.py)
- Eine Gegenprobe nicht nur auf „rot“ prüfen, sondern auf den erwarteten Grund: `carried == q.get("parent_part")` war mit `None == None` immer wahr, die Mechanikprüfung übersprang alle Teile ohne Elternteil und meldete 0 Verstöße; erst die Gegenprobe mit „im Weg“ deckte es auf. [Tests](../tests/test_series.py)
- Bausteine auf der Mittelebene gehören nicht an eine Seitenschiene: an BASIC-14 landeten Visier und Socket_Eye im Rohr, ohne dass eine Maß- oder Vertragsprüfung anschlug; seit 0.8.1 quer versetzt mit BALLONs `side_mount`. [Generator](generator.md)
- Skin-Farben am AAA-Licht wählen: AgX und Key-Licht bleichen stark (Orange wird lachsfarben), das Raster-Blatt zeigt die Farbe unverändert; Abnahme der Palette am Cycles-Bild, nicht am Blatt. [Serien](generator.md)
- `formgen/__init__.py`, `versions.py` und `skins.toml` stehen in den Schlüsseln aller Waffenstufen: Versionsbump oder neuer Skin macht 204 Blätter veraltet. Vor solchen Änderungen `out/` aus dem Cache füllen, Bump zuletzt, neue Stände als eigene Konstante. [Bericht](versions/0.9.md)
- Vor dem Anstellen an eine Sperre Treffer zählen (`plan` + `(cache/key).exists()`): ein Lauf, der nur aus dem Cache wiederherstellt, braucht weder Blender noch Sperre. [Bericht](versions/0.9.md)
- Eine Quelle erst gegen die Referenz vermessen, dann entscheiden: der ID-Abgleich traf 138 von 422 Teilen, das Namensschema (Segment + Seite + ID) traf alle, und die Teile lagen auf 1–3 mm. [Roboter](robot.md)
- GLTFExporter schreibt Node-Transformationen als `matrix`, nicht als TRS; ein Leser ohne `matrix` liefert still falsche Lagen, nur die Gesamtmaße verraten es. [Roboter](robot.md)
