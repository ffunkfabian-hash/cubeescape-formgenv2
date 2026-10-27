# Frische Fortsetzung: GEOM7 sichern, R01-/Systemabnahme fertigstellen

**Nicht fertig. Ohne Verlauf/Fork frisch fortsetzen.** Stand27.10.2026.
GEOM7/RASTER5/SPEC4 ist vollständig quick-, golden- und bildgeprüft; alle
folgenden Geometriepatches sind JETZT integriert. Nichts erneut anwenden,
keine alten Checkpoints über aktuelle Quellen kopieren. HEAD/Status aus Git lesen.

## Einstieg und Grenzen

- Tatsächliches Repo`/Users/ffunk/Claude/cubeescape-formgenv2`, Branch
  `codex/formgen-v2-first`. App-Projektwurzel`/Users/ffunk/formgenv2` ist falsch:
  dort nichts schreiben/kein Git initialisieren. Shell/Git immer mit explizitem
  tatsächlichem Repo-Workdir.
- Globale/Repo-AGENTS, docs/LESSONS.md, diese Übergabe, docs/versions/0.1.md und
  docs/auftrag-codex-formgen-v2.md zuerst lesen; vor langen Dokus suchen.
- Zwei Hauptziele bleiben W01-Geometrieparität und R01-/Systemabnahme.
  Gesamtsystem autonom fertigstellen, technischen Checkpoint nie als fertig melden.
- Sol/high für heikle Geometrie, Luna Routine, keine Astra-Starts. Getrennte
  Unteragenten und unabhängige Prüfer ausdrücklich gewünscht. Hauptagent hält
  Schnittstellen/VERSION/Integration/Commits. Keine gleichzeitigen Schreiber.
- Lokale Commits autorisiert; kein Push/PR/Merge/Upload. v1/Ballon nur lesen,
  Toolgen tabu. Keine neuen Pip-Abhängigkeiten/Cachegerüste/alten Modellmodule.
- Browser-file-URL war sicherheitsverweigert, keine Umgehung über anderen
  Browser/localhost. Statische Paketprüfung ist keine Browserabnahme.
- Kontingent am Versionsbeginn26%Rest bereits geprüft, nicht wiederholen.
  Erst vor ausdrücklich beauftragtem Merge externen`./ce codex judge`+Checkliste.

## Tatsächlich integrierter Stand

GEOM7/RASTER5/SPEC4. W01:72Teile/14842V/29284T,0Nullflächen.
47segmentierte+8Profil-+1Ringprofil-+1Taschen-+7Polyhedral-BRep-Fasen,
8Teile ohne Fasenauftrag, KEIN unsupported im Standard2Segment-W01.

Die früheren externen next-cut/variable-pocket/next-arm-Patches sind schon in
GEOM6 integriert. Jetzt zusätzlich `formgen/polybevel.py` plus geom-Routing:
alle7variablen/schrägen PostCut-Restteile upper/lower/top_shroud/magazine/
handguard/barrel/muzzle mit echten Flächen-/Kanten-/Eckpatches. Quellmaße/Cuts
unverändert, keine Hülle oder fertige Nullflächenlöschung. Zwingende Gates
auf positive geschlossene Quelle, Nullflächen, Selbstschnitt/koplanare
Überlappung; Qhull/LinAlg gezielt GeometryError. Ungültige höhere Segmente
bleiben ehrlich unsupported (z.B.upper3/4). Maschinenlesbare Diagnostics und
Warnungen zeigen konservative tatsächliche Setbackspannen. lower5mm-Vorgabe
bleibt, obere Außenkante0,96mm, Taschenmund/Boden0,36mm.

Keine bestätigte Blender-Miter-/Clamp-Parität: echter Blender5.2.2-Kern auf
denselben7PostCut-Netzen zeigt0,038–2,292% symm.Volumendifferenz und maximal
0,729mmBoundsabweichung. Referenz ohne Render in eigener Hintergrundszene
unterBlenderlock,0,031sCPU; keine .blend gespeichert. DatenbauW01 gemessen
1,125→6,454s durch zwingendes Selbstschnittgate. Geometriecache unverändert.

