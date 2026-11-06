# RoboterBasic-02 – Zuordnung und Abnahme

> Integriert in 0.11 als Blatt `RA02` ([Bericht](../versions/0.11.md)). Dieser Text ist der Abnahmebericht von Codex auf Basis `cf294c4` (0.9) und nennt den Stand vor der Integration. Modellname: RoboterBasic-02.

## Quelle und Rechte

Ausschließlich `robot_v2.blend`, SHA256 `67a350c19aec60241c86d0b2b0937469960d06c52422275844dcb8a24400d578`. 20.904.428 Bytes, Blender 5.2.2 LTS, Frame 1. Nur headless mit `--factory-startup --disable-autoexec` unter `ce lock blender` gelesen, nie gespeichert; keine eingebetteten Skripte ausgeführt. `robot_v2.blend1`/`robot_v3.blend` nicht geöffnet. Hash, Größe und Änderungszeit unverändert.

Nutzerbestätigung im Auftrag vom 05.11.2026: **„Die sind alle von mir – mit nano image banana erstellt“**. Damit ist der zunächst offene Herkunftsbefund durch eine direkte Nutzerangabe geklärt; dies ist keine aus der Blend-Datei abgeleitete Lizenzbehauptung. Referenzbilder, Shader, Studio, Quellskripte und Rig werden nicht mitgeliefert. Keine Critic-Verbindung und kein fremdes Repo im Build.

Die Quelldatei enthält 629 Objekte: 614 Meshes, 5 Empties, 3 Kameras, 6 Lichter, 1 Armature. ROBOT umfasst 554 Meshes und 2 Hand-Empties. 57 Cutter, 2 kantenbasierte Guides, Studiogeometrie und Referenzen sind Hilfen. 58 Bones, 0 Actions; 6 zyklische Damped-Track-Paare an Knie-/Knöchelkolben. Diese Constraints werden nicht übernommen.

## Maße und Koordinaten

Metrische Einheit mit `scale_length=1`: Blender-Einheit = Meter. Genau einmal `f=-1000*Y`, `u=1000*Z`, `x=1000*X`; Front −Y, anatomisch links +X. Boden u=0 (Quellenrest −0,0000022 mm ist Gleitkommarundung).

| Maß | Quelle mm | Formgen Referenzhaltung mm | Formgen A-Position mm |
|---|---:|---:|---:|
| Höhe | 1848.919751 | 1848.919750 | 1848.919750 |
| Breite | 883.877873 | 843.877880 | 1445.815514 |
| Tiefe | 497.176960 | 497.176960 | 506.751538 |

Nutzerkorrektur nach Sichtung: vorhandene Schultern und Arme je20mm nach innen; keine zusätzlichen Stege. Damit ist die Breite in der Referenzhaltung exakt 40 mm geringer als die Quelle, Höhe/Tiefe unverändert. In dieser Haltung haben Kappen und Brust je über 34.000 mm³ echten Kontakt. Die breitere A-Position entsteht durch die geöffneten Arme und ist kein Maßvergleich gegen die geschlossenen Quellarme. Die Kappen berühren den Brustpanzer auch in der A-Position. Hauptkonstanten: HEIGHT, SHOULDER_WIDTH (Abstand Oberarm-Drehpunkte, nicht äußerste Panzerbreite), ARM_LENGTH (Ober-/Unterarm zusammen), LEG_LENGTH (Ober-/Unterschenkel zusammen), HEAD_SIZE (Helmhöhe). Maße aus Weltgeometrie bzw. Bone-Endpunkten. Abhängige Positionen laufen über PARAMS und gemeinsame Segmentrahmen.

## Aufbau und Parametrisierung

Modul: `formgen/models/robot/roboterbasic_02.py`, lokale Daten: `roboterbasic_02_shapes.json`. Liefert INFO, PARTS, ASSEMBLIES, ANCHORS, POSES, PARAMS, REFERENCE_PARAMS, DATA_FILES und `document(params, sheet_id, line, name)`. Lädt mit `model.load` und `geom.evaluate` ohne Blender, Netz oder Quelldatei. Kein automatischer Registereintrag.

Nach dem am 05.11.2026 nachgereichten Stand `cf294c4` entsprechen zehn Einzelteile mit `group`/`group_de` den vier Baugruppen von 01: `head`; `upper_body` mit `upper_body`/`pelvis`; `arms` mit `shoulders`/`upper_arms`/`forearms`/`hands`; `legs` mit `thighs`/`shins`/`feet`. Alle 15 Socket-Namen bleiben erhalten. Das interne Messarchiv behält seine ursprünglichen fünf Quellkategorien für die Profilkalibrierung; ausgegebene Dokumente verwenden ausschließlich den neuen 10/4-Vertrag. `spec.build` führt gemessene Teile unter `measured_parts`. IDs nutzen das bestehende Muster `arm_R_…`, `thigh_L_…`, `torso_…`, `pelvis_…`, `helmet_…`. Quelle→ID ist unten vollständig aufgelistet. Eltern sind Daten aus der Bone-Hierarchie, nicht Blender-Parenting zur Laufzeit.

197 linke Teile werden aus der rechten Messung gespiegelt (beidseitiger Punktabstand ≤0,002 mm); Flächenwindung wird mitgespiegelt. Andere linke Teile bleiben explizite Messungen, siehe Asymmetrien. Es gibt keine zweite handgeschriebene linke Figur.

Alle 01-PARAMS-Schlüssel sind vorhanden: skeleton, arm_bulk, pose, head, upper_arm, torso, pelvis, legs, arm_drop. Der lokale Profiladapter nutzt dieselben body/arm-Konstruktoren wie 01 und kalibriert deren Referenzprofile auf gemessene 02-Familien. Zubehör folgt der gemessenen Eltern-/Bone-Zuordnung; Schalter bauen oder entfernen reale Teile. Geänderte Lüftungsschnitte werden aus einer gesondert gemessenen Vor-Boolean-Basis neu aufgebaut, damit alte Löcher wirklich geschlossen werden. Keine Blender-Runtime. Eigene Hauptmaßsteuerung dimensions.height/shoulder_width/arm_length/leg_length/head_size. arm_bulk wirkt wie im 01-Standard auf Unterarmteile; der separate Oberarm folgt upper_arm, Hände/Finger bleiben unskaliert. Die zwei schon in 01 unbenutzten Felder chest.tip/plate erzeugen bei Änderungen eine sichtbare Warnung (parameter-vorschlag.md).

Grundhaltung ist jetzt die A-Position wie im aktuellen 01: `A_ANGLE=40°`, `A_ELBOW=4°`, `A_FORE_Y=-0.08` als Vorgabe01/Entwurfsannahme. Rumpf/Kopf werden gerade gesetzt; die aus der Quelle gemessene individuelle Fußbreite bleibt erhalten. `pose.shoulder_open` dreht die Kappen spiegelgleich um das Schultergelenk, `40° - HANG_02 = 32.316°`; die Winkelkonvention entspricht 01, der gemessene Ausgangswinkel unterscheidet sich. `REFERENCE_PARAMS` hält die gemessene Quellhaltung mit der gewünschten engeren Schulterstellung fest (`origin=gemessen`, `shoulder_open=0`). Die Referenzmessung verwendet nur diese Haltung, wie docs/robot.md es für die Abnahme vorschreibt. Hauptmaße und Parameterbezeichnungen bleiben erhalten. `INFO.joints` enthält gemessene Drehpunkte und ausdrücklich angenommene Winkelgrenzen als Daten; POSES enthält nur idle, keine Bewegungsfreigabe.

## Geometrie, Formen und Rückfälle

Quelle: 89.892 Basisdreiecke, 244.979 nach Modifiern. Formgen: 554 Teile, 260247 Dreiecke in Referenzhaltung und 264549 Dreiecke in A-Position. Die unterschiedliche Tessellierung entsteht durch die gedrehten Boolean-Eingaben; Teile-IDs und Formenanzahl bleiben gleich. Primitive/Cuts werden aus gemessenen konvexen Hüllen und vollständigen gleichzähligen Ringschnitten aufgebaut, Materialvolumenprüfung 0,01 %. Ganze Figur ist keine surface.

| Form | logische Teile | inklusive Unterformen/Cuts |
|---|---:|---:|
| hull | 298 | 432 |
| loft | 18 | 34 |
| multi | 42 | 42 |
| surface | 196 | 201 |

**199 logische Teile enthalten surface-Rückfälle** (einschließlich gespiegelter Gegenstücke). Das ist eine erhebliche Einschränkung des Nachbaus, ausdrücklich keine vollständige Rekonstruktion aller Quelloperatoren als analytische Formen. Jede Ausnahme ist unten mit Name und Grund aufgeführt. Insbesondere bei Hohlpanzerung entstehen Solidify→Bevel→Cut-Folgen und ungleichzählige Profile, die das vorhandene Kit nicht verlustfrei abbildet. `model.py`/`geom.py` bleiben unverändert.

Nullvolumen-Gegenflächen an den Quellsohlen entfernt: keine Verringerung eines Tests, sondern dokumentierter Quellfehler. Nur exakt deckungsgleiche Dreieckspaare wurden beidseitig entfernt. Das schließt die betreffende Topologie; Außenmaße bleiben unverändert.

## Abnahme gegen die Quelle

Verglichen wird ausdrücklich `document(REFERENCE_PARAMS)`, nicht die ausgelieferte A-Position. Die gewünschte engere Schulterstellung betrifft auch die Arme. Deshalb fällt der isolierte Arm-IoU deutlich niedriger aus; die Gesamtfigur besteht die unveränderte Abnahme. Keine separate Baugruppenfreigabe mit IoU≥0,90 behauptet.

Identische orthografische Kameras, 1000 px/m, keine Streckung, zehn feste Höhenbänder; Grenzwerte unverändert IoU ≥0,90, Breite 0,92–1,08. Referenz-Renderbilder mit demselben Formgen-Rasterizer, Kamerarahmen und Skin weiss_graphit auf Mittelgrau, ohne Bloom. Quellbilder nutzen die gemessenen ausgewerteten Originalnetze; sie sind keine Neufassung der Quelle.

| Ansicht | IoU | Band min | Band max | bestanden |
|---|---:|---:|---:|---|
| front | 0.9283 | 0.9490 | 1.0000 | True |
| back | 0.9283 | 0.9491 | 1.0000 | True |
| side_right | 1.0000 | 1.0000 | 1.0002 | True |
| side_left | 1.0000 | 1.0000 | 1.0002 | True |

| Baugruppe | Teile | Dreiecke Referenz | Dreiecke A | schlechtester Referenz-IoU |
|---|---:|---:|---:|---:|
| head | 31 | 39802 | 39802 | 0.9989 |
| upper_body | 83 | 26063 | 28035 | 1.0000 |
| arms | 292 | 139602 | 140648 | 0.7356 |
| legs | 148 | 54780 | 56064 | 0.9999 |

| Einzelteil | Teile | Dreiecke Referenz | Dreiecke A | schlechtester Referenz-IoU |
|---|---:|---:|---:|---:|
| head | 31 | 39802 | 39802 | 0.9989 |
| upper_body | 63 | 20591 | 22563 | 1.0000 |
| pelvis | 20 | 5472 | 5472 | 1.0000 |
| shoulders | 48 | 29186 | 29484 | 0.7816 |
| upper_arms | 30 | 9700 | 10448 | 0.7523 |
| forearms | 14 | 6468 | 6468 | 0.7482 |
| hands | 200 | 94248 | 94248 | 0.4156 |
| thighs | 50 | 18656 | 20020 | 0.9992 |
| shins | 72 | 23648 | 23568 | 0.9998 |
| feet | 26 | 12476 | 12476 | 1.0000 |

Belege außerhalb des Repos: `outputs/robot-basic-02/vergleich.png`, `roboterbasic-02.png` (A-Position), `a-position-front.png`, `referenzhaltung.png`, `stance.json`, `comparison.json`, `attachment-probe.json` im Arbeitsauftrag. Keine Blätter, GLBs, Blends oder Renderbilder im Commit.

## Geometrischer Tausch 01 → 02

71 Teile der rechten 01-Armkette (`arm_R_*`, ohne den individuellen 01-Schulterpanzer) an Socket_Shoulder_R gesetzt. Alle 02-Körperteile einschließlich seiner eigenen Schulterkappen, aber ohne seine auszutauschenden Armketten, sind Gegenkörper. Geprüft sind beide Haltungen: aktuelle A-Position und REFERENCE_PARAMS. Vorher 8 Durchdringungen; dafür Freiraumtaschen an den Schulterteilen aus gemessenen konvexen 01-Gelenkformen mit **0,25 mm angenommenem Spiel pro Raumachse**. Keine fremde Quelle: verbindliches 01-Muster im selben Repo, Stand b721daf. Das ist eine benannte konstruktive Abweichung innen gegenüber robot_v2. Zusätzlich wurden fünf Freiraum-Hüllen des aktuellen 01-A-Arms (cf294c4) mit demselben 0,25-mm-Spiel invers in die gemessenen 02-Schulterrahmen übertragen. Das behebt fünf nachgewiesene A-Haltungs-Durchdringungen; es gibt keine Sonderlogik je Teil oder Haltung. Cuts sind Daten und folgen den Parametern ihres Empfangsteils; interface_clearance markiert sie unabhängig von Zierfugen, damit Profil-Neubauten sie erhalten.

Nachprobe in beiden Haltungen: jeweils 0 Überschneidungen über 1 mm³, 0 Boolean-Fehler, Socket-Abstand 0 mm. Nachweis ist statisch für die rechte Armkette, kein Lauf-/Animations- oder Waffenanbindungstest.

Kopftausch ist **nicht freigegeben**: 01-Hals dringt in Brust/Kern ein (8 nachgewiesene Überschneidungen); außerdem 10 nichtmannigfaltige Boolean-Eingaben im 01-Helm in Referenzhaltung (9 in A-Position). In A-Position ebenfalls 8 Überschneidungen. Halsquerschnitt und Anschlusstiefe unterscheiden sich. Geschütztes 01-Modell nicht geändert. Die identischen Socket-Namen allein garantieren keinen Kopftausch.

## Annahmen, Grenzen und Integration

