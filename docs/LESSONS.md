# Lehren

- Referenzbilder mit gleichem Pixelmaßstab an einer gemeinsamen Landmarke registrieren; kürzere gezeichnete Füße nicht durch Skalierung der gesamten Ansicht kompensieren. [Herkunft](herkunft-roboter.md)
- Bildbeleg und IoU-Maske müssen aus demselben Rasterframe stammen; ein zweiter Polygonzeichner kann abweichende Kanten produzieren. [Bericht](versions/0.1.md)
- Geschlossene Schalen allein verhindern keine Durchdringung: Innenkerne gegen die tatsächlichen Innenflächen und mit Schnittvolumen prüfen. [Bericht](versions/0.1.md)
- Bei Geo-Import Original-Specbytes erhalten, wenn Produzenten-Hashes weitergelten; kanonisches Neuschreiben verändert den SHA ohne semantische Änderung. [Geo](geo-export.md)
- Native Modell-ID nie als kollidierende Legacy-ID tarnen, um ein Schema zufriedenzustellen; Erweiterung als eigenen Vertrag kennzeichnen. [Geo](geo-export.md)
- Ein grüner Fixture-Release-Test ersetzt keinen Probelauf mit echten Artefakten: Schriften, verschachtelte Specs und absolute Pfade separat prüfen. [Geo](geo-export.md)
- Antialiasing-Tests prüfen die erwartete Sampleabdeckung, nicht willkürlich einen dunklen Einzelpixel. [Rastertest](../tests/test_raster.py)
- Layoutcache darf Rasterversion ignorieren, muss aber tatsächlich verwendete PNG-Größe/Callouts/Skalierung hashen; sonst bleiben Beschriftungen nach Größenwechsel veraltet. [Cache](cache.md)
