# Frische Sitzung: Contour fertigstellen

**Nicht fertig. Frisch ohne Verlauf/Fork fortsetzen.** Stand26.10.2026,23:24MEZ.
Der Arbeitsbaum enthält bewusst noch uncommittete, geprüfte Implementierung;
Git lesen und diese Arbeit erhalten. Nur diese Übergabe/Versionsbericht werden
als Dokucheckpoint committet, solange der neue Bildbeleg noch aussteht.

## Ort und vollständiger Auftrag

- Tatsächliches Repo `/Users/ffunk/Claude/cubeescape-formgenv2`, Branch
  `codex/formgen-v2-first`. App-Projektwurzel `/Users/ffunk/formgenv2` ist falsch.
- `~/.codex/AGENTS.md`, Repo-AGENTS, `docs/LESSONS.md`, diese Datei,
  `docs/versions/0.1.md` und vollständigen `docs/auftrag-codex-formgen-v2.md` lesen.
- Lokaler Codecheckpoint vor dieser Fortsetzung84d8714. Seither WIP-Dateien
  NIEMALS zurücksetzen oder überschreiben. Kein fremder Schreiber aktiv.
- Sol/high für große/heikle Geometriearbeit, keine Astra-Starts. Unteragenten
  gezielt, Baugruppen getrennt; unabhängiger Prüfer ohne Implementierung vor
  jeder Nutzermeldung. Hauptagent hält Schnittstellen/VERSION/Commits.
- Lokale Commits autorisiert, kein Push/PR/Merge/Upload. Ballon/v1 nur lesen,
  159Legacy-Modelle nur Geo, keine alten Modellmodule. Gesamtsystem fertigstellen.

## Unveränderte Referenzregeln

Vier4096²-Orthos in `~/Library/Caches/CubeEscapeFormgen/refs/`, gleicher
Frontmaßstab1924/3653mm/px und gemeinsame Helmregistrierung. Keine einzelne
Höhennormalisierung, kein Spiegel-/Maskenfit. Front bestimmt Gelenke/Fußhöhe/
Standbreite, Seiten Tiefe/Profil, Rücken Rückenmodul. Quellen/Anker in
`docs/herkunft-roboter.md` und `docs/robot-contract.md`.
Seitenboden liegt bei gleicher Registrierung49,5/50,6mm über Frontboden;
Frontpriorität bleibt erhalten. Rückenbeinstellung enger als Front. Nicht
pauschal mathematische Unmöglichkeit behaupten; theoretischer Maskenkompromiss
könnte beideIoUs bestehen, ist aber noch keine zulässige Geometrie.

## Geprüfte Implementierung im WIP

- GEOM3: Mesh64 Ein-/Ausgabe behebt143W01-Nullflächen ursächlich. Konvexe
  Komponenten einzeln mit2Kreisprofilsegmenten und konservativem Clamp.
  W01:72Teile/7777Vertices/15166Dreiecke,0Nullflächen;43segmentierteFasen,
  21konkave weiterhinungefast,8ohneFase. `requirements>=3.5.4` passendLock.
- `formgen/curves.py`: AUTOBezier nach verifiziertem Blender5.0.1-Handlecode,
  resolution12, in geom.tube integriert;6analytischeTests. Ringtransport und
  Tessellation weiterhinabweichend, echte Textglyphen/Eckmiter offen.
- R01:249Teile/18502Vertices/36060Dreiecke. UpperBody: Schulterlücke durch
  offene6mm-Kappen/Blenden und hohlen Kragen geschlossen. Arme: Hüllen32mm
  medial, Hände lokal1,25 inklFinger/Daumen/Frames. SOURCE-Armdicts bytegleich,
  alle Frontgelenke unverändert. Neue Bilder NOCH NICHT ausgewertet.
- Ready: skalierte Handdatumsabstände, GRIP[12.5,-42.665,68.75]. Fehlversuch
  Pole-.5 verworfen, Original-.35 wiederhergestellt. Unabhängig begründeter
  Oberarmroll5° um gleiche Knochenachse:0mm³ Kontakt/1,510532mm Abstand.
  Alle6Posetests grün. Zweiter Korrekturdurchgang erfolgreich, kein dritter.
- `tools/robot_evidence.py` prüft jetzt mittlere ÄUSSERE Zeilenspannweite pro
  Band; alte Flächenquote zusätzlicheDiagnose. Neue2Tests, gleiche Grenzwerte
  .92..1.08. Alle vier Masken unabhängig pixelgleich reproduziert, OriginalSHAs
  bestätigt. Alte Bandwerte sind keine Breitenabnahme.
- SPEC3: FigureGeo→Load→Spec-Roundtrip repariert; neuer Validator für bestehenden
  FigureSpec1-Vertrag. Echte W01/R01-Roundtrips/SHA/Deepcopy unabhängiggrün.
  Datenzweitlauf0gebaut8Treffer. Vier DatenGoldens aktualisiert, BildGoldens ALT.
- Letztes abgeschlossenes `./check`:143Tests/134pass/9Bildskip,33,328s,
  `/tmp/formgen-contour-refined-check.log`. Neuer eingefrorener Check inklLegacyhilfe:155Tests/146pass/9Bildskip,37,688s,
  `/tmp/formgen-contour-handoff-check.log`. Ein anschließend ergänzter
  Parent-Overlaytest wird durch den gezielten13Helpertests-Lauf abgedeckt.
  Kontingent einmal23:11MEZgeprüft:Wochenrest26%, kein5h-Fenster.

## Neu erkannte Legacy-Darstellungslücke und klarer nächster Schritt

