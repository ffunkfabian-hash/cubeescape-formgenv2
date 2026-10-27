# Frische Fortsetzung: GEOM6 integrieren, Contour fertigstellen

**Nicht fertig. Frisch ohne Verlauf/Fork fortsetzen.** Stand27.10.2026,02:25MEZ.
GEOM5/SPEC4 ist jetzt vollständig quick- und bildgeprüft; Code, Daten und
26neue Bild-/Blattgoldens werden im aktuellen lokalen Checkpoint gesichert.
Aktuellen HEAD/Status aus Git lesen. Keine älteren Checkpoints über Quellen
kopieren, nichts zurücksetzen oder fremden WIP verwerfen.

## Einstieg und Grenzen

- Tatsächliches Repo `/Users/ffunk/Claude/cubeescape-formgenv2`, Branch
  `codex/formgen-v2-first`. App-Projektwurzel `/Users/ffunk/formgenv2` ist falsch;
  dort nichts schreiben. Bei jedem Shell-/Git-Aufruf tatsächlichen Workdir setzen.
- Zuerst globale/Repo-AGENTS, docs/LESSONS.md, diese Übergabe,
  docs/versions/0.1.md und docs/auftrag-codex-formgen-v2.md lesen.
- Zwei Ziele bleiben W01-Geometrieparität und R01-/Systemabnahme.
  Gesamtsystem autonom fertigstellen; technischen Checkpoint nicht als
  Gesamtfreigabe oder erledigten Roboter ausgeben.
- gpt-6.1-sol/high für heikle Geometrie, Luna für Routine; keine Astra-Starts.
  Getrennte Unteragenten und unabhängiger Prüfer sind ausdrücklich gewünscht.
  Hauptagent hält Schnittstellen, VERSION-Konstanten, Integration und Commits.
- Lokale Commits erlaubt; kein Push/PR/Merge/Upload. v1/Ballon nur lesen.
  Keine neuen Pip-Abhängigkeiten, alten Modellmodule oder Cache-/Pipelinegerüste.
- Toolgen laut Auftrag tabu. Scopefrage ist im früheren Chat
  `01a17ac4-db0d-7610-ad7e-f2ae6fef1ec7` noch unbeantwortet; dort bei Bedarf
  direkte Nutzerantwort lesen, nicht erneut fragen/Schweigen als Freigabe nehmen.
  Geprüfter Vorschlag: docs/vorschlag-toolgen-native-contract.md.
- Browser-file-URL früher sicherheitsverweigert, keine Umgehung über anderen
  Browser/localhost. Statische Links-/Paketprüfung ist keine Browserabnahme.
- Kontingent zu Versionsbeginn bereits26%Wochenrest geprüft, nicht wiederholen.
  Vor Merge weiterhin externen `./ce codex judge` mit Checkliste fahren.

## GEOM5-Bildlauf ERLEDIGT, Quellenfreeze beendet

Der übernommene PID38556/Job `/tmp/formgen-geometry5-visual.py` ist erfolgreich
fertig, kein wartender/laufender eigener GPU-Auftrag mehr. KEINEN zweiten
GEOM5-Lauf starten. Nach1769sWarten lief er131,799s. Vor neuen Bildaufträgen
aktuellen `./ce lock status` lesen; fremde Halter niemals anfassen.

Record `~/Library/Caches/CubeEscapeFormgen/evidence/geometry5-spec4-visual.json`:
33gebaut/49Cachetreffer, danach0gebaut/82Treffer. KG02/VS02-Bilder waren Cache.
Vier registrierte R01-Farb-/Deckungsframes, zwei frische Frontprozesse Seeds1/42
mit exakt gleichen Geometrie/RGB/Deckungshashes und identischen Standardpixeln.
Alle34Quell-SHAs und vierOriginale/Referenzmasken bestätigt.
ZIP `releases/geometry5-spec4/formgen-v0.1.0-dry-run.zip` unter Cache:
4Modelle/77Nutzdateien+Manifest,7674136Bytes,
SHA256`0cc4ca1e19dde0e7483aee033fd53bc9943ff838b64f1fb9e04d7b3c2aecbfc7`.
Unabhängig CRC/Manifest/alleDatei-SHAs geprüft, keine Veröffentlichung.

