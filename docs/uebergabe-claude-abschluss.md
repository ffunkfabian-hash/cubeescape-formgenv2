# Übergabe an Claude: Contour lokal abschließen

## Ergebnis der Claude-Abschlusssitzung (27.10.2026)

Entscheidung nötig. Schritte 1–5 unten erledigt, Schritt 6 (Browser) weiter offen.
Bildlauf `evidence/final-foot-acceptance/visual.json`: IoU Front 0,9401 /
Rücken 0,8859 / rechts 0,9038 / links 0,9010; 37/40 Bänder, Band 0 Rücken
1,097 / rechts 1,417 / links 1,425. Sichtprüfung ohne Befund am Fuß;
12 R01-Goldens aktualisiert; Paket CRC + 77/77 SHAs geprüft; `./check`
251 grün/17 Bildskips. Pflichtgates Rücken-IoU und Band 0 scheitern
unverändert an den dokumentierten Referenzkonflikten: keine Gesamtfreigabe.
Abschnitte unten sind der Stand VOR dieser Sitzung. Vorgemerkte Patches: Koplanartest auf alle Fußteile ausweiten; Fensterzahlen in `legs.py` aus `FOOT_ROWS` ableiten und PROVENANCE-Leerzeichen korrigieren (ändert den Quell-SHA, daher nicht in dieser Abnahme).
Details im [Versionsbericht](versions/0.1.md#fußabnahme-27102026).

Stand 27.10.2026. Frische Sitzung OHNE Fork/Verlauf. Opus mit Denkaufwand high für die heikle Geometrie-/Gesamtabnahme. Codex-Kontingent laut Nutzer fast leer; keine weiteren Codex-Unteragenten oder Codex-Prüfläufe einplanen. Diese Datei ist der aktuelle Arbeitsstand und hat Vorrang vor älteren Übergaben. Nicht fertig.

## Auftrag und Freigaben

Letzte fachliche Nutzeranweisung wörtlich: „Übernimm die geprüften GEOM8-Fasen, setze die Fußkorrektur gezielt fort und passe Toolgen erstmal nicht für die nativen Geometrien an. Stelle die Gesamtabnahme fertig, ohne zu pushen oder zu veröffentlichen.“ Danach ausdrücklich Übergabeprompt für Claude wegen fast leerem Kontingent verlangt.

- GEOM8 ist akzeptiertes W01-Fasenziel. Keine weitere Blender-Paritätsoptimierung.
- Gezielte Fußkorrektur ausdrücklich wieder freigegeben; der unten beschriebene neue Kandidat ist bereits integriert und unabhängig geometrisch geprüft.
- Native Toolgen-Anpassung zurückgestellt, kein Blocker dieses lokalen Abschlusses. Toolgen, v1, Ballon und Cube Escape nicht ändern; keine native Toolgen-Kompatibilität behaupten.
- Lokale Commits auf bestehendem Branch autorisiert. Kein Push, PR, Merge, Upload oder veröffentlichter Release. Keine Remote-Reservierung.
- Bestehende Originale, Registrierung, Gelenke und Bildgrenzen unverändert. Keine künstlichen Sohlen/Fahnen, Maskenfits oder stillen Grenzwertänderungen.

## Tatsächlicher Arbeitsort und Git

Repo `/Users/ffunk/Claude/cubeescape-formgenv2`, Branch `codex/formgen-v2-first`, letzter Commit `4d18986`. App-Arbeitsordner `/Users/ffunk/formgenv2` ist leer und falsch; dort nichts anlegen. Bei allen Befehlen explizit das echte Repo wählen.

Aktuelle Änderungen sind UNCOMMITTET und dürfen nicht verworfen werden:
`formgen/models/figures/r01_parts/legs.py`, neue `tests/test_robot_foot.py`, `out/specs/R01.spec.json`, `out/prompts/R01.prompts.json`, README, ENTSCHEIDUNGEN, LESSONS, geo-export, Versionsbericht und Übergabedokumente. `git status` frisch prüfen. Es gibt keinen neuen Commit dieser Sitzung.

Lesen: globale Regeln, Repo-AGENTS, LESSONS, diese Übergabe; dann gezielt ursprünglicher Auftrag, `docs/robot-contract.md`, `docs/herkunft-roboter.md` und `docs/versions/0.1.md`. Der Versionsbericht ist noch kein finaler Bericht des neuen Fußstands. Ältere Fuß-UNACCEPTED-Patches niemals über aktuelle Quellen kopieren.

## Integrierte Fußkorrektur

Aktueller legs-SHA256 `7dd61f27c48eae841d2b4e47981ad1ca7c92f0af564907df999c71aa1cf2acb8`. GEOM bleibt 8: nur Modellquelle geändert, der Sourcecache invalidiert R01 gezielt.

- Drei echte helle Zehen-/Spann-/Fersenschalen statt durchgehender Weißhaut mit dunkler Auflage; alte dunkle Auflage entfernt.
- Kanonische Dreiecke vor Spiegelung/Innenumkehr. Direkt konstruierter Kern aus derselben geteilten Außenhaut, 5-mm-Schalenwand und 0,25-mm-Montageabstand. Kein CSG-Rückimport als Fehlerpfad.
- Eine unabhängige Prüfung fand zunächst acht echte koplanare Fersenüberdeckungen, zusammen 186,8 mm². Bereits korrigiert durch konforme Zerlegung der benachbarten Domänen vor deren Union und Abschluss. Neuer Regressionstest reproduziert den alten Fehler und besteht jetzt. Keine Flächenlöschung oder Gateabsenkung.
- Beine jetzt 56 Teile / 4706 Vertices / 9228 Dreiecke. Gegen HEAD bleiben 48 Nicht-Fuß-/Sohlenmeshes, alle ANCHORS und FOOT_ROWS gleich. Beim letzten Fersenfix änderten sich nur die zwei Fersenschalen, 54 andere Beinteile gleich.
- Unabhängig geprüft: positive geschlossene Netze, exakte gespiegelte Vertex- UND Dreiecksgeometrie, alle Kern-/Panel- und Panel-/Panelpaare schnittfrei, echter Spec-/Geo-Roundtrip verlustlos, keine echten neuen Selbstschnitte. Numerische gemeinsame-Vertex-Fehlalarme der Floatprobe separat mit Decimal80 geprüft. Kein Gate verändert.
- Bestehende konstruktive Sohlen-/Schalenüberlappungen sind erhalten: nicht als vollständig durchdringungsfreien Gesamtfuß bezeichnen.
- Sichtbar zu prüfen: Spannplatte beginnt konstruktiv bei f20 statt gemessenen f8,43/f10,01. Explizit in PROVENANCE deklarierte Montageannahme, circa 6,5–7 % des sichtbaren Referenzfarbfelds betroffen. Keine vollständige Konturparität behaupten.

## Prüfungen und Belege

Alle folgenden Belege unter `~/Library/Caches/CubeEscapeFormgen/evidence/`:

- `final-foot-acceptance/foot-after-heel-independent-review.json`: maßgebliche finale unabhängige Geometriefreigabe, 20/20 gezielte Tests grün (3,364 s).
- `final-foot-acceptance/foot-coplanar-after-fix.json`, `self-intersection-after-heel-fix-decimal80.json`: kein verbleibender echter Fußselbstschnitt/keine koplanare Überdeckung.
- `robot/foot-canonical-fix/geometry-report-after-heel-union.json`, `heel-union-targeted-tests.log`: finaler Datenbeleg/20 Tests; Repros im selben Ordner.
- `final-foot-acceptance/original-foot-color-fields.json`: Originalfarbfeldmessung der Spannplatte.
- `final-foot-acceptance/baseline-independent-audit.json` und `ACCEPTANCE-CHECKLIST.md`: Baseline, Rohmetriken, minimale Restabnahme. Checkliste stammt von VOR Fußfix, Punkt 1 inzwischen erledigt.
- `before-foot-final/`: 40 alte Artefakte/Frames mit SHA-Manifest als Vergleichsbasis.

Quick VOR letztem Fersenfix: 250 Tests / 233 bestanden / 17 planmäßige Bildskips, 98,825 s; `/tmp/formgen-foot-final-quick.log`. Danach 20 gezielte Tests einschließlich neuer Fersenregression auf finalem Stand unabhängig grün. Quick nicht als vollständigen finalen Bildnachweis ausgeben.

Datenbau nach Fersenfix: vier Piloten, `--stages specs,prompts,geo`, 4 gebaut / 12 Cache; `/tmp/formgen-foot-final-data.log`. R01-Spec/Prompt sind dadurch neu. Abgelöst: `tests/golden.json` ist inzwischen aktualisiert (genau 12 R01-Hashes, andere Modelle gleich; siehe Ergebnis oben).

## Kein eigener Auftrag läuft mehr

Ein Bildlauf war nur in der GPU-Warteschlange und wurde zur Übergabe mit SIGINT sauber beendet (eigener PID 67704, Exit 130). Abgelöst: Die Claude-Abschlusssitzung hat den Bildlauf danach vollständig ausgeführt; `final-foot-acceptance/visual.json` liegt vor (siehe Ergebnis oben).

Fremder GPU-Lauf beim letzten Check: Blender PID 65370 seit 07:39:46, Ballon-Export. Nicht anfassen. Vor neuem Lauf `./ce lock status`. Alle Codex-Unteragenten sind beendet und beobachten nicht weiter.

## Nächste Schritte

1. Aktuellen Git-/Quellstand und obige finale Geometriebelege prüfen. Keine neue Fußgeometrie ohne konkreten Befund; Geometriekandidat ist bereits abgenommen.
2. Bestehenden vorbereiteten Bildprüfweg wiederverwenden: `/tmp/formgen-foot-final-visual.py` mit `/tmp/formgen-foot-final-visual-sources.json` (35 Quell-SHAs, bei Übergabe exakt passend). Er baut vier Piloten inkrementell zweimal, verlangt W01/KG02/VS02-Bildcache, prüft vier R01-Frames samt Masken aus denselben Frames, zwei cachefreie R01-Seeds, unveränderte Quellen/Referenzen und lokales ZIP. Kein `--force` und kein weiterer W01-/Blenderreferenzrender.

```sh
cd /Users/ffunk/Claude/cubeescape-formgenv2
./ce lock status
./ce lock gpu -- env PYTHONPATH=/Users/ffunk/Claude/cubeescape-formgenv2 /Users/ffunk/Claude/cubeescape-formgenv2/.venv/bin/python /tmp/formgen-foot-final-visual.py > /tmp/formgen-foot-final-visual.log 2>&1
```

3. Tatsächliche Bilder unabhängig sichten: Füße gegen beide Originalseiten/Front/Rücken, insbesondere f20, Figurenblatt/Baugruppe und Ready-Pose. Kontaktbogen mit bestehendem `./ce evidence sheet` bauen. Finaler Record wird `evidence/final-foot-acceptance/visual.json`, lokales ZIP unter `releases/final-foot-acceptance/`.
4. Rohe IoUs und alle 40 Breitenbänder unverändert beurteilen. Baseline: Front 0,9400816578; Rücken 0,8859483142; rechts 0,9037987026; links 0,9013198495. 37/40 Bänder bestanden; Band0 Rücken 1,097089134 / rechts 1,424522333 / links 1,431769045. Ziel je IoU >=0,90 und je Band 0,92..1,08. Neue Schalenteilung allein löst diese Silhouettenprobleme voraussichtlich NICHT. Seitliche Originalböden liegen bei gemeinsamer Registrierung rund 50 mm über verbindlichem Frontboden. Das ist ein konkreter Referenz-/Formkonflikt, KEIN Beweis genereller Unmöglichkeit; Front/Back-Band0 besitzen sogar einen gemeinsamen zulässigen Bereich. Keine Gesamtfreigabe erfinden oder Grenzwerte still lockern. Bei nötiger neuer Zielentscheidung den konkreten finalen Bildstand vorlegen.
5. Aktuelles Paket/CRC/alle SHAs unabhängig prüfen. Erst nach Bildsichtung relevante R01-Goldens aktualisieren; gezielte Goldenprüfung, `./check` vor lokalem Commit. Bericht/README/Übergabe auf tatsächlich erreichten Stand bringen. Kein Merge beauftragt, daher keine externe Codex-Mergeprüfung nötig.
6. Browserabnahme fehlt weiter. Frühere file-URL wurde sicherheitsverweigert: keine Umgehung über anderen Browser/localhost. Aktuelle CUA-Bestandsabfrage hatte keinen vorhandenen Viewer. Statische HTML-/Link-/Paketprüfungen sind grün, ersetzen aber keine Browserbedienung. Diese Grenze ehrlich nennen.

Ziel bleibt Gesamtabnahme, nicht bloß technischer Checkpoint. Falls unveränderte Pflichtgates scheitern, konkrete verbleibende Entscheidung mit Belegen melden; keine Übergabeschleife und keine weitere Codex-Sitzung wegen des knappen Kontingents starten.