KG02v2 fehlen in BEIDEN Seiten Orangeband/Glyphen; Gegenkamera erklärt es nicht.
Geo enthält63normaleDecals, source_spec.skin.hero zusätzliche44Glyphen und
aufgelöste Farb-/Finish-/Musterlagen. `raster.py` ignoriert sie bisher.
Generische Objektraumtexturen existieren, keine falsche Aussage 'gar keine'.
Beleg aus vorhandenen Rasterpanels, ohne neuen Render:
`~/Library/Caches/CubeEscapeFormgen/evidence/comparison/kg02-v1-v2-panels.png`,
Quellen/SHA im dortigenJSON. BallonW01SideReferenz:
`~/Library/Caches/CubeEscapeBallon/out/BASIC-01-v2.1/views/side_left.png`.

- Fertiger, unabhängig geprüfter Helfer `formgen/legacy_surface.py`,
  `tests/test_legacy_surface.py` (13Tests) +Cachetest (1) grün. Noch NICHT
  in raster.py integriert; Rasterdatei weiterhin bytegleich84d8714, RASTER4.
- Bytegleicher v1Finishkatalog `docs/textures/catalog.json`, SHA3691845e6b1683861deb075bb6056a40c5e1f6a9457007d449f8a643dc7f8fb6,
  ProvenienzREADME. Keine Schwesterimports/neuePipabhängigkeit/Modellimporte.
- API: resolve(document,skin)→Surface oderNone fürnative; Surface.shade,
  render_parts(),parents(),parent_visible(),decorations(),wear(). Quellachsen(-Y,Z,X), festeMetereinheiten, ParentIDs,
  fünfLayerfamilien, Glyphen/Trim, Finishleitern/Wear analytischgeprüft.
  Zwei unabhängiggefundene Brushed/Knurl-Achsenfehler sind behoben.
- Hauptagent hat in build.view_parameters Legacy-KatalogSHA für ALLE v1Geos
  ergänzt, auch VS02ohneSkin, Hashguard PNG+Preview. Test: Katalogänderung
  invalidiert nurLegacyviews/previews, nichtnative oderSpecs/Prompts.
- ALS NÄCHSTES Rasterhelfer integrieren: sichtbareWeltposition/Normal/Level/
  Part-ID-/Geometrie-ID-Puffer, normale/Glyph-Decals mit Parent-Z-Test und
  Normalenrichtung, keine neueDeckung außerhalb Elterngeometrie; Wear darf
  Decalkanten nicht wie Modellkanten behandeln. NativePixelpfad erhalten.
  Danach RASTER5 und gezieltePixeltests/KG02Vergleich unterGPU-Sperre.

## EIN eigener GPU-Job: erhalten und zuerst beobachten

Es gibt jetzt entgegen alter Übergabe EINEN wartenden eigenen Job:
PID14579 (`heavy_lock.py`, exakteCommand mit ps prüfen), Toolsession13278.
Er wartet auf fremden Ironsight-ExportPID11101 (NICHT anfassen).
Command: Nexogen-ce lock gpu --what 'Formgen Contour gezielte Bildabnahme'
→env PYTHONPATH=/Users/ffunk/Claude/cubeescape-formgenv2
→Repo/.venv/bin/python `/tmp/formgen-contour-visual-run.py`.
Log `/tmp/formgen-contour-visual-run.log`.

Das eigene Skript hat einen Mac-Spawn-Guard und führt nach Erhalt der Sperre aus:
1. Vier registrierte R01Frames/evidence und neue IoUs/Breitenbänder.
2. Inkrementeller vollständiger Bau NUR geänderter W01/R01, jobs2.
3. Zwei unabhängige frische R01Front960px-Prozesse (Seeds1/42), KEIN Pixelcache,
   Hash von RGB undDeckungsmaske; JSON unter
   `~/Library/Caches/CubeEscapeFormgen/evidence/robot/fresh-pixel-determinism.json`.

Bis zum Ende dieses Jobs KEINE Raster-/Modell-/Geom-/Specquellen ändern, sonst
würden Frames und Cacheversionen inkonsistent. Keine zweite gleicheQueue.
Legacyhilfe/Tests sind noch unintegriert und beeinflussen diesen Lauf nicht.
Danach Farbframes/Overlays selbst und unabhängig sichten, echte neue Zahlen
melden; vorher gelten NUR alteIoUs Front.8817/Back.8272/Seiten.8785/.8753.

## Rest und Abschluss

- Roboter weiterhin nicht abgenommen (vierIoUs≥.90 und neueBreitenbänder).
- W01konkaveFasen/Font/Eckmiter offen. Sinnvoller nächster Geometrieschritt:
  fünf konstante Ringextrusionen ohneCuts statt globalemBevelneubau; Näheres
  Versionsbericht/Runtimewarnings. Keine blindenFit-/Korrekturschleifen.
- Viewer/HTMLBrowserabnahme fehlt: vorheriges Browserwerkzeug verweigertefileURL
  perSicherheitsrichtlinie, keinUmgehen durchanderenBrowser/localhost.
  StatischeLink-/Paketsichtung und Rasterpanelvergleich sind keineBrowserfreigabe.
- Legacy159 extern vorbereitet, Registry4Pilotmodelle; nichtallesungerufenrendern.
- Alter lokaler ZIP-Probelauf4Modelle/77Dateien und66GoldenHashes gehören zum
  vorherigenCheckpoint, nach aktuellen Änderungen kein finalerReleasebeleg.
- VorCodecommit neuerBildbeleg, `./check` undgezieltePrüfung; Dokumente/Version/
  LESSONS aktuellhalten. Code bewusst WIPbisneuerBildprüfung. KeinPush/PR/Merge.
- Alle alten Unteragenten werden an dieser Etappengrenze beendet/nichtbeobachtet;
  frischeSitzung spawnt gezielte neue Helfer und unabhängigen Prüfer selbst.