Eigene UND unabhängige Sichtung: W01 side_left/hero/detail_trigger/sight_iso
mit freien Öffnungen und neuen Profilfasen, kein neuer sichtbarer Blocker.
R01 vierFarbbilder UND Overlays gesichtet; Metriken exakt unabhängig aus
Alpha derselben Frames reproduziert. **3/4IoUs und37/40Breitenbänder:**
Front0.9388799013943456, Back0.8848502633482926,
SeiteR0.9038583993313966, SeiteL0.9013795711982163.
NurBand0rot: Back1.0970891339721571, R1.4245223332911552,
L1.4317690448938063. Keine Rundung/Grenzwert-/Registrierungsänderung.
Fuß-/Bodenkonflikt bleibt: Seitenboden rund50mm höher als Front; Front legt
Gelenke/Fußhöhe/Standbreite fest. Keine künstlichen Sohlen/Fahnen oder
pauschale Fußverkleinerung zum Maskenfit. Keine Unmöglichkeitsbehauptung.

Belege unter Cache/evidence:
- `formgen-independent-geometry5-visual-review.json`,
  `formgen-geometry5-w01-visual-review.json`;
- `robot/registered-geometry5-spec4-contact.png` (1600px Kontaktbogen);
- `robot/legs-lower_body-upper_body-head-arms/{metrics.json,*-frame.png,*-overlay.png}`;
- alte GEOM4-Frames unverändert in `before-geometry5-spec4/`.
Vor Änderungen diese neue GEOM5-Bildbasis separat sichern.

## Tatsächlich integrierter Stand

GEOM5/RASTER5/SPEC4, W01:72Teile/10399V/20398T,0Nullflächen.
47segmentierteFasen,4Profilfasen(sight_body/grip/trigger/trigger_guard),
1Ringprofilfase(muzzle_crown),12ungefassteCut-Netze,8ohneFase.
Eigene Offset-Ecken sind KEINE bestätigte Blender-Miter-/Clamp-Parität.
Bfont, AUTO-Bezier und vierfrühereEndringfasen sind erledigt, nicht erneutTODO.
Legacy-Oberflächen vollständig integriert; alle159Legacy-Geos einzeln über
--legacy-dir wählbar/datengebaut/Geo-roundtripgeprüft, kein Bibliotheksrender.
SPEC4: Zusatzfarben wieder[{color,share}], dominant nach Oberfläche, Glasfallback
wie v1; echterToolgen-Palettenleser und159LegacySpecs geprüft.
NativeW01/R01Geos werden vom unveränderten Toolgen ausdrücklich abgewiesen.

R01:251Teile/18960V/36968T. Neue Schulterträgerdach-/Nackenkern-/konische
Hüftgehäusekorrekturen jetzt bildgeprüft. Anker/Füße/Armquellen unverändert.
Ready-Pose mit ursprünglichem Armkern und neuer konvexer ForeCore-Freiraumfacette:
keine W01-Schnitte, Schaftabstand1,5mm/Kappe3,133mm. Pose nicht blind korrigieren.

Letzter eigener `./check`:221Tests/204pass/17Bildskips,17,234s,
`/tmp/formgen-geometry5-final-check.log`. Vorheriger unabhängiger Quick grün.
Explizite Golden-Prüfung(ohne Render):3Tests/0,273s,
`/tmp/formgen-geometry5-golden-check.log`.26Bild-/Blattgoldens nachSichtung
aktualisiert; die3Datengoldens waren schon im vorherigen WIP aktualisiert.

## Nächste konkrete Etappe: geprüfte Vorschläge integrieren

Alle Vorschläge sind bislang NUR extern, NICHT im Repo angewandt.
Dauerhaft `~/Library/Caches/CubeEscapeFormgen/evidence/geometry/next-cut-proposal/`:

1. `formgen-next-cut-integration.patch`, SHA256
   `567a4f4d552f0469337f351b705463d04e192a4ed2dd24a7d2feff189e2a9875`:
   beliebig viele ungleichlange signierte Konturen; konservative echtePost-Cut-
   X-Extrusionserkennung; rail/stock_spine/stock/butt_pad mitProfilfasen.
   Toleranzmerge behebt echten Butt-Pad-Gegenfall4,44e-16rad, keineFlächenlöschung.
   Rücksprünge≤1e-12m ausdrücklich abgewiesen. BestehendeWrapper kompatibel.
   40gezielteTests und unabhängige Topologie-/Loch-/Projektionsprüfung grün.