- Eigentums-/Herkunftsangabe: direkte Nutzerbestätigung, keine in der Datei enthaltene Lizenz.
- Schulterposition: direkte Nutzeranweisung, je20mm Innenversatz als Entwurfsannahme; keine zusätzlichen Verbindungsstücke. Kappen berühren nun den Brustpanzer. Gelenkgrenzen, idle-Benennung, Explosionsversätze, Spiegel-Toleranz 0,002 mm, Messrundung 0,00001 mm sowie 0,25-mm-Freiraum sind ausdrücklich Entwurfs-/Prüfannahmen. Ursprüngliche Geometrie und Pivots sind gemessen, keine Bildschätzung.
- Kit-Hüllen/Lofts sind numerische Rekonstruktionen. Alle surface-Ausnahmen bleiben separat als gemessen gekennzeichnet. Keine gesamte Figur als importiertes Netz.
- Quellobjekte mit mehreren Materialslots erhalten für den Grundskin die häufigste vorhandene Materialrolle; prozedurale Mikrotextur, Glanz und Innenflächen-Schattierung sind kein Bestandteil des Modells. Originalaussehen als eigener Skin-Vorschlag, skins.toml unverändert.
- Gegenüber 01: höherer, schmalerer Körper, anderer Helm/Schultern, A-Grundhaltung plus separat gemessene Referenzhaltung mit engerer Schulterstellung, neue Innenfreiräume; wesentlich mehr gemessene surface-Rückfälle. Kopf ist kein geprüfter Tauschteil.
- Nicht zuständig: Unity-Kollision, LOD, Spiel-/Animationsbudget. Keine solche Abnahme behauptet.
- Integration: Typ 2 unter `[[types]]` registrieren, Linie A um Typ 2 ergänzen, Blatt und Skin mit der vorhandenen Pipeline bauen. ID-Vorschlag RA02 erst bei Integration vergeben. Keine Änderung an Register, skins.toml, model/geom/viewer/versions.py oder 01.
- Version/Tag/Release und veröffentlichte Reservierung bewusst offen: Nutzer verbietet Push/PR/Merge. Diese additive Modellarbeit bumpte keine globale Pipeline-Version und invalidiert keine Waffen-Caches.
- Gemeinsame Panzerprofil-Parameter sind umgesetzt. Offen bleiben die zwei wirkungslosen 01-Felder und die kopfseitige mechanische Schnittstelle: siehe parameter-vorschlag.md; kein geschützter Vertrag still geändert.

## Nicht gespiegelte linke Messungen

Die Liste nennt nicht spiegelgleich nachgewiesene Kontrollpunkte. Unterschiedliche Tessellierung ist keine Behauptung einer beabsichtigten gestalterischen Asymmetrie.

`AbPlate_Lower`, `AnklePiston_L`, `Backpack_Lower`, `BootToe_L`, `ChestVent_L`, `EarDisc_LCap`, `EarDisc_LDisc`, `EarDisc_LHub`, `EarDisc_LRing`, `ElbowMed_LCap`, `ElbowMed_LDisc`, `ElbowMed_LHub`, `ElbowMed_LRing`, `Forearm_L`, `HipMed_LCap`, `HipMed_LDisc`, `HipMed_LHub`, `HipMed_LRing`, `KneeMed_L_ICap`, `KneeMed_L_IDisc`, `KneeMed_L_IHub`, `KneeMed_L_IRing`, `KneeMed_L_OCap`, `KneeMed_L_ODisc`, `KneeMed_L_OHub`, `KneeMed_L_ORing`, `KneePistonBody1_L`, `KneePistonBody2_L`, `KneePistonEyeBot1_L`, `KneePistonEyeBot2_L`, `KneePistonEyeTop1_L`, `KneePistonEyeTop2_L`, `KneePistonRod1_L`, `KneePistonRod2_L`, `R3_WristSaddle_L`, `ShinBolt1_L`, `ShinBolt2_L`, `Shin_L`, `ShoulderBlockLower_L`, `ShoulderBlock_L`, `ShoulderMed_L_BHubBolt1`, `ShoulderMed_L_BHubBolt2`, `ShoulderMed_L_BHubBolt3`, `ShoulderMed_L_BHubBolt4`, `ShoulderMed_L_FHubBolt1`, `ShoulderMed_L_FHubBolt2`, `ShoulderMed_L_FHubBolt3`, `ShoulderMed_L_FHubBolt4`, `ThighCore_L`, `ThighPlate_L`, `Thigh_L`, `ToeSeam_L`

## Sämtliche surface-Ausnahmen

| Teil-ID | Quellobjekt | Grund |
|---|---|---|
| torso_back_bolt1 | BackBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_back_bolt2 | BackBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_back_bolt3 | BackBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_back_bolt4 | BackBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_back_panel_bolt1 | BackPanelBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_back_panel_bolt2 | BackPanelBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_backpack | Backpack | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| pelvis_belt | Belt | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| pelvis_L_belt_bolt | BeltBolt_L | Geschlossene mehrschalige Schraubengeometrie: koordinatengleiche, topologisch getrennte Flansche muessen getrennt bleiben; hull/Loft-Welding wuerde die Sackbohrung oeffnen. |
| pelvis_R_belt_bolt | BeltBolt_R | Geschlossene mehrschalige Schraubengeometrie: koordinatengleiche, topologisch getrennte Flansche muessen getrennt bleiben; hull/Loft-Welding wuerde die Sackbohrung oeffnen. |
| foot_L_boot_bolt1 | BootBolt1_L | Geschlossene mehrschalige Schraubengeometrie: koordinatengleiche, topologisch getrennte Flansche muessen getrennt bleiben; hull/Loft-Welding wuerde die Sackbohrung oeffnen. |
| foot_R_boot_bolt1 | BootBolt1_R | Geschlossene mehrschalige Schraubengeometrie: koordinatengleiche, topologisch getrennte Flansche muessen getrennt bleiben; hull/Loft-Welding wuerde die Sackbohrung oeffnen. |
| foot_L_boot_bolt2 | BootBolt2_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| foot_R_boot_bolt2 | BootBolt2_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| foot_L_boot_sole | BootSole_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| foot_R_boot_sole | BootSole_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| foot_L_boot_toe | BootToe_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| foot_R_boot_toe | BootToe_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_chest | Chest | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_L_chest_vent | ChestVent_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_R_chest_vent | ChestVent_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| pelvis_codpiece | Codpiece | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_L_collar_bolt | CollarBolt_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_R_collar_bolt | CollarBolt_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_L_ear_disc_hub_bolt1 | EarDisc_LHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_L_ear_disc_hub_bolt2 | EarDisc_LHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_L_ear_disc_hub_bolt3 | EarDisc_LHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_L_ear_disc_hub_bolt4 | EarDisc_LHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_R_ear_disc_hub_bolt1 | EarDisc_RHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_R_ear_disc_hub_bolt2 | EarDisc_RHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_R_ear_disc_hub_bolt3 | EarDisc_RHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_R_ear_disc_hub_bolt4 | EarDisc_RHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_elbow_cable | ElbowCable_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_elbow_cable | ElbowCable_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_elbow_med_hub_bolt1 | ElbowMed_LHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_elbow_med_hub_bolt2 | ElbowMed_LHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_elbow_med_hub_bolt3 | ElbowMed_LHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_elbow_med_hub_bolt4 | ElbowMed_LHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_elbow_med_hub_bolt1 | ElbowMed_RHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_elbow_med_hub_bolt2 | ElbowMed_RHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_elbow_med_hub_bolt3 | ElbowMed_RHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_elbow_med_hub_bolt4 | ElbowMed_RHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_forearm_bolt1 | ForearmBolt1_L | Geschlossene mehrschalige Schraubengeometrie: koordinatengleiche, topologisch getrennte Flansche muessen getrennt bleiben; hull/Loft-Welding wuerde die Sackbohrung oeffnen. |
| arm_R_forearm_bolt1 | ForearmBolt1_R | Geschlossene mehrschalige Schraubengeometrie: koordinatengleiche, topologisch getrennte Flansche muessen getrennt bleiben; hull/Loft-Welding wuerde die Sackbohrung oeffnen. |
| arm_L_forearm_bolt2 | ForearmBolt2_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_forearm_bolt2 | ForearmBolt2_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_forearm_core | ForearmCore_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_forearm_core | ForearmCore_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_forearm_inner_plate | ForearmInnerPlate_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_forearm_inner_plate | ForearmInnerPlate_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_forearm | Forearm_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_forearm | Forearm_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_hand_plate | HandPlate_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_hand_plate | HandPlate_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_helmet | Helmet | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_L_hip_med_hub_bolt1 | HipMed_LHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_L_hip_med_hub_bolt2 | HipMed_LHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_L_hip_med_hub_bolt3 | HipMed_LHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_L_hip_med_hub_bolt4 | HipMed_LHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_R_hip_med_hub_bolt1 | HipMed_RHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_R_hip_med_hub_bolt2 | HipMed_RHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_R_hip_med_hub_bolt3 | HipMed_RHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_R_hip_med_hub_bolt4 | HipMed_RHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_L_hose | Hose_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_R_hose | Hose_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_jaw | Jaw | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| kneecap_L_knee_bolt1 | KneeBolt1_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| kneecap_R_knee_bolt1 | KneeBolt1_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| kneecap_L_knee_bolt2 | KneeBolt2_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| kneecap_R_knee_bolt2 | KneeBolt2_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_L_knee_cable | KneeCable_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_R_knee_cable | KneeCable_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_L_knee_med_ihub_bolt1 | KneeMed_L_IHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_L_knee_med_ihub_bolt2 | KneeMed_L_IHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_L_knee_med_ihub_bolt3 | KneeMed_L_IHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_L_knee_med_ihub_bolt4 | KneeMed_L_IHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_L_knee_med_ohub_bolt1 | KneeMed_L_OHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_L_knee_med_ohub_bolt2 | KneeMed_L_OHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_L_knee_med_ohub_bolt3 | KneeMed_L_OHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_L_knee_med_ohub_bolt4 | KneeMed_L_OHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_R_knee_med_ihub_bolt1 | KneeMed_R_IHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_R_knee_med_ihub_bolt2 | KneeMed_R_IHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_R_knee_med_ihub_bolt3 | KneeMed_R_IHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_R_knee_med_ihub_bolt4 | KneeMed_R_IHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_R_knee_med_ohub_bolt1 | KneeMed_R_OHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_R_knee_med_ohub_bolt2 | KneeMed_R_OHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_R_knee_med_ohub_bolt3 | KneeMed_R_OHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_R_knee_med_ohub_bolt4 | KneeMed_R_OHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| kneecap_L_knee | Knee_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| kneecap_R_knee | Knee_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_palm | Palm_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_palm | Palm_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_r2_hand_screw1 | R2_HandScrew1_L | Geschlossene mehrschalige Schraubengeometrie: koordinatengleiche, topologisch getrennte Flansche muessen getrennt bleiben; hull/Loft-Welding wuerde die Sackbohrung oeffnen. |
| arm_R_r2_hand_screw1 | R2_HandScrew1_R | Geschlossene mehrschalige Schraubengeometrie: koordinatengleiche, topologisch getrennte Flansche muessen getrennt bleiben; hull/Loft-Welding wuerde die Sackbohrung oeffnen. |
| arm_L_r2_hand_screw2 | R2_HandScrew2_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_r2_hand_screw2 | R2_HandScrew2_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_r3_grip_finger_tip1 | R3_Grip_FingerTip1_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_r3_grip_finger_tip1 | R3_Grip_FingerTip1_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_r3_grip_finger_tip2 | R3_Grip_FingerTip2_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_r3_grip_finger_tip2 | R3_Grip_FingerTip2_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_r3_grip_finger_tip3 | R3_Grip_FingerTip3_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_r3_grip_finger_tip3 | R3_Grip_FingerTip3_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_r3_grip_finger_tip4 | R3_Grip_FingerTip4_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_r3_grip_finger_tip4 | R3_Grip_FingerTip4_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_r3_grip_thumb_mid | R3_Grip_ThumbMid_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_r3_grip_thumb_mid | R3_Grip_ThumbMid_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_r3_grip_thumb_tip | R3_Grip_ThumbTip_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_r3_grip_thumb_tip | R3_Grip_ThumbTip_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_r3_palm_heel | R3_PalmHeel_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_r3_palm_heel | R3_PalmHeel_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_r3_thenar_pad | R3_ThenarPad_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_r3_thenar_pad | R3_ThenarPad_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_r3_wrist_boltminus1 | R3_WristBolt-1_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_r3_wrist_boltminus1 | R3_WristBolt-1_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_r3_wrist_bolt1 | R3_WristBolt1_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_r3_wrist_bolt1 | R3_WristBolt1_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_r3_wrist_gaiter | R3_WristGaiter_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_r3_wrist_gaiter | R3_WristGaiter_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_r3_wrist_saddle | R3_WristSaddle_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_r3_wrist_saddle | R3_WristSaddle_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_r4_chin_inner_seal | R4_ChinInnerSeal | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| foot_L_r4_toe_bumper | R4_ToeBumper_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| foot_R_r4_toe_bumper | R4_ToeBumper_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_r4_visor_cyan | R4_VisorCyan | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_r5_sensor_inner_bezel | R5_SensorInnerBezel | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_ref_armor_finger_tip1 | RefArmor_FingerTip1_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_ref_armor_finger_tip1 | RefArmor_FingerTip1_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_ref_armor_finger_tip2 | RefArmor_FingerTip2_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_ref_armor_finger_tip2 | RefArmor_FingerTip2_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_ref_armor_finger_tip3 | RefArmor_FingerTip3_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_ref_armor_finger_tip3 | RefArmor_FingerTip3_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_ref_armor_finger_tip4 | RefArmor_FingerTip4_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_ref_armor_finger_tip4 | RefArmor_FingerTip4_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_ref_armor_thumb_mid | RefArmor_ThumbMid_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_ref_armor_thumb_mid | RefArmor_ThumbMid_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_ref_armor_thumb_tip | RefArmor_ThumbTip_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_ref_armor_thumb_tip | RefArmor_ThumbTip_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_L_ref_back_mount_screw1 | RefBackMountScrew1_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_R_ref_back_mount_screw1 | RefBackMountScrew1_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_L_ref_back_mount_screw2 | RefBackMountScrew2_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_R_ref_back_mount_screw2 | RefBackMountScrew2_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_rib_plate | RibPlate | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| pelvis_seat | Seat | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_sensor | Sensor | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_L_shin_bolt1 | ShinBolt1_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_R_shin_bolt1 | ShinBolt1_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_L_shin_bolt2 | ShinBolt2_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_R_shin_bolt2 | ShinBolt2_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_L_shin_chevron | ShinChevron_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_R_shin_chevron | ShinChevron_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_L_shin | Shin_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| shin_R_shin | Shin_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_L_shoulder_block_lower | ShoulderBlockLower_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_R_shoulder_block_lower | ShoulderBlockLower_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_L_shoulder_block | ShoulderBlock_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_R_shoulder_block | ShoulderBlock_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_L_shoulder_bolt1 | ShoulderBolt1_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_R_shoulder_bolt1 | ShoulderBolt1_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_L_shoulder_bolt2 | ShoulderBolt2_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_R_shoulder_bolt2 | ShoulderBolt2_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_shoulder_med_bhub_bolt1 | ShoulderMed_L_BHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_shoulder_med_bhub_bolt2 | ShoulderMed_L_BHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_shoulder_med_bhub_bolt3 | ShoulderMed_L_BHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_shoulder_med_bhub_bolt4 | ShoulderMed_L_BHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_shoulder_med_fhub_bolt1 | ShoulderMed_L_FHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_shoulder_med_fhub_bolt2 | ShoulderMed_L_FHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_shoulder_med_fhub_bolt3 | ShoulderMed_L_FHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_shoulder_med_fhub_bolt4 | ShoulderMed_L_FHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_shoulder_med_bhub_bolt1 | ShoulderMed_R_BHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_shoulder_med_bhub_bolt2 | ShoulderMed_R_BHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_shoulder_med_bhub_bolt3 | ShoulderMed_R_BHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_shoulder_med_bhub_bolt4 | ShoulderMed_R_BHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_shoulder_med_fhub_bolt1 | ShoulderMed_R_FHubBolt1 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_shoulder_med_fhub_bolt2 | ShoulderMed_R_FHubBolt2 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_shoulder_med_fhub_bolt3 | ShoulderMed_R_FHubBolt3 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_shoulder_med_fhub_bolt4 | ShoulderMed_R_FHubBolt4 | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_L_thigh_bolt1 | ThighBolt1_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_R_thigh_bolt1 | ThighBolt1_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_L_thigh_bolt2 | ThighBolt2_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_R_thigh_bolt2 | ThighBolt2_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_L_thigh_bolt3 | ThighBolt3_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_R_thigh_bolt3 | ThighBolt3_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_L_thigh_bolt4 | ThighBolt4_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_R_thigh_bolt4 | ThighBolt4_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_L_thigh_hatch_bolt1 | ThighHatchBolt1_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_R_thigh_hatch_bolt1 | ThighHatchBolt1_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_L_thigh_hatch_bolt2 | ThighHatchBolt2_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_R_thigh_hatch_bolt2 | ThighHatchBolt2_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_L_thigh_plate | ThighPlate_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_R_thigh_plate | ThighPlate_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_L_thigh | Thigh_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| thigh_R_thigh | Thigh_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| torso_torso_core | TorsoCore | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_upper_arm | UpperArm_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_upper_arm | UpperArm_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_visor | Visor | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| helmet_visor_frame | VisorFrame | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_L_wrist_cuff | WristCuff_L | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |
| arm_R_wrist_cuff | WristCuff_R | Nichtkonvexe geschlossene Detail-/Hohlform; gemessene Ringschnitte sind nicht vollstaendig gleichzaehlig. Bestehendes Kit kann die ausgewerte Schnitt-/Wand-/Fasenfolge nicht verlustfrei ausdruecken. |