R01:251Teile/19106V/37268T. GEOM6-Oberarmwange7aktiveStützen jeSeite,u1350/+8mm;
Originalpunktpräfix/f-u-Hülle/medialerRand/Anker erhalten. GEOM7-Kopffix:
_wall trianguliert Außen-/Innenflächen einmal korrespondierend; Hinterkopfplatte
symmetrisch mit denselben9Originalpunkten/4mmf-Wand. Dunkles Housing lokal gegen
wirkliche Panelinnenfläche ausgenommen. Frühere schwarze Insel ist verschwunden;
12Kopfnetze geändert, Kopf-Ränder/Symmetrie/Innenwände unabhängig geprüft.
40841innerePanelstrahlen0Verdeckung,0Schnitt;3exakteRandstrahlen tangieren
benachbartesGehaeuse. SeitlicheFläche40,2157mm²kleiner, Front/Backmaske identisch.

Ready-Pose/Anker/Sohlen unverändert. Bestehende6Poseprüfungen grün; frühere
tatsächlich gefaste W01-/Roboter-Kollisionsprüfung Schnitt0. Keine Pose blind
korrigieren. Bfont/AUTO-Bezier/Legacyoberflächen/159LegacyGeos undSPEC4 sind
bereits erledigt; nicht erneutTODO. Native Abnehmergrenze bleibt offen.

## Neue Bild-/Prüfbasis, abgeschlossen

KEIN eigener wartender/laufender GPU-/Blenderauftrag, Quellenfreeze beendet;
vor neuem Bildjob echten`./ce lock status` lesen, fremdeJobs niemals anfassen.
Keinen zweiten GEOM7-Bildlauf starten. Ein inkrementeller Lauf116,428s:
31gebaut/51Treffer, danach0gebaut/82Treffer, Legacybilder gecacht.
35Quell-SHAs unverändert;2cachefreieSeedprozesse1/42RGB/Deckung/Geometrieexaktgleich
undStandardfront pixelidentisch. Keine Referenz-/Masken-/Registrierungsänderung.

R01 roheIoUs: Front0.9400816578075649, Back0.8859483142429271,
R0.9037987025908385, L0.9013198495013238. Weiter3/4IoUs und37/40Breitenbänder.
NurBand0rot: Back1.0970891339721571, R1.4245223332911552, L1.4317690448938063.
Front bestimmt Gelenke/Fußhöhe/Standbreite; Seitenboden rund50mmhöher. Keine
künstlichen Sohlen/Fahnen, Maskenfits, Rundung oder Grenzwertänderung. Keine
mathematische Unmöglichkeit behaupten. Material-Rollenwechsel anSchienbeinrücken
bleibt nicht vierfachbelegt; Kniekorrektur unbegründet.

Eigene UND unabhängige Sichtung W01siebenAnsichten/Ballonoriginale und R01vier
Farben/Overlays/Kopfcrops abgeschlossen, keine neuen Bildblocker.22Bild-/Blatt-
Goldens danach aktualisiert. ./check244Tests/227pass/17Bildskips72,546s,
42gezielteTests29,092s; Golden3Tests0,254sOHNERender. Logs
`/tmp/formgen-geometry7-{targeted,quick,visual,golden-check}.log`.

Belege unter`~/Library/Caches/CubeEscapeFormgen/evidence/`:
- geometry7-spec4-visual.json, formgen-geometry7-visual-review.json,
  formgen-independent-geometry7-visual-review.json;
- geometry/formgen-independent-geometry7-w01-visual-review.json,
  geometry/formgen-independent-brep-{production-review,adversarial,edge-locality,blender-comparison}.json;
- robot/registered-geometry7-spec4-contact.png,
  robot/geometry7-head-comparison.png, formgen-independent-geometry7-head-frame-crops.png,
  robot/legs-lower_body-upper_body-head-arms/{metrics.json,*-frame.png,*-overlay.png};
