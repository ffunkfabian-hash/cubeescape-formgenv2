# Entscheidungen

| Datum | Entscheidung | Herkunft |
|---|---|---|
| 26.10.2026 | Eigenes Formgen-v2-Repo, Pythonmodelle in kit-Sprache und v1-Geo-Eingang | direkter Nutzerauftrag und [Auftrag](auftrag-codex-formgen-v2.md) |
| 26.10.2026 | Cache-Abnahme vor jedem ersten Rendering; Bild-, Layout- und Datenartefakte getrennt | Nutzerauftrag |
| 26.10.2026 | Lokaler Branch statt Remote-Reservierung, weil diese pushen würde | ausdrückliche Grenze kein Push/PR |
| 26.10.2026 | Aliasfelder und gemeinsame Meter-Netzschnittstelle | [Modellsprache](modellsprache.md), Implementierungsentscheidung |
| 26.10.2026 | Vier neue Orthos; gemeinsamer Frontmaßstab und Helmregistrierung; Frontgelenke/Fußhöhe verbindlich, Seiten Tiefe/Profil, Rücken Rückenmodul | direkte Nutzerkorrektur; [Herkunft](herkunft-roboter.md) |
| 26.10.2026 | Abnahmemaske stammt aus finalem Raster-Part-Buffer; gleicher Frame wie Farbbeleg | unabhängiger Prüfhinweis; RASTER4 |
| 26.10.2026 | Native W01- und Figuren-Geos als eigene explizite Namespaces; keine kollidierende KG-ID | v1-Schema schließt W01 aus; [Geo](geo-export.md) |
| 26.10.2026 | Legacy-Specs bytegleich ausgeben; interne Importpfade nur intern, exportierte Promptpfade relativ | SHA- und Paketprüfung |
| 26.10.2026 | Einhand-Low-Ready mit W01 als starre, gesonderte Pose; neutrale Abnahmekontur unverändert | Gestaltungsannahme; [Pose](robot-pose.md) |
| 26.10.2026 | Lokaler Checkpoint ausdrücklich nicht fertig; frische Sitzung statt Verlauf-Fork | globale Kontext-/Übergaberegel |
| 26.10.2026 | Breitenbänder messen mittlere äußere Zeilenspannweite einschließlich Zwischenräumen, alte Flächenquote bleibt Zusatzdiagnose | unabhängiger Messfehlerbefund; [Vertrag](robot-contract.md) |
| 26.10.2026 | Double-Präzision an beiden Manifold-Grenzen; komponentenweise Zweissegment-Fasen für konvexe Teile | 143 W01-Nullflächen durch Float32-Knotenkollaps; analytische Profil-/Solidtests; keine Blender-Gesamtparität |
| 26.10.2026 | Lokale Handinstanz 1,25 und Oberarmhüllen 32mm medial; Quelldicts und Gelenkachsen unverändert | Frontkonturvergleich; Maße/Annahmen in arms.PROVENANCE.ortho_instance_adjustments; Bildabnahme weiterhin erforderlich |
| 27.10.2026 | Konstante Ringextrusionen ohne Cuts mit echten Endringfasen; Bfont als statische Konturressource, Runtime ohne Fontparser/Blender | geometrische Gegenfälle und191FreeType-Datensätze geprüft; [Modellsprache](modellsprache.md), [Font](fonts/README.md) |
| 27.10.2026 | Legacy-Skins/Decals aus erhaltenem Spec mit Parent-/Normal-/Tiefenschutz; physische Seiten statt gleicher Mündungsrichtung vergleichen |24Rastertests und unabhängige KG02-Sichtung; [Raster](raster.md) |
| 27.10.2026 | Zusätzliche Legacy-IDs nur ausdrücklich per`--legacy-dir`; referenzierte Sight-Spec mitliefern, Standard weiterhin vier Piloten |159Datenroundtrips,0gebaut/636Treffer im zweiten Datenlauf |
| 27.10.2026 | Gemeinsame Konturfehler geometrisch korrigieren; zusätzliche Unterarmmasse am realen Schaftfreiraum begrenzen | Front-/Rücken-/Seitenmessung, alte Armkerne/Anker/Sohlen erhalten; Schaftabstand1,5mm |
| 27.10.2026 | Strenge vier IoUs und alle40Breitenbänder bleiben unverändert; aktueller Roboter nicht freigegeben |2/4IoUs,37/40Bänder; [Bericht](versions/0.1.md) |
| 27.10.2026 | SPEC4 verwendet Spec2-Zusatzfarben als color/share-Listen, flächengewichtete Dominanz und Glasfallback wie v1 | echter Toolgen-Palettenleser und analytischer Würfeltest; [Spec](figure-spec.md) |
| 27.10.2026 | Native Toolgen-Abnahme benötigt eine separate Abnehmeränderung; Formate und fehlende semantische Angaben nicht tarnen | unveränderter echter Abnehmer verweigert W01-/R01-Geos; Legacy-Weld beschädigt zwei native Netze; [Vorschlag](vorschlag-toolgen-native-contract.md) |
| 27.10.2026 | GEOM6 rekonstruiert nur nachgewiesene konstante Post-Cut-X-Extrusionen sowie eine rechteckige X-Minus-Blindtasche; andere variable Netze bleiben ausdrücklich unsupported | echte Volumendifferenz-, Topologie-, Loch-/Blindbodenprüfungen; lokale Offset-Ecken ohne bestätigte Blender-Miterparität |