## Vollständige Objektzuordnung

Hilfs-/Studioobjekte werden ausdrücklich nicht als Roboterteile übernommen; ihre Wirkung steckt gegebenenfalls in der vermessenen Form. Alle 629 Quellobjekte sind erfasst.

| Quellobjekt | Teil-ID / Status | Einzelteil | Baugruppe | SHAPES | Rolle | Elternteil |
|---|---|---|---|---|---|---|
| AbPlate_Lower | pelvis_ab_plate_lower | pelvis | upper_body | hull | shell | pelvis_waist |
| AbPlate_Upper | pelvis_ab_plate_upper | pelvis | upper_body | multi | shell | pelvis_waist |
| AnkleCore_L | shin_L_ankle_core | shins | legs | hull | graphite | shin_L_shin |
| AnkleCore_R | shin_R_ankle_core | shins | legs | hull | graphite | shin_R_shin |
| AnkleInsert_L | shin_L_ankle_insert | shins | legs | hull | graphite | shin_L_shin |
| AnkleInsert_R | shin_R_ankle_insert | shins | legs | hull | graphite | shin_R_shin |
| AnklePistonRod_L | foot_L_ankle_piston_rod | feet | legs | hull | metal | foot_L_boot_toe |
| AnklePistonRod_R | foot_R_ankle_piston_rod | feet | legs | hull | metal | foot_R_boot_toe |
| AnklePiston_L | shin_L_ankle_piston | shins | legs | hull | graphite | shin_L_shin |
| AnklePiston_R | shin_R_ankle_piston | shins | legs | hull | graphite | shin_R_shin |
| BackBolt1 | torso_back_bolt1 | upper_body | upper_body | surface | metal | torso_torso_core |
| BackBolt2 | torso_back_bolt2 | upper_body | upper_body | surface | metal | torso_torso_core |
| BackBolt3 | torso_back_bolt3 | upper_body | upper_body | surface | metal | torso_torso_core |
| BackBolt4 | torso_back_bolt4 | upper_body | upper_body | surface | metal | torso_torso_core |
| BackGrilleFrame_L | torso_L_back_grille_frame | upper_body | upper_body | hull | graphite | torso_torso_core |
| BackGrilleFrame_R | torso_R_back_grille_frame | upper_body | upper_body | hull | graphite | torso_torso_core |
| BackGrille_L | torso_L_back_grille | upper_body | upper_body | multi | graphite | torso_torso_core |
| BackGrille_R | torso_R_back_grille | upper_body | upper_body | multi | graphite | torso_torso_core |
| BackLowerGrille | torso_back_lower_grille | upper_body | upper_body | multi | graphite | torso_torso_core |
| BackLowerGrilleFrame | torso_back_lower_grille_frame | upper_body | upper_body | hull | graphite | torso_torso_core |
| BackLowerPanel_L | torso_L_back_lower_panel | upper_body | upper_body | hull | graphite | torso_torso_core |
| BackLowerPanel_R | torso_R_back_lower_panel | upper_body | upper_body | hull | graphite | torso_torso_core |
| BackPanel | torso_back_panel | upper_body | upper_body | hull | dark_metal | torso_torso_core |
| BackPanelBolt1 | torso_back_panel_bolt1 | upper_body | upper_body | surface | metal | torso_torso_core |
| BackPanelBolt2 | torso_back_panel_bolt2 | upper_body | upper_body | surface | metal | torso_torso_core |
| BackSideGrilleFrame_L | torso_L_back_side_grille_frame | upper_body | upper_body | hull | graphite | torso_torso_core |
| BackSideGrilleFrame_R | torso_R_back_side_grille_frame | upper_body | upper_body | hull | graphite | torso_torso_core |
| BackSideGrille_L | torso_L_back_side_grille | upper_body | upper_body | multi | graphite | torso_torso_core |
| BackSideGrille_R | torso_R_back_side_grille | upper_body | upper_body | multi | graphite | torso_torso_core |
| BackSlot_L | torso_L_back_slot | upper_body | upper_body | hull | graphite | torso_torso_core |
| BackSlot_R | torso_R_back_slot | upper_body | upper_body | hull | graphite | torso_torso_core |
| BackSpineFins | torso_back_spine_fins | upper_body | upper_body | multi | graphite | torso_torso_core |
| BackTopVent | torso_back_top_vent | upper_body | upper_body | multi | graphite | torso_torso_core |
| BackTopVentFrame | torso_back_top_vent_frame | upper_body | upper_body | hull | graphite | torso_torso_core |
| BackTriangle_L | torso_L_back_triangle | upper_body | upper_body | hull | graphite | torso_torso_core |
| BackTriangle_R | torso_R_back_triangle | upper_body | upper_body | hull | graphite | torso_torso_core |
| Backpack | torso_backpack | upper_body | upper_body | surface | shell | torso_torso_core |
| Backpack_Lower | torso_backpack_lower | upper_body | upper_body | hull | shell | torso_torso_core |
| Belt | pelvis_belt | pelvis | upper_body | surface | graphite | pelvis_pelvis_core |
| BeltBolt_L | pelvis_L_belt_bolt | pelvis | upper_body | surface | metal | pelvis_pelvis_core |
| BeltBolt_R | pelvis_R_belt_bolt | pelvis | upper_body | surface | metal | pelvis_pelvis_core |
| BeltBuckle | pelvis_belt_buckle | pelvis | upper_body | hull | metal | pelvis_pelvis_core |
| BoardGuides | nicht übernehmen: MESH / GUIDES | — | — | — | — | — |
| BootAnkle_L | foot_L_boot_ankle | feet | legs | hull | graphite | foot_L_boot_toe |
| BootAnkle_R | foot_R_boot_ankle | feet | legs | hull | graphite | foot_R_boot_toe |
| BootBolt1_L | foot_L_boot_bolt1 | feet | legs | surface | metal | foot_L_boot_toe |
| BootBolt1_R | foot_R_boot_bolt1 | feet | legs | surface | metal | foot_R_boot_toe |
| BootBolt2_L | foot_L_boot_bolt2 | feet | legs | surface | metal | foot_L_boot_toe |
| BootBolt2_R | foot_R_boot_bolt2 | feet | legs | surface | metal | foot_R_boot_toe |
| BootHeel_L | foot_L_boot_heel | feet | legs | hull | shell | foot_L_boot_toe |
| BootHeel_R | foot_R_boot_heel | feet | legs | hull | shell | foot_R_boot_toe |
| BootSole_L | foot_L_boot_sole | feet | legs | surface | rubber | foot_L_boot_toe |
| BootSole_R | foot_R_boot_sole | feet | legs | surface | rubber | foot_R_boot_toe |
| BootToe_L | foot_L_boot_toe | feet | legs | multi | shell | shin_L_shin |
| BootToe_R | foot_R_boot_toe | feet | legs | multi | shell | shin_R_shin |
| BuckleSlot | pelvis_buckle_slot | pelvis | upper_body | hull | graphite | pelvis_pelvis_core |
| BuckleTongue | pelvis_buckle_tongue | pelvis | upper_body | hull | metal | pelvis_pelvis_core |
| CAM_Hero | nicht übernehmen: CAMERA / STUDIO | — | — | — | — | — |
| CAM_HeroMatch | nicht übernehmen: CAMERA / STUDIO | — | — | — | — | — |
| CUT_AbPocket | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_BackH | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_BackSideV_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_BackSideV_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ChestH | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ChestSlots_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ChestSlots_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_CodPocket | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ForearmV_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ForearmV_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_Grille_BackGrilleFrame_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_Grille_BackGrilleFrame_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_Grille_BackSideGrilleFrame_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_Grille_BackSideGrilleFrame_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_Grille_BackTopVentFrame | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_R2_Tread_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_R2_Tread_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_R3_HandEngraving_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_R3_HandEngraving_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_R4_ChinVent | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_R4_ToeJoint_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_R4_ToeJoint_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_R5_ChestSeam_Dn | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_R5_ChestSeam_Up | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_RefAnkleV_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_RefAnkleV_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_RefBackPanel1_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_RefBackPanel1_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_RefBackPanel2_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_RefBackPanel2_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_RefBackTopNotch | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_RefHelmetSeam_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_RefHelmetSeam_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_SensorPocket | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ShinH_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ShinH_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ShinPocket_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ShinPocket_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ShinV_O_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ShinV_O_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ShoulderPocket_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ShoulderPocket_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ShoulderV_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ShoulderV_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ThighH_F_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ThighH_F_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ThighH_O_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ThighH_O_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ThighHatch_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_ThighHatch_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_UpperArmH_F_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_UpperArmH_F_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_UpperArmH_O_L | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_UpperArmH_O_R | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CUT_Visor | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| CalfInsert_L | shin_L_calf_insert | shins | legs | hull | dark_metal | shin_L_shin |
| CalfInsert_R | shin_R_calf_insert | shins | legs | hull | dark_metal | shin_R_shin |
| Chest | torso_chest | upper_body | upper_body | surface | shell | torso_torso_core |
| ChestBand | torso_chest_band | upper_body | upper_body | hull | graphite | torso_torso_core |
| ChestChevron | torso_chest_chevron | upper_body | upper_body | hull | dark_metal | torso_torso_core |
| ChestSeam_Dn | torso_chest_seam_dn | upper_body | upper_body | loft | dark_metal | torso_torso_core |
| ChestSeam_Up | torso_chest_seam_up | upper_body | upper_body | loft | dark_metal | torso_torso_core |
| ChestVent_L | torso_L_chest_vent | upper_body | upper_body | surface | dark_metal | torso_torso_core |
| ChestVent_R | torso_R_chest_vent | upper_body | upper_body | surface | dark_metal | torso_torso_core |
| ChinVent | helmet_chin_vent | head | head | hull | dark_metal | helmet_helmet |
| CodGroove | pelvis_cod_groove | pelvis | upper_body | hull | graphite | pelvis_pelvis_core |
| Codpiece | pelvis_codpiece | pelvis | upper_body | multi | shell | pelvis_pelvis_core |
| Collar | helmet_collar | head | head | hull | graphite | torso_torso_core |
| CollarBolt_L | helmet_L_collar_bolt | head | head | surface | metal | helmet_collar |
| CollarBolt_R | helmet_R_collar_bolt | head | head | surface | metal | helmet_collar |
| EarDisc_LCap | helmet_L_ear_disc_cap | head | head | hull | dark_metal | helmet_helmet |
| EarDisc_LDisc | helmet_L_ear_disc_disc | head | head | hull | dark_metal | helmet_helmet |
| EarDisc_LHub | helmet_L_ear_disc_hub | head | head | hull | dark_metal | helmet_helmet |
| EarDisc_LHubBolt1 | helmet_L_ear_disc_hub_bolt1 | head | head | surface | metal | helmet_helmet |
| EarDisc_LHubBolt2 | helmet_L_ear_disc_hub_bolt2 | head | head | surface | metal | helmet_helmet |
| EarDisc_LHubBolt3 | helmet_L_ear_disc_hub_bolt3 | head | head | surface | metal | helmet_helmet |
| EarDisc_LHubBolt4 | helmet_L_ear_disc_hub_bolt4 | head | head | surface | metal | helmet_helmet |
| EarDisc_LRecess | helmet_L_ear_disc_recess | head | head | hull | dark_metal | helmet_helmet |
| EarDisc_LRing | helmet_L_ear_disc_ring | head | head | loft | metal | helmet_helmet |
| EarDisc_RCap | helmet_R_ear_disc_cap | head | head | hull | dark_metal | helmet_helmet |
| EarDisc_RDisc | helmet_R_ear_disc_disc | head | head | hull | dark_metal | helmet_helmet |
| EarDisc_RHub | helmet_R_ear_disc_hub | head | head | hull | dark_metal | helmet_helmet |
| EarDisc_RHubBolt1 | helmet_R_ear_disc_hub_bolt1 | head | head | surface | metal | helmet_helmet |
| EarDisc_RHubBolt2 | helmet_R_ear_disc_hub_bolt2 | head | head | surface | metal | helmet_helmet |
| EarDisc_RHubBolt3 | helmet_R_ear_disc_hub_bolt3 | head | head | surface | metal | helmet_helmet |
| EarDisc_RHubBolt4 | helmet_R_ear_disc_hub_bolt4 | head | head | surface | metal | helmet_helmet |
| EarDisc_RRecess | helmet_R_ear_disc_recess | head | head | hull | dark_metal | helmet_helmet |
| EarDisc_RRing | helmet_R_ear_disc_ring | head | head | loft | metal | helmet_helmet |
| ElbowCable_L | arm_L_elbow_cable | upper_arms | arms | surface | graphite | arm_L_upper_arm |
| ElbowCable_R | arm_R_elbow_cable | upper_arms | arms | surface | graphite | arm_R_upper_arm |
| ElbowInnerCap_L | arm_L_elbow_inner_cap | upper_arms | arms | hull | graphite | arm_L_upper_arm |
| ElbowInnerCap_R | arm_R_elbow_inner_cap | upper_arms | arms | hull | graphite | arm_R_upper_arm |
| ElbowInnerRing_L | arm_L_elbow_inner_ring | upper_arms | arms | hull | metal | arm_L_upper_arm |
| ElbowInnerRing_R | arm_R_elbow_inner_ring | upper_arms | arms | hull | metal | arm_R_upper_arm |
| ElbowMed_LCap | arm_L_elbow_med_cap | upper_arms | arms | hull | dark_metal | arm_L_upper_arm |
| ElbowMed_LDisc | arm_L_elbow_med_disc | upper_arms | arms | hull | dark_metal | arm_L_upper_arm |
| ElbowMed_LHub | arm_L_elbow_med_hub | upper_arms | arms | hull | dark_metal | arm_L_upper_arm |
| ElbowMed_LHubBolt1 | arm_L_elbow_med_hub_bolt1 | upper_arms | arms | surface | metal | arm_L_upper_arm |
| ElbowMed_LHubBolt2 | arm_L_elbow_med_hub_bolt2 | upper_arms | arms | surface | metal | arm_L_upper_arm |
| ElbowMed_LHubBolt3 | arm_L_elbow_med_hub_bolt3 | upper_arms | arms | surface | metal | arm_L_upper_arm |
| ElbowMed_LHubBolt4 | arm_L_elbow_med_hub_bolt4 | upper_arms | arms | surface | metal | arm_L_upper_arm |
| ElbowMed_LRecess | arm_L_elbow_med_recess | upper_arms | arms | hull | dark_metal | arm_L_upper_arm |
| ElbowMed_LRing | arm_L_elbow_med_ring | upper_arms | arms | loft | metal | arm_L_upper_arm |
| ElbowMed_RCap | arm_R_elbow_med_cap | upper_arms | arms | hull | dark_metal | arm_R_upper_arm |
| ElbowMed_RDisc | arm_R_elbow_med_disc | upper_arms | arms | hull | dark_metal | arm_R_upper_arm |
| ElbowMed_RHub | arm_R_elbow_med_hub | upper_arms | arms | hull | dark_metal | arm_R_upper_arm |
| ElbowMed_RHubBolt1 | arm_R_elbow_med_hub_bolt1 | upper_arms | arms | surface | metal | arm_R_upper_arm |
| ElbowMed_RHubBolt2 | arm_R_elbow_med_hub_bolt2 | upper_arms | arms | surface | metal | arm_R_upper_arm |
| ElbowMed_RHubBolt3 | arm_R_elbow_med_hub_bolt3 | upper_arms | arms | surface | metal | arm_R_upper_arm |
| ElbowMed_RHubBolt4 | arm_R_elbow_med_hub_bolt4 | upper_arms | arms | surface | metal | arm_R_upper_arm |
| ElbowMed_RRecess | arm_R_elbow_med_recess | upper_arms | arms | hull | dark_metal | arm_R_upper_arm |
| ElbowMed_RRing | arm_R_elbow_med_ring | upper_arms | arms | loft | metal | arm_R_upper_arm |
| Elbow_L | arm_L_elbow | upper_arms | arms | hull | graphite | arm_L_upper_arm |
| Elbow_R | arm_R_elbow | upper_arms | arms | hull | graphite | arm_R_upper_arm |
| Finger1_L | arm_L_finger1 | hands | arms | hull | graphite | arm_L_palm |
| Finger1_R | arm_R_finger1 | hands | arms | hull | graphite | arm_R_palm |
| Finger2_L | arm_L_finger2 | hands | arms | hull | graphite | arm_L_palm |
| Finger2_R | arm_R_finger2 | hands | arms | hull | graphite | arm_R_palm |
| Finger3_L | arm_L_finger3 | hands | arms | hull | graphite | arm_L_palm |
| Finger3_R | arm_R_finger3 | hands | arms | hull | graphite | arm_R_palm |
| Finger4_L | arm_L_finger4 | hands | arms | hull | graphite | arm_L_palm |
| Finger4_R | arm_R_finger4 | hands | arms | hull | graphite | arm_R_palm |
| FingerMid1_L | arm_L_finger_mid1 | hands | arms | hull | graphite | arm_L_finger1 |
| FingerMid1_R | arm_R_finger_mid1 | hands | arms | hull | graphite | arm_R_finger1 |
| FingerMid2_L | arm_L_finger_mid2 | hands | arms | hull | graphite | arm_L_finger2 |
| FingerMid2_R | arm_R_finger_mid2 | hands | arms | hull | graphite | arm_R_finger2 |
| FingerMid3_L | arm_L_finger_mid3 | hands | arms | hull | graphite | arm_L_finger3 |
| FingerMid3_R | arm_R_finger_mid3 | hands | arms | hull | graphite | arm_R_finger3 |
| FingerMid4_L | arm_L_finger_mid4 | hands | arms | hull | graphite | arm_L_finger4 |
| FingerMid4_R | arm_R_finger_mid4 | hands | arms | hull | graphite | arm_R_finger4 |
| FingerTip1_L | arm_L_finger_tip1 | hands | arms | hull | graphite | arm_L_finger_mid1 |
| FingerTip1_R | arm_R_finger_tip1 | hands | arms | hull | graphite | arm_R_finger_mid1 |
| FingerTip2_L | arm_L_finger_tip2 | hands | arms | hull | graphite | arm_L_finger_mid2 |
| FingerTip2_R | arm_R_finger_tip2 | hands | arms | hull | graphite | arm_R_finger_mid2 |
| FingerTip3_L | arm_L_finger_tip3 | hands | arms | hull | graphite | arm_L_finger_mid3 |
| FingerTip3_R | arm_R_finger_tip3 | hands | arms | hull | graphite | arm_R_finger_mid3 |
| FingerTip4_L | arm_L_finger_tip4 | hands | arms | hull | graphite | arm_L_finger_mid4 |
| FingerTip4_R | arm_R_finger_tip4 | hands | arms | hull | graphite | arm_R_finger_mid4 |
| ForearmBolt1_L | arm_L_forearm_bolt1 | forearms | arms | surface | metal | arm_L_forearm |
| ForearmBolt1_R | arm_R_forearm_bolt1 | forearms | arms | surface | metal | arm_R_forearm |
| ForearmBolt2_L | arm_L_forearm_bolt2 | forearms | arms | surface | metal | arm_L_forearm |
| ForearmBolt2_R | arm_R_forearm_bolt2 | forearms | arms | surface | metal | arm_R_forearm |
| ForearmCore_L | arm_L_forearm_core | forearms | arms | surface | graphite | arm_L_forearm |
| ForearmCore_R | arm_R_forearm_core | forearms | arms | surface | graphite | arm_R_forearm |
| ForearmInnerPlate_L | arm_L_forearm_inner_plate | forearms | arms | surface | dark_metal | arm_L_forearm |
| ForearmInnerPlate_R | arm_R_forearm_inner_plate | forearms | arms | surface | dark_metal | arm_R_forearm |
| ForearmPlate_L | arm_L_forearm_plate | forearms | arms | hull | graphite | arm_L_forearm |
| ForearmPlate_R | arm_R_forearm_plate | forearms | arms | hull | graphite | arm_R_forearm |
| Forearm_L | arm_L_forearm | forearms | arms | surface | shell | arm_L_upper_arm |
| Forearm_R | arm_R_forearm | forearms | arms | surface | shell | arm_R_upper_arm |
| HandPlate_L | arm_L_hand_plate | hands | arms | surface | shell | arm_L_palm |
| HandPlate_R | arm_R_hand_plate | hands | arms | surface | shell | arm_R_palm |
| Hand_L | nicht übernehmen: EMPTY / ROBOT | — | — | — | — | — |
| Hand_R | nicht übernehmen: EMPTY / ROBOT | — | — | — | — | — |
| HeadGrid | nicht übernehmen: MESH / GUIDES | — | — | — | — | — |
| Helmet | helmet_helmet | head | head | surface | graphite | helmet_collar |
| HipJoint_L | thigh_L_hip_joint | thighs | legs | hull | graphite | thigh_L_thigh_core |
| HipJoint_R | thigh_R_hip_joint | thighs | legs | hull | graphite | thigh_R_thigh_core |
| HipMed_LCap | thigh_L_hip_med_cap | thighs | legs | hull | dark_metal | thigh_L_thigh_core |
| HipMed_LDisc | thigh_L_hip_med_disc | thighs | legs | hull | dark_metal | thigh_L_thigh_core |
| HipMed_LHub | thigh_L_hip_med_hub | thighs | legs | hull | dark_metal | thigh_L_thigh_core |
| HipMed_LHubBolt1 | thigh_L_hip_med_hub_bolt1 | thighs | legs | surface | metal | thigh_L_thigh_core |
| HipMed_LHubBolt2 | thigh_L_hip_med_hub_bolt2 | thighs | legs | surface | metal | thigh_L_thigh_core |
| HipMed_LHubBolt3 | thigh_L_hip_med_hub_bolt3 | thighs | legs | surface | metal | thigh_L_thigh_core |
| HipMed_LHubBolt4 | thigh_L_hip_med_hub_bolt4 | thighs | legs | surface | metal | thigh_L_thigh_core |
| HipMed_LRecess | thigh_L_hip_med_recess | thighs | legs | hull | dark_metal | thigh_L_thigh_core |
| HipMed_LRing | thigh_L_hip_med_ring | thighs | legs | loft | metal | thigh_L_thigh_core |
| HipMed_RCap | thigh_R_hip_med_cap | thighs | legs | hull | dark_metal | thigh_R_thigh_core |
| HipMed_RDisc | thigh_R_hip_med_disc | thighs | legs | hull | dark_metal | thigh_R_thigh_core |
| HipMed_RHub | thigh_R_hip_med_hub | thighs | legs | hull | dark_metal | thigh_R_thigh_core |
| HipMed_RHubBolt1 | thigh_R_hip_med_hub_bolt1 | thighs | legs | surface | metal | thigh_R_thigh_core |
| HipMed_RHubBolt2 | thigh_R_hip_med_hub_bolt2 | thighs | legs | surface | metal | thigh_R_thigh_core |
| HipMed_RHubBolt3 | thigh_R_hip_med_hub_bolt3 | thighs | legs | surface | metal | thigh_R_thigh_core |
| HipMed_RHubBolt4 | thigh_R_hip_med_hub_bolt4 | thighs | legs | surface | metal | thigh_R_thigh_core |
| HipMed_RRecess | thigh_R_hip_med_recess | thighs | legs | hull | dark_metal | thigh_R_thigh_core |
| HipMed_RRing | thigh_R_hip_med_ring | thighs | legs | loft | metal | thigh_R_thigh_core |
| HoseClamp_L | torso_L_hose_clamp | upper_body | upper_body | hull | metal | torso_torso_core |
| HoseClamp_R | torso_R_hose_clamp | upper_body | upper_body | hull | metal | torso_torso_core |
| Hose_L | torso_L_hose | upper_body | upper_body | surface | graphite | torso_torso_core |
| Hose_R | torso_R_hose | upper_body | upper_body | surface | graphite | torso_torso_core |
| Jaw | helmet_jaw | head | head | surface | shell | helmet_helmet |
| KneeBolt1_L | kneecap_L_knee_bolt1 | shins | legs | surface | metal | kneecap_L_knee |
| KneeBolt1_R | kneecap_R_knee_bolt1 | shins | legs | surface | metal | kneecap_R_knee |
| KneeBolt2_L | kneecap_L_knee_bolt2 | shins | legs | surface | metal | kneecap_L_knee |
| KneeBolt2_R | kneecap_R_knee_bolt2 | shins | legs | surface | metal | kneecap_R_knee |
| KneeCable_L | thigh_L_knee_cable | thighs | legs | surface | graphite | thigh_L_thigh_core |
| KneeCable_R | thigh_R_knee_cable | thighs | legs | surface | graphite | thigh_R_thigh_core |
| KneeCore_L | shin_L_knee_core | shins | legs | hull | graphite | shin_L_shin |
| KneeCore_R | shin_R_knee_core | shins | legs | hull | graphite | shin_R_shin |
| KneeGroove_L | kneecap_L_knee_groove | shins | legs | hull | graphite | kneecap_L_knee |
| KneeGroove_R | kneecap_R_knee_groove | shins | legs | hull | graphite | kneecap_R_knee |
| KneeJoint_L | shin_L_knee_joint | shins | legs | hull | graphite | shin_L_shin |
| KneeJoint_R | shin_R_knee_joint | shins | legs | hull | graphite | shin_R_shin |
| KneeMed_L_ICap | shin_L_knee_med_icap | shins | legs | hull | dark_metal | shin_L_shin |
| KneeMed_L_IDisc | shin_L_knee_med_idisc | shins | legs | hull | dark_metal | shin_L_shin |
| KneeMed_L_IHub | shin_L_knee_med_ihub | shins | legs | hull | dark_metal | shin_L_shin |
| KneeMed_L_IHubBolt1 | shin_L_knee_med_ihub_bolt1 | shins | legs | surface | metal | shin_L_shin |
| KneeMed_L_IHubBolt2 | shin_L_knee_med_ihub_bolt2 | shins | legs | surface | metal | shin_L_shin |
| KneeMed_L_IHubBolt3 | shin_L_knee_med_ihub_bolt3 | shins | legs | surface | metal | shin_L_shin |
| KneeMed_L_IHubBolt4 | shin_L_knee_med_ihub_bolt4 | shins | legs | surface | metal | shin_L_shin |
| KneeMed_L_IRecess | shin_L_knee_med_irecess | shins | legs | hull | dark_metal | shin_L_shin |
| KneeMed_L_IRing | shin_L_knee_med_iring | shins | legs | loft | metal | shin_L_shin |
| KneeMed_L_OCap | shin_L_knee_med_ocap | shins | legs | hull | dark_metal | shin_L_shin |
| KneeMed_L_ODisc | shin_L_knee_med_odisc | shins | legs | hull | dark_metal | shin_L_shin |
| KneeMed_L_OHub | shin_L_knee_med_ohub | shins | legs | hull | dark_metal | shin_L_shin |
| KneeMed_L_OHubBolt1 | shin_L_knee_med_ohub_bolt1 | shins | legs | surface | metal | shin_L_shin |
| KneeMed_L_OHubBolt2 | shin_L_knee_med_ohub_bolt2 | shins | legs | surface | metal | shin_L_shin |
| KneeMed_L_OHubBolt3 | shin_L_knee_med_ohub_bolt3 | shins | legs | surface | metal | shin_L_shin |
| KneeMed_L_OHubBolt4 | shin_L_knee_med_ohub_bolt4 | shins | legs | surface | metal | shin_L_shin |
| KneeMed_L_ORecess | shin_L_knee_med_orecess | shins | legs | hull | dark_metal | shin_L_shin |
| KneeMed_L_ORing | shin_L_knee_med_oring | shins | legs | loft | metal | shin_L_shin |
| KneeMed_R_ICap | shin_R_knee_med_icap | shins | legs | hull | dark_metal | shin_R_shin |
| KneeMed_R_IDisc | shin_R_knee_med_idisc | shins | legs | hull | dark_metal | shin_R_shin |
| KneeMed_R_IHub | shin_R_knee_med_ihub | shins | legs | hull | dark_metal | shin_R_shin |
| KneeMed_R_IHubBolt1 | shin_R_knee_med_ihub_bolt1 | shins | legs | surface | metal | shin_R_shin |
| KneeMed_R_IHubBolt2 | shin_R_knee_med_ihub_bolt2 | shins | legs | surface | metal | shin_R_shin |
| KneeMed_R_IHubBolt3 | shin_R_knee_med_ihub_bolt3 | shins | legs | surface | metal | shin_R_shin |
| KneeMed_R_IHubBolt4 | shin_R_knee_med_ihub_bolt4 | shins | legs | surface | metal | shin_R_shin |
| KneeMed_R_IRecess | shin_R_knee_med_irecess | shins | legs | hull | dark_metal | shin_R_shin |
| KneeMed_R_IRing | shin_R_knee_med_iring | shins | legs | loft | metal | shin_R_shin |
| KneeMed_R_OCap | shin_R_knee_med_ocap | shins | legs | hull | dark_metal | shin_R_shin |
| KneeMed_R_ODisc | shin_R_knee_med_odisc | shins | legs | hull | dark_metal | shin_R_shin |
| KneeMed_R_OHub | shin_R_knee_med_ohub | shins | legs | hull | dark_metal | shin_R_shin |
| KneeMed_R_OHubBolt1 | shin_R_knee_med_ohub_bolt1 | shins | legs | surface | metal | shin_R_shin |
| KneeMed_R_OHubBolt2 | shin_R_knee_med_ohub_bolt2 | shins | legs | surface | metal | shin_R_shin |
| KneeMed_R_OHubBolt3 | shin_R_knee_med_ohub_bolt3 | shins | legs | surface | metal | shin_R_shin |
| KneeMed_R_OHubBolt4 | shin_R_knee_med_ohub_bolt4 | shins | legs | surface | metal | shin_R_shin |
| KneeMed_R_ORecess | shin_R_knee_med_orecess | shins | legs | hull | dark_metal | shin_R_shin |
| KneeMed_R_ORing | shin_R_knee_med_oring | shins | legs | loft | metal | shin_R_shin |
| KneePistonBody1_L | thigh_L_knee_piston_body1 | thighs | legs | hull | graphite | thigh_L_thigh_core |
| KneePistonBody1_R | thigh_R_knee_piston_body1 | thighs | legs | hull | graphite | thigh_R_thigh_core |
| KneePistonBody2_L | thigh_L_knee_piston_body2 | thighs | legs | hull | graphite | thigh_L_thigh_core |
| KneePistonBody2_R | thigh_R_knee_piston_body2 | thighs | legs | hull | graphite | thigh_R_thigh_core |
| KneePistonEyeBot1_L | shin_L_knee_piston_eye_bot1 | shins | legs | hull | metal | shin_L_shin |
| KneePistonEyeBot1_R | shin_R_knee_piston_eye_bot1 | shins | legs | hull | metal | shin_R_shin |
| KneePistonEyeBot2_L | shin_L_knee_piston_eye_bot2 | shins | legs | hull | metal | shin_L_shin |
| KneePistonEyeBot2_R | shin_R_knee_piston_eye_bot2 | shins | legs | hull | metal | shin_R_shin |
| KneePistonEyeTop1_L | thigh_L_knee_piston_eye_top1 | thighs | legs | hull | metal | thigh_L_thigh_core |
| KneePistonEyeTop1_R | thigh_R_knee_piston_eye_top1 | thighs | legs | hull | metal | thigh_R_thigh_core |
| KneePistonEyeTop2_L | thigh_L_knee_piston_eye_top2 | thighs | legs | hull | metal | thigh_L_thigh_core |
| KneePistonEyeTop2_R | thigh_R_knee_piston_eye_top2 | thighs | legs | hull | metal | thigh_R_thigh_core |
| KneePistonRod1_L | shin_L_knee_piston_rod1 | shins | legs | hull | metal | shin_L_shin |
| KneePistonRod1_R | shin_R_knee_piston_rod1 | shins | legs | hull | metal | shin_R_shin |
| KneePistonRod2_L | shin_L_knee_piston_rod2 | shins | legs | hull | metal | shin_L_shin |
| KneePistonRod2_R | shin_R_knee_piston_rod2 | shins | legs | hull | metal | shin_R_shin |
| Knee_L | kneecap_L_knee | shins | legs | surface | shell | thigh_L_thigh_core |
| Knee_R | kneecap_R_knee | shins | legs | surface | shell | thigh_R_thigh_core |
| L_Backdrop | nicht übernehmen: LIGHT / STUDIO | — | — | — | — | — |
| L_Fill | nicht übernehmen: LIGHT / STUDIO | — | — | — | — | — |
| L_Key | nicht übernehmen: LIGHT / STUDIO | — | — | — | — | — |
| L_Rim | nicht übernehmen: LIGHT / STUDIO | — | — | — | — | — |
| L_RimKick | nicht übernehmen: LIGHT / STUDIO | — | — | — | — | — |
| L_Top | nicht übernehmen: LIGHT / STUDIO | — | — | — | — | — |
| Neck | helmet_neck | head | head | hull | graphite | helmet_collar |
| NeckRing1 | helmet_neck_ring1 | head | head | hull | metal | helmet_collar |
| NeckRing2 | helmet_neck_ring2 | head | head | hull | graphite | helmet_collar |
| OrangeDetail_1 | pelvis_orange_detail_1 | pelvis | upper_body | hull | accent | pelvis_pelvis_core |
| OrangeDetail_2 | pelvis_orange_detail_2 | pelvis | upper_body | hull | accent | pelvis_pelvis_core |
| OrangeDetail_3 | torso_orange_detail_3 | upper_body | upper_body | hull | accent | torso_torso_core |
| OrangeDetail_4 | pelvis_orange_detail_4 | pelvis | upper_body | hull | accent | pelvis_pelvis_core |
| OrangeDetail_5 | pelvis_orange_detail_5 | pelvis | upper_body | hull | accent | pelvis_pelvis_core |
| OrangeDetail_6 | torso_orange_detail_6 | upper_body | upper_body | hull | accent | torso_torso_core |
| Palm_L | arm_L_palm | hands | arms | surface | graphite | arm_L_forearm |
| Palm_R | arm_R_palm | hands | arms | surface | graphite | arm_R_forearm |
| PelvisCore | pelvis_pelvis_core | pelvis | upper_body | hull | graphite | — |
| R2_AnkleAxle_L | foot_L_r2_ankle_axle | feet | legs | hull | metal | foot_L_boot_toe |
| R2_AnkleAxle_R | foot_R_r2_ankle_axle | feet | legs | hull | metal | foot_R_boot_toe |
| R2_AnkleBearing_L | foot_L_r2_ankle_bearing | feet | legs | hull | metal | foot_L_boot_toe |
| R2_AnkleBearing_R | foot_R_r2_ankle_bearing | feet | legs | hull | metal | foot_R_boot_toe |
| R2_AnkleHinge_L | foot_L_r2_ankle_hinge | feet | legs | hull | dark_metal | foot_L_boot_toe |
| R2_AnkleHinge_R | foot_R_r2_ankle_hinge | feet | legs | hull | dark_metal | foot_R_boot_toe |
| R2_AnkleRodJoint_L | foot_L_r2_ankle_rod_joint | feet | legs | hull | dark_metal | foot_L_boot_toe |
| R2_AnkleRodJoint_R | foot_R_r2_ankle_rod_joint | feet | legs | hull | dark_metal | foot_R_boot_toe |
| R2_ChestNormalSource | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| R2_HandScrew1_L | arm_L_r2_hand_screw1 | hands | arms | surface | metal | arm_L_palm |
| R2_HandScrew1_R | arm_R_r2_hand_screw1 | hands | arms | surface | metal | arm_R_palm |
| R2_HandScrew2_L | arm_L_r2_hand_screw2 | hands | arms | surface | metal | arm_L_palm |
| R2_HandScrew2_R | arm_R_r2_hand_screw2 | hands | arms | surface | metal | arm_R_palm |
| R2_WristAxle_L | arm_L_r2_wrist_axle | hands | arms | hull | metal | arm_L_palm |
| R2_WristAxle_R | arm_R_r2_wrist_axle | hands | arms | hull | metal | arm_R_palm |
| R2_WristBearing_L | arm_L_r2_wrist_bearing | hands | arms | hull | metal | arm_L_palm |
| R2_WristBearing_R | arm_R_r2_wrist_bearing | hands | arms | hull | metal | arm_R_palm |
| R2_WristGimbal_L | arm_L_r2_wrist_gimbal | hands | arms | hull | dark_metal | arm_L_palm |
| R2_WristGimbal_R | arm_R_r2_wrist_gimbal | hands | arms | hull | dark_metal | arm_R_palm |
| R3_Grip_Finger1_L | arm_L_r3_grip_finger1 | hands | arms | hull | rubber | arm_L_finger1 |
| R3_Grip_Finger1_R | arm_R_r3_grip_finger1 | hands | arms | hull | rubber | arm_R_finger1 |
| R3_Grip_Finger2_L | arm_L_r3_grip_finger2 | hands | arms | hull | rubber | arm_L_finger2 |
| R3_Grip_Finger2_R | arm_R_r3_grip_finger2 | hands | arms | hull | rubber | arm_R_finger2 |
| R3_Grip_Finger3_L | arm_L_r3_grip_finger3 | hands | arms | hull | rubber | arm_L_finger3 |
| R3_Grip_Finger3_R | arm_R_r3_grip_finger3 | hands | arms | hull | rubber | arm_R_finger3 |
| R3_Grip_Finger4_L | arm_L_r3_grip_finger4 | hands | arms | hull | rubber | arm_L_finger4 |
| R3_Grip_Finger4_R | arm_R_r3_grip_finger4 | hands | arms | hull | rubber | arm_R_finger4 |
| R3_Grip_FingerMid1_L | arm_L_r3_grip_finger_mid1 | hands | arms | hull | rubber | arm_L_finger_mid1 |
| R3_Grip_FingerMid1_R | arm_R_r3_grip_finger_mid1 | hands | arms | hull | rubber | arm_R_finger_mid1 |
| R3_Grip_FingerMid2_L | arm_L_r3_grip_finger_mid2 | hands | arms | hull | rubber | arm_L_finger_mid2 |
| R3_Grip_FingerMid2_R | arm_R_r3_grip_finger_mid2 | hands | arms | hull | rubber | arm_R_finger_mid2 |
| R3_Grip_FingerMid3_L | arm_L_r3_grip_finger_mid3 | hands | arms | hull | rubber | arm_L_finger_mid3 |
| R3_Grip_FingerMid3_R | arm_R_r3_grip_finger_mid3 | hands | arms | hull | rubber | arm_R_finger_mid3 |
| R3_Grip_FingerMid4_L | arm_L_r3_grip_finger_mid4 | hands | arms | hull | rubber | arm_L_finger_mid4 |
| R3_Grip_FingerMid4_R | arm_R_r3_grip_finger_mid4 | hands | arms | hull | rubber | arm_R_finger_mid4 |
| R3_Grip_FingerTip1_L | arm_L_r3_grip_finger_tip1 | hands | arms | surface | rubber | arm_L_finger_tip1 |
| R3_Grip_FingerTip1_R | arm_R_r3_grip_finger_tip1 | hands | arms | surface | rubber | arm_R_finger_tip1 |
| R3_Grip_FingerTip2_L | arm_L_r3_grip_finger_tip2 | hands | arms | surface | rubber | arm_L_finger_tip2 |
| R3_Grip_FingerTip2_R | arm_R_r3_grip_finger_tip2 | hands | arms | surface | rubber | arm_R_finger_tip2 |
| R3_Grip_FingerTip3_L | arm_L_r3_grip_finger_tip3 | hands | arms | surface | rubber | arm_L_finger_tip3 |
| R3_Grip_FingerTip3_R | arm_R_r3_grip_finger_tip3 | hands | arms | surface | rubber | arm_R_finger_tip3 |
| R3_Grip_FingerTip4_L | arm_L_r3_grip_finger_tip4 | hands | arms | surface | rubber | arm_L_finger_tip4 |
| R3_Grip_FingerTip4_R | arm_R_r3_grip_finger_tip4 | hands | arms | surface | rubber | arm_R_finger_tip4 |
| R3_Grip_ThumbMid_L | arm_L_r3_grip_thumb_mid | hands | arms | surface | rubber | arm_L_thumb_mid |
| R3_Grip_ThumbMid_R | arm_R_r3_grip_thumb_mid | hands | arms | surface | rubber | arm_R_thumb_mid |
| R3_Grip_ThumbTip_L | arm_L_r3_grip_thumb_tip | hands | arms | surface | rubber | arm_L_thumb_tip |
| R3_Grip_ThumbTip_R | arm_R_r3_grip_thumb_tip | hands | arms | surface | rubber | arm_R_thumb_tip |
| R3_Grip_Thumb_L | arm_L_r3_grip_thumb | hands | arms | hull | rubber | arm_L_thumb |
| R3_Grip_Thumb_R | arm_R_r3_grip_thumb | hands | arms | hull | rubber | arm_R_thumb |
| R3_KnucklePad1_L | arm_L_r3_knuckle_pad1 | hands | arms | hull | graphite | arm_L_palm |
| R3_KnucklePad1_R | arm_R_r3_knuckle_pad1 | hands | arms | hull | graphite | arm_R_palm |
| R3_KnucklePad2_L | arm_L_r3_knuckle_pad2 | hands | arms | hull | graphite | arm_L_palm |
| R3_KnucklePad2_R | arm_R_r3_knuckle_pad2 | hands | arms | hull | graphite | arm_R_palm |
| R3_KnucklePad3_L | arm_L_r3_knuckle_pad3 | hands | arms | hull | graphite | arm_L_palm |
| R3_KnucklePad3_R | arm_R_r3_knuckle_pad3 | hands | arms | hull | graphite | arm_R_palm |
| R3_KnucklePad4_L | arm_L_r3_knuckle_pad4 | hands | arms | hull | graphite | arm_L_palm |
| R3_KnucklePad4_R | arm_R_r3_knuckle_pad4 | hands | arms | hull | graphite | arm_R_palm |
| R3_PalmCenter_L | arm_L_r3_palm_center | hands | arms | hull | graphite | arm_L_palm |
| R3_PalmCenter_R | arm_R_r3_palm_center | hands | arms | hull | graphite | arm_R_palm |
| R3_PalmHeel_L | arm_L_r3_palm_heel | hands | arms | surface | graphite | arm_L_palm |
| R3_PalmHeel_R | arm_R_r3_palm_heel | hands | arms | surface | graphite | arm_R_palm |
| R3_PalmScrew1_L | arm_L_r3_palm_screw1 | hands | arms | hull | metal | arm_L_palm |
| R3_PalmScrew1_R | arm_R_r3_palm_screw1 | hands | arms | hull | metal | arm_R_palm |
| R3_PalmScrew2_L | arm_L_r3_palm_screw2 | hands | arms | hull | metal | arm_L_palm |
| R3_PalmScrew2_R | arm_R_r3_palm_screw2 | hands | arms | hull | metal | arm_R_palm |
| R3_PalmScrew3_L | arm_L_r3_palm_screw3 | hands | arms | hull | metal | arm_L_palm |
| R3_PalmScrew3_R | arm_R_r3_palm_screw3 | hands | arms | hull | metal | arm_R_palm |
| R3_PinEnds_Finger1_L | arm_L_r3_pin_ends_finger1 | hands | arms | multi | metal | arm_L_finger1 |
| R3_PinEnds_Finger1_R | arm_R_r3_pin_ends_finger1 | hands | arms | multi | metal | arm_R_finger1 |
| R3_PinEnds_Finger2_L | arm_L_r3_pin_ends_finger2 | hands | arms | multi | metal | arm_L_finger2 |
| R3_PinEnds_Finger2_R | arm_R_r3_pin_ends_finger2 | hands | arms | multi | metal | arm_R_finger2 |
| R3_PinEnds_Finger3_L | arm_L_r3_pin_ends_finger3 | hands | arms | multi | metal | arm_L_finger3 |
| R3_PinEnds_Finger3_R | arm_R_r3_pin_ends_finger3 | hands | arms | multi | metal | arm_R_finger3 |
| R3_PinEnds_Finger4_L | arm_L_r3_pin_ends_finger4 | hands | arms | multi | metal | arm_L_finger4 |
| R3_PinEnds_Finger4_R | arm_R_r3_pin_ends_finger4 | hands | arms | multi | metal | arm_R_finger4 |
| R3_PinEnds_FingerMid1_L | arm_L_r3_pin_ends_finger_mid1 | hands | arms | multi | metal | arm_L_finger_mid1 |
| R3_PinEnds_FingerMid1_R | arm_R_r3_pin_ends_finger_mid1 | hands | arms | multi | metal | arm_R_finger_mid1 |
| R3_PinEnds_FingerMid2_L | arm_L_r3_pin_ends_finger_mid2 | hands | arms | multi | metal | arm_L_finger_mid2 |
| R3_PinEnds_FingerMid2_R | arm_R_r3_pin_ends_finger_mid2 | hands | arms | multi | metal | arm_R_finger_mid2 |
| R3_PinEnds_FingerMid3_L | arm_L_r3_pin_ends_finger_mid3 | hands | arms | multi | metal | arm_L_finger_mid3 |
| R3_PinEnds_FingerMid3_R | arm_R_r3_pin_ends_finger_mid3 | hands | arms | multi | metal | arm_R_finger_mid3 |
| R3_PinEnds_FingerMid4_L | arm_L_r3_pin_ends_finger_mid4 | hands | arms | multi | metal | arm_L_finger_mid4 |
| R3_PinEnds_FingerMid4_R | arm_R_r3_pin_ends_finger_mid4 | hands | arms | multi | metal | arm_R_finger_mid4 |
| R3_PinEnds_FingerTip1_L | arm_L_r3_pin_ends_finger_tip1 | hands | arms | multi | metal | arm_L_finger_tip1 |
| R3_PinEnds_FingerTip1_R | arm_R_r3_pin_ends_finger_tip1 | hands | arms | multi | metal | arm_R_finger_tip1 |
| R3_PinEnds_FingerTip2_L | arm_L_r3_pin_ends_finger_tip2 | hands | arms | multi | metal | arm_L_finger_tip2 |
| R3_PinEnds_FingerTip2_R | arm_R_r3_pin_ends_finger_tip2 | hands | arms | multi | metal | arm_R_finger_tip2 |
| R3_PinEnds_FingerTip3_L | arm_L_r3_pin_ends_finger_tip3 | hands | arms | multi | metal | arm_L_finger_tip3 |
| R3_PinEnds_FingerTip3_R | arm_R_r3_pin_ends_finger_tip3 | hands | arms | multi | metal | arm_R_finger_tip3 |
| R3_PinEnds_FingerTip4_L | arm_L_r3_pin_ends_finger_tip4 | hands | arms | multi | metal | arm_L_finger_tip4 |
| R3_PinEnds_FingerTip4_R | arm_R_r3_pin_ends_finger_tip4 | hands | arms | multi | metal | arm_R_finger_tip4 |
| R3_PinEnds_ThumbMid_L | arm_L_r3_pin_ends_thumb_mid | hands | arms | multi | metal | arm_L_thumb_mid |
| R3_PinEnds_ThumbMid_R | arm_R_r3_pin_ends_thumb_mid | hands | arms | multi | metal | arm_R_thumb_mid |
| R3_PinEnds_ThumbTip_L | arm_L_r3_pin_ends_thumb_tip | hands | arms | multi | metal | arm_L_thumb_tip |
| R3_PinEnds_ThumbTip_R | arm_R_r3_pin_ends_thumb_tip | hands | arms | multi | metal | arm_R_thumb_tip |
| R3_PinEnds_Thumb_L | arm_L_r3_pin_ends_thumb | hands | arms | multi | metal | arm_L_thumb |
| R3_PinEnds_Thumb_R | arm_R_r3_pin_ends_thumb | hands | arms | multi | metal | arm_R_thumb |
| R3_ThenarPad_L | arm_L_r3_thenar_pad | hands | arms | surface | graphite | arm_L_palm |
| R3_ThenarPad_R | arm_R_r3_thenar_pad | hands | arms | surface | graphite | arm_R_palm |
| R3_ThumbSocketCap_L | arm_L_r3_thumb_socket_cap | hands | arms | hull | metal | arm_L_palm |
| R3_ThumbSocketCap_R | arm_R_r3_thumb_socket_cap | hands | arms | hull | metal | arm_R_palm |
| R3_ThumbSocket_L | arm_L_r3_thumb_socket | hands | arms | hull | dark_metal | arm_L_palm |
| R3_ThumbSocket_R | arm_R_r3_thumb_socket | hands | arms | hull | dark_metal | arm_R_palm |
| R3_WristBolt-1_L | arm_L_r3_wrist_boltminus1 | hands | arms | surface | metal | arm_L_palm |
| R3_WristBolt-1_R | arm_R_r3_wrist_boltminus1 | hands | arms | surface | metal | arm_R_palm |
| R3_WristBolt1_L | arm_L_r3_wrist_bolt1 | hands | arms | surface | metal | arm_L_palm |
| R3_WristBolt1_R | arm_R_r3_wrist_bolt1 | hands | arms | surface | metal | arm_R_palm |
| R3_WristGaiter_L | arm_L_r3_wrist_gaiter | hands | arms | surface | graphite | arm_L_palm |
| R3_WristGaiter_R | arm_R_r3_wrist_gaiter | hands | arms | surface | graphite | arm_R_palm |
| R3_WristHolder-1_L | arm_L_r3_wrist_holderminus1 | hands | arms | hull | shell | arm_L_palm |
| R3_WristHolder-1_R | arm_R_r3_wrist_holderminus1 | hands | arms | hull | shell | arm_R_palm |
| R3_WristHolder1_L | arm_L_r3_wrist_holder1 | hands | arms | hull | shell | arm_L_palm |
| R3_WristHolder1_R | arm_R_r3_wrist_holder1 | hands | arms | hull | shell | arm_R_palm |
| R3_WristSaddle_L | arm_L_r3_wrist_saddle | hands | arms | surface | dark_metal | arm_L_palm |
| R3_WristSaddle_R | arm_R_r3_wrist_saddle | hands | arms | surface | dark_metal | arm_R_palm |
| R4_ChinInnerSeal | helmet_r4_chin_inner_seal | head | head | surface | graphite | helmet_helmet |
| R4_HelmetNormalSource | nicht übernehmen: MESH / CUTTERS | — | — | — | — | — |
| R4_ToeBumper_L | foot_L_r4_toe_bumper | feet | legs | surface | rubber | foot_L_boot_toe |
| R4_ToeBumper_R | foot_R_r4_toe_bumper | feet | legs | surface | rubber | foot_R_boot_toe |
| R4_VisorCyan | helmet_r4_visor_cyan | head | head | surface | energy | helmet_helmet |
| R5_SensorInnerBezel | torso_r5_sensor_inner_bezel | upper_body | upper_body | surface | metal | torso_torso_core |
| R5_SensorLightRing | torso_r5_sensor_light_ring | upper_body | upper_body | loft | energy | torso_torso_core |
| R5_SensorOuterBezel | torso_r5_sensor_outer_bezel | upper_body | upper_body | loft | metal | torso_torso_core |
| R5_SensorRetainers | torso_r5_sensor_retainers | upper_body | upper_body | multi | metal | torso_torso_core |
| REF_Back | nicht übernehmen: EMPTY / REF | — | — | — | — | — |
| REF_Front | nicht übernehmen: EMPTY / REF | — | — | — | — | — |
| REF_Side | nicht übernehmen: EMPTY / REF | — | — | — | — | — |
| RIG | nicht übernehmen: ARMATURE / RIG | — | — | — | — | — |
| RefArmor_Finger1_L | arm_L_ref_armor_finger1 | hands | arms | hull | shell | arm_L_finger1 |
| RefArmor_Finger1_R | arm_R_ref_armor_finger1 | hands | arms | hull | shell | arm_R_finger1 |
| RefArmor_Finger2_L | arm_L_ref_armor_finger2 | hands | arms | hull | shell | arm_L_finger2 |
| RefArmor_Finger2_R | arm_R_ref_armor_finger2 | hands | arms | hull | shell | arm_R_finger2 |
| RefArmor_Finger3_L | arm_L_ref_armor_finger3 | hands | arms | hull | shell | arm_L_finger3 |
| RefArmor_Finger3_R | arm_R_ref_armor_finger3 | hands | arms | hull | shell | arm_R_finger3 |
| RefArmor_Finger4_L | arm_L_ref_armor_finger4 | hands | arms | hull | shell | arm_L_finger4 |
| RefArmor_Finger4_R | arm_R_ref_armor_finger4 | hands | arms | hull | shell | arm_R_finger4 |
| RefArmor_FingerMid1_L | arm_L_ref_armor_finger_mid1 | hands | arms | hull | shell | arm_L_finger_mid1 |
| RefArmor_FingerMid1_R | arm_R_ref_armor_finger_mid1 | hands | arms | hull | shell | arm_R_finger_mid1 |
| RefArmor_FingerMid2_L | arm_L_ref_armor_finger_mid2 | hands | arms | hull | shell | arm_L_finger_mid2 |
| RefArmor_FingerMid2_R | arm_R_ref_armor_finger_mid2 | hands | arms | hull | shell | arm_R_finger_mid2 |
| RefArmor_FingerMid3_L | arm_L_ref_armor_finger_mid3 | hands | arms | hull | shell | arm_L_finger_mid3 |
| RefArmor_FingerMid3_R | arm_R_ref_armor_finger_mid3 | hands | arms | hull | shell | arm_R_finger_mid3 |
| RefArmor_FingerMid4_L | arm_L_ref_armor_finger_mid4 | hands | arms | hull | shell | arm_L_finger_mid4 |
| RefArmor_FingerMid4_R | arm_R_ref_armor_finger_mid4 | hands | arms | hull | shell | arm_R_finger_mid4 |
| RefArmor_FingerTip1_L | arm_L_ref_armor_finger_tip1 | hands | arms | surface | shell | arm_L_finger_tip1 |
| RefArmor_FingerTip1_R | arm_R_ref_armor_finger_tip1 | hands | arms | surface | shell | arm_R_finger_tip1 |
| RefArmor_FingerTip2_L | arm_L_ref_armor_finger_tip2 | hands | arms | surface | shell | arm_L_finger_tip2 |
| RefArmor_FingerTip2_R | arm_R_ref_armor_finger_tip2 | hands | arms | surface | shell | arm_R_finger_tip2 |
| RefArmor_FingerTip3_L | arm_L_ref_armor_finger_tip3 | hands | arms | surface | shell | arm_L_finger_tip3 |
| RefArmor_FingerTip3_R | arm_R_ref_armor_finger_tip3 | hands | arms | surface | shell | arm_R_finger_tip3 |
| RefArmor_FingerTip4_L | arm_L_ref_armor_finger_tip4 | hands | arms | surface | shell | arm_L_finger_tip4 |
| RefArmor_FingerTip4_R | arm_R_ref_armor_finger_tip4 | hands | arms | surface | shell | arm_R_finger_tip4 |
| RefArmor_ThumbMid_L | arm_L_ref_armor_thumb_mid | hands | arms | surface | shell | arm_L_thumb_mid |
| RefArmor_ThumbMid_R | arm_R_ref_armor_thumb_mid | hands | arms | surface | shell | arm_R_thumb_mid |
| RefArmor_ThumbTip_L | arm_L_ref_armor_thumb_tip | hands | arms | surface | shell | arm_L_thumb_tip |
| RefArmor_ThumbTip_R | arm_R_ref_armor_thumb_tip | hands | arms | surface | shell | arm_R_thumb_tip |
| RefArmor_Thumb_L | arm_L_ref_armor_thumb | hands | arms | hull | shell | arm_L_thumb |
| RefArmor_Thumb_R | arm_R_ref_armor_thumb | hands | arms | hull | shell | arm_R_thumb |
| RefBackMount1_L | torso_L_ref_back_mount1 | upper_body | upper_body | hull | graphite | torso_torso_core |
| RefBackMount1_R | torso_R_ref_back_mount1 | upper_body | upper_body | hull | graphite | torso_torso_core |
| RefBackMount2_L | torso_L_ref_back_mount2 | upper_body | upper_body | hull | graphite | torso_torso_core |
| RefBackMount2_R | torso_R_ref_back_mount2 | upper_body | upper_body | hull | graphite | torso_torso_core |
| RefBackMountScrew1_L | torso_L_ref_back_mount_screw1 | upper_body | upper_body | surface | metal | torso_torso_core |
| RefBackMountScrew1_R | torso_R_ref_back_mount_screw1 | upper_body | upper_body | surface | metal | torso_torso_core |
| RefBackMountScrew2_L | torso_L_ref_back_mount_screw2 | upper_body | upper_body | surface | metal | torso_torso_core |
| RefBackMountScrew2_R | torso_R_ref_back_mount_screw2 | upper_body | upper_body | surface | metal | torso_torso_core |
| RefBackPanel1_L | torso_L_ref_back_panel1 | upper_body | upper_body | hull | shell | torso_torso_core |
| RefBackPanel1_R | torso_R_ref_back_panel1 | upper_body | upper_body | hull | shell | torso_torso_core |
| RefBackPanel2_L | torso_L_ref_back_panel2 | upper_body | upper_body | hull | shell | torso_torso_core |
| RefBackPanel2_R | torso_R_ref_back_panel2 | upper_body | upper_body | hull | shell | torso_torso_core |
| RefPin_finger1_L | arm_L_ref_pin_finger1 | hands | arms | hull | dark_metal | arm_L_finger1 |
| RefPin_finger1_R | arm_R_ref_pin_finger1 | hands | arms | hull | dark_metal | arm_R_finger1 |
| RefPin_finger2_L | arm_L_ref_pin_finger2 | hands | arms | hull | dark_metal | arm_L_finger2 |
| RefPin_finger2_R | arm_R_ref_pin_finger2 | hands | arms | hull | dark_metal | arm_R_finger2 |
| RefPin_finger3_L | arm_L_ref_pin_finger3 | hands | arms | hull | dark_metal | arm_L_finger3 |
| RefPin_finger3_R | arm_R_ref_pin_finger3 | hands | arms | hull | dark_metal | arm_R_finger3 |
| RefPin_finger4_L | arm_L_ref_pin_finger4 | hands | arms | hull | dark_metal | arm_L_finger4 |
| RefPin_finger4_R | arm_R_ref_pin_finger4 | hands | arms | hull | dark_metal | arm_R_finger4 |
| RefPin_fingermid1_L | arm_L_ref_pin_fingermid1 | hands | arms | hull | dark_metal | arm_L_finger_mid1 |
| RefPin_fingermid1_R | arm_R_ref_pin_fingermid1 | hands | arms | hull | dark_metal | arm_R_finger_mid1 |
| RefPin_fingermid2_L | arm_L_ref_pin_fingermid2 | hands | arms | hull | dark_metal | arm_L_finger_mid2 |
| RefPin_fingermid2_R | arm_R_ref_pin_fingermid2 | hands | arms | hull | dark_metal | arm_R_finger_mid2 |
| RefPin_fingermid3_L | arm_L_ref_pin_fingermid3 | hands | arms | hull | dark_metal | arm_L_finger_mid3 |
| RefPin_fingermid3_R | arm_R_ref_pin_fingermid3 | hands | arms | hull | dark_metal | arm_R_finger_mid3 |
| RefPin_fingermid4_L | arm_L_ref_pin_fingermid4 | hands | arms | hull | dark_metal | arm_L_finger_mid4 |
| RefPin_fingermid4_R | arm_R_ref_pin_fingermid4 | hands | arms | hull | dark_metal | arm_R_finger_mid4 |
| RefPin_fingertip1_L | arm_L_ref_pin_fingertip1 | hands | arms | hull | dark_metal | arm_L_finger_tip1 |
| RefPin_fingertip1_R | arm_R_ref_pin_fingertip1 | hands | arms | hull | dark_metal | arm_R_finger_tip1 |
| RefPin_fingertip2_L | arm_L_ref_pin_fingertip2 | hands | arms | hull | dark_metal | arm_L_finger_tip2 |
| RefPin_fingertip2_R | arm_R_ref_pin_fingertip2 | hands | arms | hull | dark_metal | arm_R_finger_tip2 |
| RefPin_fingertip3_L | arm_L_ref_pin_fingertip3 | hands | arms | hull | dark_metal | arm_L_finger_tip3 |
| RefPin_fingertip3_R | arm_R_ref_pin_fingertip3 | hands | arms | hull | dark_metal | arm_R_finger_tip3 |
| RefPin_fingertip4_L | arm_L_ref_pin_fingertip4 | hands | arms | hull | dark_metal | arm_L_finger_tip4 |
| RefPin_fingertip4_R | arm_R_ref_pin_fingertip4 | hands | arms | hull | dark_metal | arm_R_finger_tip4 |
| RefPin_thumb_L | arm_L_ref_pin_thumb | hands | arms | hull | dark_metal | arm_L_thumb |
| RefPin_thumb_R | arm_R_ref_pin_thumb | hands | arms | hull | dark_metal | arm_R_thumb |
| RefPin_thumbmid_L | arm_L_ref_pin_thumbmid | hands | arms | hull | dark_metal | arm_L_thumb_mid |
| RefPin_thumbmid_R | arm_R_ref_pin_thumbmid | hands | arms | hull | dark_metal | arm_R_thumb_mid |
| RefPin_thumbtip_L | arm_L_ref_pin_thumbtip | hands | arms | hull | dark_metal | arm_L_thumb_tip |
| RefPin_thumbtip_R | arm_R_ref_pin_thumbtip | hands | arms | hull | dark_metal | arm_R_thumb_tip |
| RibPlate | torso_rib_plate | upper_body | upper_body | surface | shell | torso_torso_core |
| RibStripe | torso_rib_stripe | upper_body | upper_body | hull | graphite | torso_torso_core |
| SIL_Cam | nicht übernehmen: CAMERA / Scene Collection | — | — | — | — | — |
| Seat | pelvis_seat | pelvis | upper_body | surface | shell | pelvis_pelvis_core |
| Sensor | torso_sensor | upper_body | upper_body | surface | glass | torso_torso_core |
| SensorBezel | torso_sensor_bezel | upper_body | upper_body | hull | dark_metal | torso_torso_core |
| SensorHousing | torso_sensor_housing | upper_body | upper_body | hull | dark_metal | torso_torso_core |
| ShinBolt1_L | shin_L_shin_bolt1 | shins | legs | surface | metal | shin_L_shin |
| ShinBolt1_R | shin_R_shin_bolt1 | shins | legs | surface | metal | shin_R_shin |
| ShinBolt2_L | shin_L_shin_bolt2 | shins | legs | surface | metal | shin_L_shin |
| ShinBolt2_R | shin_R_shin_bolt2 | shins | legs | surface | metal | shin_R_shin |
| ShinChevron_L | shin_L_shin_chevron | shins | legs | surface | graphite | shin_L_shin |
| ShinChevron_R | shin_R_shin_chevron | shins | legs | surface | graphite | shin_R_shin |
| Shin_L | shin_L_shin | shins | legs | surface | shell | thigh_L_thigh_core |
| Shin_R | shin_R_shin | shins | legs | surface | shell | thigh_R_thigh_core |
| ShoulderBlockCore_L | torso_L_shoulder_block_core | shoulders | arms | hull | graphite | torso_torso_core |
| ShoulderBlockCore_R | torso_R_shoulder_block_core | shoulders | arms | hull | graphite | torso_torso_core |
| ShoulderBlockLower_L | torso_L_shoulder_block_lower | shoulders | arms | surface | graphite | torso_L_shoulder_block |
| ShoulderBlockLower_R | torso_R_shoulder_block_lower | shoulders | arms | surface | graphite | torso_R_shoulder_block |
| ShoulderBlock_L | torso_L_shoulder_block | shoulders | arms | surface | shell | torso_L_shoulder_block_core |
| ShoulderBlock_R | torso_R_shoulder_block | shoulders | arms | surface | shell | torso_R_shoulder_block_core |
| ShoulderBolt1_L | torso_L_shoulder_bolt1 | shoulders | arms | surface | metal | torso_L_shoulder_block |
| ShoulderBolt1_R | torso_R_shoulder_bolt1 | shoulders | arms | surface | metal | torso_R_shoulder_block |
| ShoulderBolt2_L | torso_L_shoulder_bolt2 | shoulders | arms | surface | metal | torso_L_shoulder_block |
| ShoulderBolt2_R | torso_R_shoulder_bolt2 | shoulders | arms | surface | metal | torso_R_shoulder_block |
| ShoulderJoint_L | arm_L_shoulder_joint | shoulders | arms | hull | graphite | torso_L_shoulder_block_core |
| ShoulderJoint_R | arm_R_shoulder_joint | shoulders | arms | hull | graphite | torso_R_shoulder_block_core |
| ShoulderMed_L_BCap | arm_L_shoulder_med_bcap | shoulders | arms | hull | dark_metal | torso_L_shoulder_block_core |
| ShoulderMed_L_BDisc | arm_L_shoulder_med_bdisc | shoulders | arms | hull | dark_metal | torso_L_shoulder_block_core |
| ShoulderMed_L_BHub | arm_L_shoulder_med_bhub | shoulders | arms | hull | dark_metal | torso_L_shoulder_block_core |
| ShoulderMed_L_BHubBolt1 | arm_L_shoulder_med_bhub_bolt1 | shoulders | arms | surface | metal | torso_L_shoulder_block_core |
| ShoulderMed_L_BHubBolt2 | arm_L_shoulder_med_bhub_bolt2 | shoulders | arms | surface | metal | torso_L_shoulder_block_core |
| ShoulderMed_L_BHubBolt3 | arm_L_shoulder_med_bhub_bolt3 | shoulders | arms | surface | metal | torso_L_shoulder_block_core |
| ShoulderMed_L_BHubBolt4 | arm_L_shoulder_med_bhub_bolt4 | shoulders | arms | surface | metal | torso_L_shoulder_block_core |
| ShoulderMed_L_BRecess | arm_L_shoulder_med_brecess | shoulders | arms | hull | dark_metal | torso_L_shoulder_block_core |
| ShoulderMed_L_BRing | arm_L_shoulder_med_bring | shoulders | arms | loft | metal | torso_L_shoulder_block_core |
| ShoulderMed_L_FCap | arm_L_shoulder_med_fcap | shoulders | arms | hull | dark_metal | torso_L_shoulder_block_core |
| ShoulderMed_L_FDisc | arm_L_shoulder_med_fdisc | shoulders | arms | hull | dark_metal | torso_L_shoulder_block_core |
| ShoulderMed_L_FHub | arm_L_shoulder_med_fhub | shoulders | arms | hull | dark_metal | torso_L_shoulder_block_core |
| ShoulderMed_L_FHubBolt1 | arm_L_shoulder_med_fhub_bolt1 | shoulders | arms | surface | metal | torso_L_shoulder_block_core |
| ShoulderMed_L_FHubBolt2 | arm_L_shoulder_med_fhub_bolt2 | shoulders | arms | surface | metal | torso_L_shoulder_block_core |
| ShoulderMed_L_FHubBolt3 | arm_L_shoulder_med_fhub_bolt3 | shoulders | arms | surface | metal | torso_L_shoulder_block_core |
| ShoulderMed_L_FHubBolt4 | arm_L_shoulder_med_fhub_bolt4 | shoulders | arms | surface | metal | torso_L_shoulder_block_core |
| ShoulderMed_L_FRecess | arm_L_shoulder_med_frecess | shoulders | arms | hull | dark_metal | torso_L_shoulder_block_core |
| ShoulderMed_L_FRing | arm_L_shoulder_med_fring | shoulders | arms | loft | metal | torso_L_shoulder_block_core |
| ShoulderMed_R_BCap | arm_R_shoulder_med_bcap | shoulders | arms | hull | dark_metal | torso_R_shoulder_block_core |
| ShoulderMed_R_BDisc | arm_R_shoulder_med_bdisc | shoulders | arms | hull | dark_metal | torso_R_shoulder_block_core |
| ShoulderMed_R_BHub | arm_R_shoulder_med_bhub | shoulders | arms | hull | dark_metal | torso_R_shoulder_block_core |
| ShoulderMed_R_BHubBolt1 | arm_R_shoulder_med_bhub_bolt1 | shoulders | arms | surface | metal | torso_R_shoulder_block_core |
| ShoulderMed_R_BHubBolt2 | arm_R_shoulder_med_bhub_bolt2 | shoulders | arms | surface | metal | torso_R_shoulder_block_core |
| ShoulderMed_R_BHubBolt3 | arm_R_shoulder_med_bhub_bolt3 | shoulders | arms | surface | metal | torso_R_shoulder_block_core |
| ShoulderMed_R_BHubBolt4 | arm_R_shoulder_med_bhub_bolt4 | shoulders | arms | surface | metal | torso_R_shoulder_block_core |
| ShoulderMed_R_BRecess | arm_R_shoulder_med_brecess | shoulders | arms | hull | dark_metal | torso_R_shoulder_block_core |
| ShoulderMed_R_BRing | arm_R_shoulder_med_bring | shoulders | arms | loft | metal | torso_R_shoulder_block_core |
| ShoulderMed_R_FCap | arm_R_shoulder_med_fcap | shoulders | arms | hull | dark_metal | torso_R_shoulder_block_core |
| ShoulderMed_R_FDisc | arm_R_shoulder_med_fdisc | shoulders | arms | hull | dark_metal | torso_R_shoulder_block_core |
| ShoulderMed_R_FHub | arm_R_shoulder_med_fhub | shoulders | arms | hull | dark_metal | torso_R_shoulder_block_core |
| ShoulderMed_R_FHubBolt1 | arm_R_shoulder_med_fhub_bolt1 | shoulders | arms | surface | metal | torso_R_shoulder_block_core |
| ShoulderMed_R_FHubBolt2 | arm_R_shoulder_med_fhub_bolt2 | shoulders | arms | surface | metal | torso_R_shoulder_block_core |
| ShoulderMed_R_FHubBolt3 | arm_R_shoulder_med_fhub_bolt3 | shoulders | arms | surface | metal | torso_R_shoulder_block_core |
| ShoulderMed_R_FHubBolt4 | arm_R_shoulder_med_fhub_bolt4 | shoulders | arms | surface | metal | torso_R_shoulder_block_core |
| ShoulderMed_R_FRecess | arm_R_shoulder_med_frecess | shoulders | arms | hull | dark_metal | torso_R_shoulder_block_core |
| ShoulderMed_R_FRing | arm_R_shoulder_med_fring | shoulders | arms | loft | metal | torso_R_shoulder_block_core |
| SpineRing1 | pelvis_spine_ring1 | pelvis | upper_body | hull | graphite | pelvis_waist |
| SpineRing2 | pelvis_spine_ring2 | pelvis | upper_body | hull | graphite | pelvis_waist |
| SpineRing3 | pelvis_spine_ring3 | pelvis | upper_body | hull | graphite | pelvis_waist |
| Studio_Cyc | nicht übernehmen: MESH / STUDIO | — | — | — | — | — |
| ThighBolt1_L | thigh_L_thigh_bolt1 | thighs | legs | surface | metal | thigh_L_thigh_core |
| ThighBolt1_R | thigh_R_thigh_bolt1 | thighs | legs | surface | metal | thigh_R_thigh_core |
| ThighBolt2_L | thigh_L_thigh_bolt2 | thighs | legs | surface | metal | thigh_L_thigh_core |
| ThighBolt2_R | thigh_R_thigh_bolt2 | thighs | legs | surface | metal | thigh_R_thigh_core |
| ThighBolt3_L | thigh_L_thigh_bolt3 | thighs | legs | surface | metal | thigh_L_thigh_core |
| ThighBolt3_R | thigh_R_thigh_bolt3 | thighs | legs | surface | metal | thigh_R_thigh_core |
| ThighBolt4_L | thigh_L_thigh_bolt4 | thighs | legs | surface | metal | thigh_L_thigh_core |
| ThighBolt4_R | thigh_R_thigh_bolt4 | thighs | legs | surface | metal | thigh_R_thigh_core |
| ThighCore_L | thigh_L_thigh_core | thighs | legs | hull | graphite | pelvis_pelvis_core |
| ThighCore_R | thigh_R_thigh_core | thighs | legs | hull | graphite | pelvis_pelvis_core |
| ThighHatchBolt1_L | thigh_L_thigh_hatch_bolt1 | thighs | legs | surface | metal | thigh_L_thigh_core |
| ThighHatchBolt1_R | thigh_R_thigh_hatch_bolt1 | thighs | legs | surface | metal | thigh_R_thigh_core |
| ThighHatchBolt2_L | thigh_L_thigh_hatch_bolt2 | thighs | legs | surface | metal | thigh_L_thigh_core |
| ThighHatchBolt2_R | thigh_R_thigh_hatch_bolt2 | thighs | legs | surface | metal | thigh_R_thigh_core |
| ThighPlate_L | thigh_L_thigh_plate | thighs | legs | surface | graphite | thigh_L_thigh_core |
| ThighPlate_R | thigh_R_thigh_plate | thighs | legs | surface | graphite | thigh_R_thigh_core |
| ThighTrim_L | thigh_L_thigh_trim | thighs | legs | hull | metal | thigh_L_thigh_core |
| ThighTrim_R | thigh_R_thigh_trim | thighs | legs | hull | metal | thigh_R_thigh_core |
| Thigh_L | thigh_L_thigh | thighs | legs | surface | shell | thigh_L_thigh_core |
| Thigh_R | thigh_R_thigh | thighs | legs | surface | shell | thigh_R_thigh_core |
| ThumbMid_L | arm_L_thumb_mid | hands | arms | hull | graphite | arm_L_thumb |
| ThumbMid_R | arm_R_thumb_mid | hands | arms | hull | graphite | arm_R_thumb |
| ThumbTip_L | arm_L_thumb_tip | hands | arms | hull | graphite | arm_L_thumb_mid |
| ThumbTip_R | arm_R_thumb_tip | hands | arms | hull | graphite | arm_R_thumb_mid |
| Thumb_L | arm_L_thumb | hands | arms | hull | graphite | arm_L_palm |
| Thumb_R | arm_R_thumb | hands | arms | hull | graphite | arm_R_palm |
| ToeSeam_L | foot_L_toe_seam | feet | legs | hull | dark_metal | foot_L_boot_toe |
| ToeSeam_R | foot_R_toe_seam | feet | legs | hull | dark_metal | foot_R_boot_toe |
| TorsoCore | torso_torso_core | upper_body | upper_body | surface | graphite | pelvis_waist |
| UpperArmCore_L | arm_L_upper_arm_core | upper_arms | arms | hull | graphite | arm_L_upper_arm |
| UpperArmCore_R | arm_R_upper_arm_core | upper_arms | arms | hull | graphite | arm_R_upper_arm |
| UpperArm_L | arm_L_upper_arm | upper_arms | arms | surface | shell | torso_L_shoulder_block_core |
| UpperArm_R | arm_R_upper_arm | upper_arms | arms | surface | shell | torso_R_shoulder_block_core |
| Visor | helmet_visor | head | head | surface | graphite | helmet_helmet |
| VisorFrame | helmet_visor_frame | head | head | surface | graphite | helmet_helmet |
| Waist | pelvis_waist | pelvis | upper_body | hull | graphite | pelvis_pelvis_core |
| WristCuff_L | arm_L_wrist_cuff | forearms | arms | surface | shell | arm_L_forearm |
| WristCuff_R | arm_R_wrist_cuff | forearms | arms | surface | shell | arm_R_forearm |