- geometry/remaining-geometry-proposal/formgen-remaining-polyhedral-report.md,
  ProduktionspatchSHAf983b22f32003a75740f675faca208f3cffed01c2a9cc1b665c6e493968ce91d
  ist BEREITS integriert. Gegen40c169d genau7W01Netzänderungen;
- geometry/blender-postcut-reference/{input.json,reference.json,blender_reference.py};
- before-geometry7/44Dateien+SHAmanifest alsGEOM6Basis, before-geometry6/GEOM5Basis.

ZIP imCache`releases/geometry7-spec4/formgen-v0.1.0-dry-run.zip`:
77Nutzdateien+Manifest/7782721Bytes,
SHA52ede7726dae90e5e59c327849989b1420c6f9871a09104cea602889feff0a5a.
UnabhängigCRC/alle77Manifestdatei-SHAs bestätigt. KeineVeröffentlichung.

## Zwei offene Nutzerentscheidungen nicht dupliziert fragen

1. Fußprototyp gemäß Korrektur-Obergrenze PAUSIERT. In abgebendemChat
   `01a17af7-5bf7-7dd1-846e-3dad6643014f` steht asynchroneFrage: nach unabhängiger
   Ursachenprüfung ausnahmsweise mitSol/xhigh gezieltfortsetzen oder vorerst
   zurückstellen. Vor abhängigemFußcode direkteNutzerantwort dort lesen,
   keineAntwortistKEINEFreigabe. Astra bleibtgesperrt. Frage nichtduplizieren.
2. ToolgenScopefrage imfrüherenChat`01a17ac4-db0d-7610-ad7e-f2ae6fef1ec7` noch
   unbeantwortet. BeiBedarf direkteAntwortlesen, Toolgennichtanfassen.
   docs/vorschlag-toolgen-native-contract.md istechtergeprüfterAbnehmervorschlag:
   W01/R01Namespacesverweigert, LegacyWeld/Doppelbevel und optionaleAngaben
   brauchenMigration. Kein bloßesAllowlisting/ID-Umtarnen.

## Fußvorschlag: echte offene Formabweichung, KEIN integrierbarer Patch

BeideSeitenoriginale zeigen getrennteToe-/Spann-/Heel-Schalen, sichtbaren dunklen
Mittelfuß unddunklesFersenmittelfeld. AktuelldurchgehendeweißeHalbschalen/glatte
Sohle sindabweichend. Extern`robot/remaining-robot-proposal/REPORT.md` mit
Kontaktbogen,3gesichertenQuellständen,Repro+Logs undUNACCEPTED-Patches.
BesterPrüfstart`legs_first_complete_proposal.py`SHA
484c74258e0eb77b2dfb3c19398d62f38082bdc74c4df7a49f2f07737c7753f4:
58Beinteile/4488V/8760T,15/16AltTestsgrün,alle6PoseTestsgrün. ABERzusätzlicher
neuerSpannschalentest5,848974/5,733212mm³Schnitt undechteAsymmetrie.
NichtbloßunterschiedlicheTessellierung: _shell drehtnichtplanareQuads VORdem
Fan/Clipping, wähltbeimSpiegeln andereDiagonalen(Quadsbis7,029mmnichtplanar).
SpätesterStand`legs_proposal.py`enthältzusätzlichnegativeCore−0,005853874m³
beidseitigwegenfalschemPauschalFaceReverse. NICHTblindanwenden/reparieren.
UnabhängigerRecord`formgen-independent-geometry6-foot-rootcause-review.json`.
Wegen3×SymmetriebefundkeinevierteRundevorNutzerentscheidung. Instep-Reimport-
Differenzseparatbelegt: nativeCSG vsMesh64ReimportändertVolumenexaktumschädliche
Schnittmenge; Außen/Innen-Diagonalendieser3neuenPanelswarenbereitskorrekt.

AlleUnteragentenbeiÜbergabebeendet; keineweiterenSchreiber/Beobachter.
QuellekoppeltsichnachZustellungab. NurfrischeneueSitzungohneVerlauf/Fork.
