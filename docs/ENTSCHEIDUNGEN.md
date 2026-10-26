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
