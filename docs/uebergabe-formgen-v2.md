# Frische Fortsetzung: Contour fertigstellen

**Nicht fertig. Frisch ohne Verlauf/Fork fortsetzen.** Stand27.10.2026.
Diese Etappe wird als geprüfter technischer Codecheckpoint lokal committet.
Aktuellen HEAD/Status aus Git lesen; keinen alten Checkpoint zurückspielen.

## Einstieg und Grenzen

- Tatsächliches Repo `/Users/ffunk/Claude/cubeescape-formgenv2`, Branch
  `codex/formgen-v2-first`. App-Projektwurzel `/Users/ffunk/formgenv2` ist falsch.
- Zuerst `~/.codex/AGENTS.md`, Repo-AGENTS, `docs/LESSONS.md`, diese Datei,
  `docs/versions/0.1.md`, vollständigen `docs/auftrag-codex-formgen-v2.md` lesen.
- Sol/high für große/heikle Geometrie, Luna für Routine; keine Astra-Starts.
  Unteragenten gezielt und dateigetrennt, unabhängiger Prüfer ohne Umsetzung.
  Hauptagent hält Schnittstellen, Versionen und Commits.
- Lokale Commits autorisiert; kein Push/PR/Merge/Upload. v1/Ballon nur lesen,
  keine alten Modellmodule/eng-Sprache übernehmen, keine neuen Pipabhängigkeiten,
  kein Cache-/Pipelinegerüst neu bauen.
- Zwei verbleibende Hauptziele: W01-Geometrieparität und R01-/Systemabnahme.
  Gesamtsystem weiter autonom fertigstellen; technischen Checkpoint nicht
  als Zielerfüllung oder freigegebenen Roboter ausgeben.

## Aktueller implementierter Stand

- GEOM4/RASTER5, SPEC3. Mesh64 behebt143W01-Nullflächen. Konvexe Komponenten
  mit Zweissegmentfasen; vier konstante Ringextrusionen mit echten Endringfasen.
  AUTO-Bezier-Mittellinien resolution12; Ringtransport/Tessellation abweichend.
- W01:72 Teile/9605 Vertices/18810 Dreiecke,0 Nullflächen;47 segmentierteFasen,
  17weiterhinungefast,8ohneFase. Echte Bfont-Schrift ersetzt Rechtecktafel.
  Statische191ASCII-/Latin1-Zeichen,189sichtbar; Runtime JSON/numpy/manifold3d.
  Herkunft/Scope/PFB-Notice=null: `docs/fonts/README.md`. Font-SHA wird in
  nativer Geometrieplanung und Worker-Guards berücksichtigt; Ressourcencache
  aktualisiert sich bei geänderten Bytes auch im selben Prozess.
- Legacy-Oberflächen sind JETZT integriert und bildgeprüft, kein Helfer-TODO:
  aufgelöste Hero-Lagen, normale Decals/Glyphen/Trim/Wear, Parent-/Tiefen-/
  Normalenschutz, keine neue flache Geometriedeckung, Parent-Annotationen.
  Detailauswahl filtert entfernte Parents. Normale muss zur Kamera und mit
  dot>0,5 zur Parentnormalen zeigen (neue v2-Schutzregel). Katalog-SHA in
  allen Legacy-Ansichts-/Previewkeys, auch VS02ohneSkin.
- KG02Orangeband undGlyphen aufBEIDENphysischenSeiten/Hero vorhanden. Gleiche
  Mündungsrichtung v1/v2 kann physische Seiten vertauschen! v2side_left(+X)
  entspricht v1LEFT(old+z), auch bei entgegengesetzter Bildhändigkeit.
  KeineGlyphenspiegelung zum Screenshotfit einbauen.
- Alle159 Legacy-Geos über `--legacy-dir ~/Library/Caches/CubeEscapeFormgen/imports/v1`
  einzeln perID wählbar. Benötigte Sight-Specs kommen über vorhandene Stufen
  mit, ohne zusätzliche Visierbilder/Geo. Ohne IDs bleiben vier Piloten.
  Alle159Datenbau/Geo-Roundtrips geprüft:636 gebaut, danach0 gebaut/636 Treffer.
- FigureGeo→Spec-Roundtrip/Validator repariert; Legacy-Specbytes unverändert.
  NativeW01-/Figure-Geos sind eigene Namespaces, Toolgen-Abnahme noch offen.

## W01-Restgeometrie

Ungefasste IDs/Grundform/Cutanzahl:
`upper prof8`, `lower prof4`, `top_shroud prof4`, `bolt_carrier box1`,
`rail box7`, `sight_body prof0`, `grip prof0`, `trigger prof0`,
`trigger_guard prof0`, `magazine prof7`, `handguard plan7`, `barrel cyl4`,
`muzzle cyl8`, `muzzle_crown cyl0`, `stock_spine box3`, `stock prof1`,
`butt_pad prof6`.
Vier sichere Endringteile sind erledigt, NICHT erneut als TODO behandeln:
shroud_bracket/core_ring/sight_frame_trim/handguard_cap. Muzzle_crown ist
achteckig mit45°-Längskanten und benötigt zusätzliche Längsfasen/Eckmiter.
Allgemeine konkave Fasen nicht durch konvexe Hülle/Flächenlöschen vortäuschen.
Vor neuem Algorithmus gezielt Quelle/Tests lesen, analytisch prüfen, dann nur
betroffene W01-Ansichten unter Ressourcensperre bauen. Keine pauschalen Render.

## R01: neuer tatsächlicher Bildstand