## Zusätzliche Netzprüfung und bekannte Quellgrenzen

A-Position: positive Teilvolumina 554/554; keine Kante mit mehr als zwei Flächen. 7 bereits in der Quelle offene Teile werden ausdrücklich beibehalten; keine Engine-/Manifold-Gesamtfreigabe. 1733 sehr kleine Quell-/QHull-/CSG-Facetten (≤1e-11 m², einschließlich numerischer Nullflächen) sind separat benannt. Die Triangulierung ist haltungsabhängig, daher gilt diese Tabelle ausdrücklich für die A-Position. Beleg mesh-qa.json außerhalb des Repos.

| Teil | Randkanten | kleine Facetten | Grund |
|---|---:|---:|---|
| torso_back_panel_bolt1 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| torso_back_panel_bolt2 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| torso_backpack | 3 | 0 | Bereits gemessene offene Quellgeometrie; keine Engine-Freigabe |
| pelvis_L_belt_bolt | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| pelvis_R_belt_bolt | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| foot_L_boot_bolt1 | 0 | 9 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| foot_R_boot_bolt1 | 0 | 9 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| foot_L_boot_bolt2 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| foot_R_boot_bolt2 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| torso_chest | 0 | 3 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| helmet_L_ear_disc_ring | 0 | 10 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| helmet_R_ear_disc_ring | 0 | 10 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_elbow_cable | 16 | 0 | Bereits gemessene offene Quellgeometrie; keine Engine-Freigabe |
| arm_R_elbow_cable | 16 | 0 | Bereits gemessene offene Quellgeometrie; keine Engine-Freigabe |
| arm_L_elbow_med_ring | 0 | 80 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_elbow_med_ring | 0 | 73 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_forearm_bolt1 | 0 | 5 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_forearm_bolt1 | 0 | 5 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_forearm_bolt2 | 0 | 1 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_forearm_bolt2 | 0 | 1 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| helmet_helmet | 0 | 95 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_L_hip_med_ring | 0 | 131 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_R_hip_med_ring | 0 | 137 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| torso_L_hose | 20 | 0 | Bereits gemessene offene Quellgeometrie; keine Engine-Freigabe |
| torso_R_hose | 20 | 0 | Bereits gemessene offene Quellgeometrie; keine Engine-Freigabe |
| kneecap_L_knee_bolt1 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| kneecap_R_knee_bolt1 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| kneecap_L_knee_bolt2 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| kneecap_R_knee_bolt2 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_L_knee_cable | 16 | 0 | Bereits gemessene offene Quellgeometrie; keine Engine-Freigabe |
| thigh_R_knee_cable | 16 | 0 | Bereits gemessene offene Quellgeometrie; keine Engine-Freigabe |
| shin_L_knee_med_ihub_bolt1 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_L_knee_med_ihub_bolt2 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_L_knee_med_ihub_bolt3 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_L_knee_med_ihub_bolt4 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_L_knee_med_iring | 0 | 84 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_L_knee_med_ohub_bolt1 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_L_knee_med_ohub_bolt2 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_L_knee_med_ohub_bolt3 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_L_knee_med_ohub_bolt4 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_L_knee_med_oring | 0 | 33 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_R_knee_med_ihub_bolt1 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_R_knee_med_ihub_bolt2 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_R_knee_med_ihub_bolt3 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_R_knee_med_ihub_bolt4 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_R_knee_med_iring | 0 | 113 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_R_knee_med_ohub_bolt1 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_R_knee_med_ohub_bolt2 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_R_knee_med_ohub_bolt3 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_R_knee_med_ohub_bolt4 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_R_knee_med_oring | 0 | 37 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_r2_hand_screw1 | 0 | 7 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_r2_hand_screw1 | 0 | 7 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_r2_hand_screw2 | 0 | 7 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_r2_hand_screw2 | 0 | 7 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_r3_wrist_boltminus1 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_r3_wrist_boltminus1 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_r3_wrist_bolt1 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_r3_wrist_bolt1 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| torso_r5_sensor_light_ring | 0 | 88 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| torso_r5_sensor_outer_bezel | 0 | 56 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_L_shin_bolt1 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_R_shin_bolt1 | 0 | 7 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_L_shin_bolt2 | 0 | 7 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| shin_R_shin_bolt2 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| torso_L_shoulder_block_core | 0 | 16 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| torso_R_shoulder_block_core | 0 | 17 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| torso_L_shoulder_block_lower | 0 | 15 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| torso_R_shoulder_block_lower | 0 | 12 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| torso_L_shoulder_block | 0 | 3 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| torso_R_shoulder_block | 0 | 3 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_shoulder_med_bhub_bolt1 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_shoulder_med_bhub_bolt2 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_shoulder_med_bhub_bolt3 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_shoulder_med_bhub_bolt4 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_shoulder_med_bring | 0 | 75 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_shoulder_med_fhub_bolt1 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_shoulder_med_fhub_bolt2 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_shoulder_med_fhub_bolt3 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_shoulder_med_fhub_bolt4 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_L_shoulder_med_fring | 0 | 60 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_shoulder_med_bhub_bolt1 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_shoulder_med_bhub_bolt2 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_shoulder_med_bhub_bolt3 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_shoulder_med_bhub_bolt4 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_shoulder_med_bring | 0 | 82 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_shoulder_med_fhub_bolt1 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_shoulder_med_fhub_bolt2 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_shoulder_med_fhub_bolt3 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_shoulder_med_fhub_bolt4 | 0 | 4 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| arm_R_shoulder_med_fring | 0 | 80 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_L_thigh_bolt1 | 0 | 7 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_R_thigh_bolt1 | 0 | 7 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_L_thigh_bolt2 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_R_thigh_bolt2 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_L_thigh_bolt3 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_R_thigh_bolt3 | 0 | 8 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_L_thigh_bolt4 | 0 | 7 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_R_thigh_bolt4 | 0 | 7 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_L_thigh_hatch_bolt1 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_R_thigh_hatch_bolt1 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_L_thigh_hatch_bolt2 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |
| thigh_R_thigh_hatch_bolt2 | 0 | 6 | Gemessene Boolean-/Fasenfacette bzw. numerische QHull-/CSG-Tessellierung |