2. DANACH `formgen-variable-pocket-integration.patch`, SHA256
   `b6fd1bd01893c99d4c49c89ca26f49baec6c06758d5336677ac8aebe8009dfc6`:
   echte rechteckigeX-Minus-Blindtasche inBox, nurbolt_carrier alsnativerPilot.
   Direktverbundene Außen/Mund/Wand/Boden/Eckpatches; bei2mmTiefe lokalerClamp
   0,98mm. NeuerStatussegmented_pocket_bevel/planar_pocket_chamfer, ehrlicheWarnung.
   Zusammen45Tests und unabhängigeProduktionscodeprüfung bestanden.
   Genau5weitereW01-Netze ändern sich, dann11895V/23390T; R01exaktidentisch.
   Weitere7Cut-Netze ausdrücklichunsupported, keineBlender-Paritätbehaupten.
   Berichte und independent-*-review/cases.json liegen imgleichen Ordner.

Separat `evidence/robot/next-arm-proposal/`:
`formgen-next-robot-arm-only.patch` ergänzt7aktiveHullstützen anupper_shell_*
bei u1350/+8mm.18Originalpunkte bleiben; spiegelgleich, f/u-Hülle/medialerRand
und Konturabu1450 erhalten. u1400-Stützen waren3D-redundant und entfallen.
LokaleWölbung ist in Front+Backfarbreferenzen und neuenFrames begründet.
Hauptagent hat geometrisch gleichenVorschlag nurinmemory eingesetzt:
alle6bestehendenPose-/Kontakt-/Kollisionstests grün(1,262s), aktuelleGEOM5W01.
BestehenderArm-Punktlistentest muss zusätzlicheStützen korrekt zulassen;
Originalpunktpräfix und vollständige f/u-Hüllengleichheit weiter prüfen.
Nach echterIntegration und neuerW01Geometrie gezieltePoseprüfung wiederholen.
Kein Materialpatch anwenden: Back zeigt helleSchienbeinrückseite, Seiten dunkle
Rückläufe. PauschalerRollenwechsel ist nichtvierfachbelegt; Materialalternative
bleibt in eigenemBericht offen. Knieänderung war nicht begründet.

Hauptagent: beideGeom-Patches inReihenfolge prüfen/anwenden, Armpatch gezielt,
GEOMauf6 setzen, passendeDoku nachführen. Datenbau nurvierPiloten, neueDaten-
Goldens, Quick+gezieltePrüfung; genauEIN gezielterinkrementellerBildauftrag
unterGPU-Sperre mitneuemQuellsnapshot. Eigene/unabhängigeBildsichtung,
neueMaskenwerte, Bildgoldens undlokalerCommit. Nicht erneutPipelinebauen.

## Restgeometrie nicht vortäuschen

lower: vierrechteckigeTaschen beidseitig sind post-Cut-exakt rekonstruiert,
aber zweiMünder überschneiden die unveränderte5mm-Außenfase: EndcapZ81mm,
Mundoberkante82,735mm, je35,984624mm² außerhalb; schon ungefast20mm² außerhalb.
Pocketradius-Verkleinerung allein löst es nicht. KEINlower-Netz/Diff gebaut.
`formgen-lower-pocket-{report.md,check.json,preflight.py}` bei next-cut-proposal.
Echte übergreifende Ecklösung/ausdrücklichbegründeterClamp erforderlich,
kein heimliches Modell-/Breitenändern. AndereRestteile upper/top_shroud/
magazine/handguard/barrel/muzzle besitzen variableQuerschnitte oder schräge
Flächen; kein einzelnes2D-Profil, keinekonvexeHülle alsFormersatz.

Alle bisherigenUnteragenten beendet. Die abgebendeSitzung koppelt sich ab;
keine weiterenSchreiber oderBeobachter, Fortsetzungfrisch ohneVerlauf/Fork.