251 Teile/18872 Vertices/36792 Dreiecke. Vier4096²-Orthos in
`~/Library/Caches/CubeEscapeFormgen/refs/`, gemeinsamer Frontmaßstab1924/3653 mm/px,
Helmregistrierung. Front legt Gelenke, Standbreite und Fußhöhe fest; Seiten
Tiefe/Profil, Rücken Rückenmodul. Keine Einzelbildnormalisierung/Maskenfits.

Aktuelle unabhängige Werte aus denselben Farb-/Deckungsframes:
Front0,9350187; Rücken0,8811756; SeiteR0,9024968; SeiteL0,8998656.
**2/4 IoUs und37/40 Breitenbänder bestanden.** SeiteL nicht auf0,90aufrunden.
NurBand0(0..192,4 mm)rot: Rücken1,097089, Seiten1,424522/1,431769.
Alle übrigen37 Bänder bestanden. Bilder/Overlays/metrics.json:
`~/Library/Caches/CubeEscapeFormgen/evidence/robot/legs-lower_body-upper_body-head-arms/`.
Kontaktbogen `evidence/robot/registered-geometry4-raster5-contact.png`.

Erledigte, gemessene Korrekturen dieser Etappe:
- Schulterkappen bäuchiger Verlauf statt pauschaler Verbreiterung; Taille
  beiu1220halbbreit126 mm. Anschluss/Kragen, F/U-Profile/Anker erhalten.
- Oberarmhüllen X0,79 um bestehende mediale Hüllenachse; unveränderte F/U.
  ForeCore bis20 mm medial ergänzt, alte24Punkte/Außen-/Seitenprojektion erhalten.
- Knie hinten echte5 mm-Schale, vorderer Knieschild ergänzt; Fußrücken/Zehen nach
  beiden Seiten erweitert,3 mm-Spannbelag folgt echter Oberfläche. Frontkontur
  der Beine an4608Höhen analytisch identisch; Gelenke und Sohlen unverändert.
- Handmaßstab1,25, Source-Dicts/SHA d713339e… und Frontachsen unverändert.
  Ready-Pole−0,35 und5°Oberarmroll erhalten. Neue ForeCore-Masse berührte den
  Schaft; durch unabhängig gemessene konvexe Freiraumfacette NUR drei neue
  Stützpunkte begrenzt. Alle Originalpunkte bleiben; Schnitt gegen alle
  W01-Teile0, Schaftabstand1,5 mm, Kappe3,133 mm. Keine neue Rollkorrektur!

Wichtiger Restbefund, nicht blind korrigieren:
Seitenboden liegt bei Helmregistrierung rund50 mm über Frontboden. Oberhalb
beider Bodenlinien ist die Fußbreite nun fast gleich(.9924/.9788); der große
Band0-Wert entsteht vorwiegend durch3415/3562Modellpixel unter Referenzboden.
Pauschal Fuß verkleinern ist dadurch NICHT begründet. Rücken zeichnet Beine/
Füße enger; Front-/Back-Modellmasken sind korrekt gespiegelt exaktgleich,
Zielmasken untereinanderIoU.897458. Noch4068fehlende und3973überschüssigePixel
gegenBEIDEReferenzen zeigen gemeinsame geometrische Verbesserungsmöglichkeiten.
Keine mathematische Unmöglichkeit behaupten; ein theoretischer Maskenkompromiss
ist noch keine zulässige Geometrie. Keine künstlichen Sohlen/Fahnen zum Bandfit.

## Prüfstand und Belege

- `./check`:202 Tests/185pass/17 Bildskips,39,796 s,
  `/tmp/formgen-geometry4-raster5-check.log`.
- Tatsächliche24 Rastertests(8 Kamera/Material,16Pixel)grün unter GPU-Lock. Vollständiger Vierpilotbau
  62 gebaut/20 Treffer, Wiederholung0 gebaut/82 Treffer.
- Abschlussrecord `~/Library/Caches/CubeEscapeFormgen/evidence/integrated-geometry4-raster5.json`.
  Drei angeforderteKG02PNG sindpixelgleich zum unabhängig gesichteten Prototyp.
  Ein Prüfskript erwartete fälschlich optionalesiso.png im Standardblatt;
  Dateivergleich korrigiert, kein vollständiger Neu-/Doppelrender nötig.
- 66 Golden-Hashes aktualisiert als technischer Entwurf, keine Designabnahme.
- Lokales ZIP4 Modelle/77 Nutzdateien+Manifest,7634889 Bytes,
  SHA42f6026eb315273ff6a081c992ec884ab882a2ba1e23b756a0cbe97ee4cc568b.
  Pfad `~/Library/Caches/CubeEscapeFormgen/releases/formgen-v0.1.0-dry-run.zip`.
- Cachefreie R01-Pixelprobe zwei frische Prozesse Seeds1/42 vor der letzten
  Modellkorrektur gleich; nicht als neuen Nachweis des letzten Modells ausgeben.
- Keine eigenen GPU-Jobs mehr. Fremde Ironsight-Aufträge nicht anfassen;
  vor neuen Bildjobs echten`ce lock status` lesen. Keine Queue duplizieren.
- Browserabnahme offen: früherefile-URL-Sicherheitsverweigerung, keineUmgehung
  durchanderenBrowser/localhost. StatischePaket-/LinkprüfungistkeineFreigabe.
- Kontingent zuVersionsbeginn bereitsgeprüft(26%Wochenrest); nicht routinemäßig
  erneutprüfen. VorMerge weiterhin vorgeschriebenenexternenJudge fahren.

Alle bisherigen Unteragenten beendet, keine weiteren Schreiber. Die abgebende
Sitzung beobachtet die Fortsetzung nicht. Fortsetzung frisch, nie Fork/Verlauf.
