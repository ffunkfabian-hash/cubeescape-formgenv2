# Bfont-Konturen

`bfont-contours.json` enthält abgeleitete Konturbefehle, Advances und Bounds
für druckbares ASCII und Latin-1 (191 Zeichen, davon 189 sichtbar).
Quelle ist Blenders eingebettete [Bfont-PFB aus v5.2.0](https://github.com/blender/blender/blob/v5.2.0/release/datafiles/bfont.pfb),
25181 Bytes, SHA256
`a33954fdab9fb09b9d308cb7f970518293128922ffc523c0a22b3b314a9a56c6`.
Blender registriert diese Ressource in
[creator.cc](https://github.com/blender/blender/blob/v5.2.0/source/creator/creator.cc).

Die einmalige Extraktion verwendete FreeType aus dem bereits vorhandenen
Pillow-Paket. Der normale Bau liest ausschließlich die statische JSON-Datei;
die Geometrie benötigt numpy und das vorhandene manifold3d. Der Font-Info-Satz
meldet Bfont Regular 001.001 und `Notice=null`. Ein eigenständiger PFB-
Lizenzhinweis ist in den geprüften Upstream-Angaben nicht belegt; Herkunft und
dieser offene Status stehen auch in der Ressource.

Unterstützt sind eine Zeile, Standardabstände, LEFT/CENTER/RIGHT und die drei
kit-Seitenrichtungen. Basis ist die Grundlinie. Die tatsächlichen Bfont-
Metriken verwenden Blenders Fallbackmaßstab 1/1000. `size` und `depth` werden
in Autorenmillimetern übergeben; die Extrusion reicht von −depth bis +depth.
Kurvenauflösung 12 entspricht dem Curve-Default in
[DNA_curve_types.h](https://github.com/blender/blender/blob/v5.2.0/source/blender/makesdna/DNA_curve_types.h).
Float64-Sampling beansprucht keine identische Blender-float32-Tessellation.

Alle Glyphbefehle und Metriken wurden einmalig gegen FreeType geprüft;
die normalen Tests prüfen die statische Ressource, Polynomextrema, Löcher,
geschlossene Netze, Ausrichtung und Grenzen ohne Fontparser-Abhängigkeit.
Der Geometriecache und die Worker-Quellprüfung binden den Ressourcen-SHA ein.
