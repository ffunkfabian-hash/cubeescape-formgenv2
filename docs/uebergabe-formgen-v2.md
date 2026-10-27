# Formgen v2: GEOM8 und offene Gesamtabnahme

**Nicht fertig. Stand 27.10.2026.** GEOM8/RASTER5/SPEC4 ist integriert,
quick-, golden- und bildgeprüft. Keine alten Patches erneut anwenden und keine
Checkpoints über aktuelle Quellen kopieren. HEAD und Arbeitsbaum aus Git lesen.

## Einstieg und Grenzen

- Tatsächliches Repo `/Users/ffunk/Claude/cubeescape-formgenv2`, Branch
  `codex/formgen-v2-first`. App-Projektwurzel `/Users/ffunk/formgenv2` ist falsch:
  dort nichts schreiben oder initialisieren. Shell/Git immer mit explizitem Repo-Workdir.
- Zuerst globale/Repo-AGENTS, `docs/LESSONS.md`, diese Datei,
  `docs/versions/0.1.md` und `docs/auftrag-codex-formgen-v2.md`; vor langen Dokus suchen.
- Zwei Ziele: W01-Geometrieparität und R01-/Systemabnahme. Technischen
  Zwischenstand nicht als Gesamtfertigstellung melden.
- Sol/high für heikle Geometrie, Luna für Routine, kein Astra. Getrennte
  Unteragenten und unabhängige Prüfer ausdrücklich gewünscht; Hauptagent hält
  Schnittstellen, VERSION, Integration und Commits. Keine gleichzeitigen Schreiber.
- Lokale Commits autorisiert; kein Push/PR/Merge/Upload. v1/Ballon nur lesen,
  Toolgen tabu. Keine neuen Pip-Abhängigkeiten oder Cachegerüste.
- Frühere Browser-file-URL sicherheitsverweigert: keine Umgehung über anderen
  Browser/localhost. Statische Paketprüfung ist keine Browserabnahme.
- Kontingent zu Versionsbeginn bereits 26 % Rest geprüft, nicht wiederholen.
  Erst vor ausdrücklich beauftragtem Merge externen `./ce codex judge` + Checkliste.

## Integrierte GEOM8-Korrektur

W01: 72 Teile / 14842 V / 29284 T, 0 Nullflächen, alle 64 Fasenaufträge
im Standard-2-Segment-Modell ausgewertet, 8 Teile ohne Fasenauftrag.
Genau sieben Netze gegenüber GEOM7 geändert: upper/lower/top_shroud/magazine/
handguard/barrel/muzzle. Alle übrigen W01-Netze und sämtliche R01-Netze gleich.

Bisher klemmte das Post-Cut-BRep jede Kante unabhängig; Blender begrenzt den
Auftrag gemeinsam. GEOM8 übernimmt das Minimum aller bisherigen konservativen
0,24-Abstandsgrenzen als gemeinsame Breite. Die unveränderten Bedingungen
flacher Ecken dürfen weiter reduzieren. Keine IDs, Quellmaße, Cuts, Hüllen oder
Flächenlöschung als Anpassung. Alle positiven Quellen-/Topologie-/Nullflächen-/
Selbstschnitt-/Überlappungsgates bleiben zwingend.

`bevel_diagnostics` und Warnung zeigen gemeinsamen Clamp, effektive Spanne und
weitere Reduktionen: lower weiterhin 5 mm Vorgabe, jetzt überall 0,36 mm;
Handschutz gemeinsam 0,72 mm, vier Kanten bis 0,719486293 mm reduziert.
upper mit vier Segmenten ist nun tatsächlich gültig (1084 V / 2164 T), positiv
und geschlossen; separater Fehlerweitergabetest hält `unsupported` ehrlich.

Alle sieben symmetrischen Volumendifferenzen zu denselben echten Blender-
5.2.2-Referenznetzen sinken. Maximal 0,499 % statt 2,292 %, Bounds maximal
0,083772 statt 0,728651 mm; Handschutz 5079,862 → 1105,247 mm³.
**Keine exakte Blender-Miter-/Clamp-Parität.** Konservativer Grenzwert und eigene
Eckpatches weichen weiter ab. Separat analysierter Original-Triangle-Kollaps
liefert Handschutz 1,68180449 mm und Magazin 0,570829946 mm; der bestehende
Handschutz-Eckalgorithmus scheitert aber schon bei gemeinsam 1,5 mm.
Nicht blind diesen größeren Grenzwert übernehmen. Tube-Ringtransport bleibt
ebenfalls dokumentiert abweichend. Kein neuer Blenderlauf.

