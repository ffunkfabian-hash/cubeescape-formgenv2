# R01: Ready mit W01

Status: **Entwurf, Bildabnahme offen.** Die vier Orthos definieren weiterhin den unveränderten Neutralstand. Ready ist eine zusätzliche Pose und verwendet dieselben Teile, Gelenke und Abmessungen. Kein Bauteil und keine Baugruppe wird neu modelliert.

## Geometrischer Vertrag

`r01_poses.build_poses(PARTS, ANCHORS)` liefert `idle` mit leeren Transformationen sowie `ready` mit starren 4×4-Matrizen in Weltkoordinaten (Meter; x links, y hinten, z oben). Nur die rechte Schulter-/Oberarm-, Unterarm-, Hand- und Fingergruppen erhalten Transformationen. Die linke Seite bleibt neutral. Die Schulter bleibt am gemessenen Anschluss; analytische Zweiglied-IK erhält die vorhandenen Ober-/Unterarmlängen 285,729/283,512 mm. Der Ellbogen-Pole `[0,-0.35,-1]` ist eine Gestaltungsannahme: unten und deutlich außen, damit der Schaft den Unterarm nicht kreuzt.

Das W01-Griffdatum liegt in Ready bei `[500,1320,-320]` mm in Autorenkoordinaten `(f,u,x)`. Die Waffe zeigt nach `+f`, mit waagerechtem Lauf rechts außerhalb des Rumpfes. Dies ist ein einhändiger Low-Ready-Entwurf; die linke Hand stützt die Waffe nicht. Alle Platzierungszahlen sind Annahmen, keine Messungen an den Zielbildern.

`hand_socket()` definiert `Socket_Hand_R` am tatsächlichen Griffdatum: lokal `[10,-37,55]` mm relativ zum vorhandenen rechten Handrahmen. Der bisherige Kardan-/Handgelenkursprung bleibt separat als `Socket_Wrist_R` erhalten. In Ready verläuft Hand-`+X` entlang Waffenhöhe, Hand-`+Y` nach außen und Hand-`+Z` nach vorn. Der Griff mit 30 mm Breite berührt so die unveränderte Handfläche; die vier Fingerreihen liegen entlang seiner Höhe.

Fortsetzung 26.10.2026: Die anhand der Frontkontur vergrößerte Handinstanz (Faktor1,25; Quelle unverändert) ersetzt das obige ursprüngliche Griffdatum durch `[12.5,-42.665,68.75]`mm. Der y-Abstand ist die skalierte halbe Handdicke plus14mm für den weiterhin30mm breiten W01-Griff; der nominelle Kontakt beträgt1mm. Sämtliche neutralen und posierten Finger-/Daumenabstände verwenden dieselbe Instanzskalierung. Die Posematrizen selbst bleiben starr, ohne Skalierung.

Nach der32mm medialen Oberarmhüllen-Korrektur überschnitt die Schaftkappe das Gehäuse um2,061mm³. Ein erster Korrekturversuch mit Ellbogen-Pole `[0,-.5,-1]` verschlechterte dies auf6,076mm³ und wurde verworfen. Die unabhängige Flächennormalen-/Rotationsdiagnose identifizierte den Oberarmroll als geeigneten Freiheitsgrad. Bei wiederhergestelltem ursprünglichen Pole `[0,-.35,-1]` zieht ein5°-Autorenrahmenroll (physisch entgegengesetzte Achsenrichtung) die Hülle zurück: Schnittvolumen0,0mm³, realer Mindestabstand1,510532mm. Schulter, Ellbogen, Wrist und Griffdatum bleiben unverändert; eine neue Abstandsprüfung verlangt mehr als1mm. Zweiter gezielter Korrekturdurchgang bestanden; keine dritte Sol-Runde.

Fortsetzung27.10.2026: Die unabhängig belegte20mm-Verbreiterung des medialen
Unterarmkerns berührte zunächst den Schaft. Eine SAT-Freiraumebene begrenzt
ausschließlich drei neue Stützpunkte (maximal5,904mm Rücknahme in X).
Alle24ursprünglichen Kernpunkte bleiben erhalten; eine konvexe Facette hält
1,5mm Abstand zum Schaft,3,133mm zur Schaftkappe. Ebene und Herleitung stehen
in`arms.PROVENANCE.fore_stock_clearance`. Gelenke, Pole und5°-Roll bleiben
unverändert. Der bestehende vollständige Waffen-/Körper-Schnitttest besteht.

Alle vier Finger verwenden die vorhandene Quellpose `SOURCE.FINGER_POSES['grip']` (62/74/48 Grad); der Daumen verwendet deren Werte 38/12/30 Grad einschließlich Abspreizung relativ zur neutralen 30-Grad-Lage. Die starren Glieder werden jeweils um ihre vorhandenen Gelenke bewegt. Der Zeigefinger berührt den Abzug, die Pose stellt deshalb keine abgesicherte Fingerstellung neben dem Abzugsbügel dar. Die Lage des Abzugs wird nicht erfunden: W01-Teil `trigger`, Profil etwa `f=43.25..51.25`, `u=15..41`, Breite 7 mm, liefert die Kontaktdaten.

## Einbindung

Der Roboter-Master installiert zuerst `ANCHORS['Socket_Hand_R'] = hand_socket()`, dann `POSES = build_poses(PARTS, ANCHORS)`. Die Ready-Definition referenziert W01 in `attachments`, mit Quellanker `Socket_Hand`, Zielanker `Socket_Hand_R` und einer Weltrotation von 3×3 Identität.

`evaluated_attachment(weapon_document, robot_document, 'ready')` platziert eine bereits ausgewertete W01 über beide Griffanker und liefert eine neue Kopie mit transformierten Netzen, Weltankern und aktualisierten Boundingboxen. Das Roboterdokument muss dabei **unposiert** sein, weil die Funktion selbst dessen Ready-Matrix auf den Zielanker anwendet. Die Funktion lädt keine Modelle nach und rendert nicht. Der Aufrufer verwaltet Cache-Abhängigkeiten und Präfixe für Teil-/Baugruppen-/Anker-IDs beim Zusammenführen. Autorenanker `at` bleiben Herkunftsdaten; `position_m` enthält die platzierte Weltlage.

## Prüfbelege und Grenzen

`tests/test_robot_pose.py` prüft unverändertes Idle, rechte Gruppenabdeckung, echte Bewegung, starre Matrizen ohne Skalierung, Schulteranschluss, Kette Schulter–Ellbogen–Wrist, alle Finger-/Daumengelenke, deckungsgleiche Waffen-/Hand-Sockets und unveränderte Eingabedokumente. Zusätzlich werden bei verfügbarem `manifold3d` echte Schnittvolumina ausgewerteter Netze geprüft:

- Kleine Schnittvolumina zwischen Griff und Handfläche/Mittelfinger/Daumen sowie zwischen Abzug und Zeigefinger belegen Kontakt. Diese bewusst erlaubten Kontakte sind keine physikalische Griffsimulation; lokale Durchdringungen sind im Bild zu beurteilen.
- Sämtliche W01-Teile bleiben ohne relevantes Schnittvolumen (`≤ 1e-10 m³`, numerische Toleranz) zu Rumpf, Kopf und rechtem Ober-/Unterarm. Hand-/Griffkontakt ist davon ausgenommen.

Die Tests verwenden echte Booleans, aber keine Fasen. Sie ersetzen keine Bildprüfung von Handgriff, Schaftfreigang, Gelenkhüllen und Pose. Ein MP4 ist nicht erforderlich: Hier wird eine statische zusätzliche Pose definiert, keine Animation und kein zeitlicher Ablauf.