## Prüfung und Review

Aktueller Typ02-Stand auf Basis cf294c4: 32 gezielte Roboterprüfungen grün, einschließlich Gegenproben, A-/Referenz-Armtausch, Schulterkontakt, Zwei-Ebenen-Vertrag, measured_parts-Spec und Profil-CSG. Nach den Reviewkorrekturen wurden die 17 Modellprüfungen sowie die verbesserte Breiten-Gegenprobe gezielt erneut grün geprüft. Die exakten Dreieckszähler sind 264549 in A-Position und 260247 in Referenzhaltung; die Werte sind wegen der zusätzlichen inneren Freiraum-Cuts und der haltungsabhängigen CSG-Tessellierung gegenüber der alten Fassung geändert.

Vollständiger aktueller ./check über ./ce check: 502 Tests grün, 23 übersprungen, 856.564 Sekunden. Der frühere Lauf auf b721daf (477 Tests, 23 Skips) ist kein Nachweis für die neue Basis.

Zusätzlicher Pipeline-Nachweis im Speicher: GLB-Bau mit weiss_graphit erfolgreich, 554 Mesh-Knoten; basic_assembly/basic_group entsprechen bei jedem Knoten der neuen 10/4-Zuordnung. Keine GLB-Datei geschrieben.

Testzuordnung: Im Ausgangsrepo existiert kein test_map.json. unittest discover entdeckt über tests/robot/__init__.py beide Testdateien. Direkter Befehl: `.venv/bin/python -m unittest discover -s tests/robot -v`. Kein zusätzliches Zuordnungsformat eingeführt.

Unabhängiger numerischer Vertragsabgleich: A-Richtungen und Schulteröffnung entsprechen der 01-Semantik; Kappe und Arm teilen ihren Pivot bis auf Rundung im Bereich 0,000001 mm. Beide Haltungen warnungsfrei. CLI-Richter über ./ce judge --api mit Opus, weil Codex-Kontingent unter 15 Prozent: erster Auftrag teilweise abgeschnitten, keine Freigabe; zweiter vollständiger Auftrag nach Korrekturen ohne hohe Befunde. Niedriger Hinweis zur tautologischen Breiten-Gegenprobe durch einen echten Modellmutanten ersetzt (eingefrorene Kappe; gezielt grün). Der Kommentarverweis auf diesen vollständigen Bericht bleibt richtig; die große Zuordnungstabelle war bewusst nicht im API-Diff. Keine formale CLI-Freigabe behauptet. Geschätzte Gesamtkosten beider Prüfaufträge: 0,2691288 USD. Keine weitere Anfrage zur Fortsetzung abgeschnittener Antworten.