Externer integrierter Patch unter `evidence/geometry/global-clamp-proposal/`,
SHA256 `b54e5afeefa992e07d01ac2127caf3ec2c5b56c1db62603414e79302c1040f59`.
Versionierte Primärquelle und SHA-Provenienz unter
`evidence/geometry/blender-postcut-reference/bmesh_bevel-v5.2.2.*`.
Unabhängiger CPU-Record `geometry/formgen-independent-geometry8-global-clamp-review.json`.

## Abgeschlossene aktuelle Prüfungen

- 17 gezielte Geometrie-/Poseprüfungen grün, 10,721 s; unabhängige elf
  Proposaltests und erneute sieben Referenzberechnungen grün.
- `./check`: 247 Tests / 230 bestanden / 17 planmäßige Bildskips, 63,578 s.
  Zwei W01-Datengoldens geändert; Vierpilot-Datenbau 8 gebaut / 8 Treffer.
- Ein inkrementeller Bildlauf 111,658 s: 31 gebaut / 51 Treffer, danach 0 / 82.
  Alle 35 Quell-SHAs stabil. Zwei cachefreie W01-Seeds 1/42 geometrisch,
  RGB und Deckung exakt gleich und Standardbild pixelgleich.
- Eigene und unabhängige Bildsichtung gegen GEOM7 und vier echte Ballon-Stills:
  keine neuen Bildblocker. Acht W01-Ansichten und R01 Ready/Front/Back geprüft.
  R01 Front/Back pixelgleich; Ready 2654 geänderte Pixel an der Waffe.
- Erst danach 14 Bild-/Blattgoldens angepasst. Goldencheck ohne Render:
  drei Tests / 0,255 s. Logs `/tmp/formgen-geometry8-{targeted,quick,visual,golden-check}.log`.
- Keine weitere GEOM8-Aufnahme starten. Kein eigener schwerer Auftrag läuft
  oder wartet; vor einem neuen Job `./ce lock status`, Fremdes nicht anfassen.

Alle folgenden Pfade unter `~/Library/Caches/CubeEscapeFormgen/`:
`evidence/geometry8-spec4-visual.json`, `evidence/formgen-geometry8-visual-review.json`,
`evidence/geometry/formgen-independent-geometry8-visual-review.json`,
`evidence/geometry/geometry8-vs7-w01-contact.png`,
`evidence/geometry/geometry8-w01-orthos.png`. GEOM7-Basis 38 Dateien +
SHA-Manifest unter `evidence/before-geometry8/`; frühere Belege unverändert.

Lokales ZIP `releases/geometry8-spec4/formgen-v0.1.0-dry-run.zip`:
77 Nutzdateien + Manifest, 7771427 Bytes,
SHA256 `de813973efea5e0006fa444613ca580b05c1e10f47dc8aab1185d6611787caae`.
Unabhängig CRC und alle 77 Datei-SHAs geprüft;
`evidence/formgen-independent-geometry8-package-review.json`. Keine Veröffentlichung.

## Erhaltene R01- und Systemgrenzen

R01 GEOM7-Kopffix und GEOM6-Oberarmwangen bleiben erhalten:
251 Teile / 19106 V / 37268 T. Keine R01-Netzänderung, Ready-Pose/Anker/Sohlen
unverändert, alle sechs Poseprüfungen grün. Bfont/AUTO-Bezier/Legacyoberflächen/
159 Legacy-Geos/SPEC4 sind erledigt, nicht erneut TODO.

R01 rohe IoUs unverändert: Front 0.9400816578075649, Back 0.8859483142429271,
R 0.9037987025908385, L 0.9013198495013238. Weiter 3/4 IoUs und 37/40 Bänder;
nur Band0 rot: Back 1.0970891339721571, R 1.4245223332911552,
L 1.4317690448938063. Front bestimmt Gelenke/Fußhöhe/Standbreite;
Seitenboden rund 50 mm höher. Keine künstlichen Sohlen/Fahnen, Maskenfits,
Rundung/Grenzwert-/Registrierungsänderung oder Unmöglichkeitsbehauptung.
Keine unbelegte pauschale Knie- oder Schienbeinrollenkorrektur.

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
