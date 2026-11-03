# Für Sightline: was Formgen v2 an BALLONs Bau- und Exportweg fehlt (0.5 „Forge“, aktualisiert 0.6 „Hangar“)

**Stand 0.7 „Waypoint“ (03.11.2026):** BALLON 0.41 „Intake“ hat die Punkte 1, 2, 3 (Teil), 5 und Tabelle a–d umgesetzt
(BALLON `docs/formgen-schnittstelle.md`, Postfach #16 Kommentar 6599212878). Formgen nutzt am Pin `fe4a5dc` (BALLON 0.42):
`blender_build.main(W=…, base=…, argv=[…])` mit `basic/variant.as_module` statt eines Moduls in `sys.modules`,
`export_unity.bake_weapon(…, arms=False)` (Waffenatlas ohne Arme, Regel beider Wege) und die Weltpunkte `POINTS`; das Paket hat
`format_version` 2 mit Datensatz `model`. Offen bleiben e (Piloten 16/17), f (Gameplay je Variante), 6, 7, 8 und 9. Der Text unten
ist der Stand 0.6.

Status: Liste aus dem Machbarkeitsnachweis 0.5 (Arbeitsnummer 0.3, 02.11.2026), in 0.6 nachgeführt (alle Linien auf den
v2.1-Piloten, Stufe `asset`, Bake-Probe BA01/BD01). BALLON wurde nicht geändert; gelesen am Pin
`dcdda603f6567d4d62a10d968d7987e1c5292643` (`basic/kit.py`, `tools/blender_build.py`, `tools/bake_unity.py`,
`tools/export_unity.py`, `tools/ego_build.py`, `basic/arms/ego.py`). Formgen ruft diese Dateien aus einem `git archive`-Schnappschuss
auf (`formgen/ballon_kit.py`, `formgen/blender/asset_build.py`).

1. **Datenübergabe an `blender_build.main`.** Das Werkzeug lädt die Waffe nur über den Modulnamen (`basic.<name>` bzw.
   `basic.weapons.<name>`). Formgen hängt dafür je Lauf ein erzeugtes Modul `basic.weapons.formgen_<ID>` in `sys.modules`.
   Wunsch: `main(W=None)` oder `build_weapon(W, out)` mit Modulobjekt bzw. Datensatz.
2. **Spielpaket ohne Ego-Szene.** `export_unity.bake_weapon(sc, e, …)` braucht eine `ego_build.Scene` (Arme, `set_weapon`,
   `rest_pose`) und schreibt fest nach `DST` (`unity/Assets/Ballon/Generated`). Formgen ruft deshalb die Einzelschritte
   (`apply_modifiers`, `unwrap`, `bake_atlas`, `mesh_bounds`, `export_fbx`, `store_textures`) selbst in derselben Reihenfolge auf –
   ohne Arme in der Szene. **0.6 geprüft:** Die Arme verändern den Waffenatlas – BA01 (Pilot unverändert) gegen BALLONs
   eingecheckten Unity-Atlas von BASIC-01-v2.1: Normalen identisch, Albedo Ø 0,32/255 (PSNR 40,5 dB), Spec Ø 0,16 (45 dB),
   AO aber Ø 19,8 (PSNR 12,9 dB): unser AO ist nirgends dunkler, in 8,7 % der belegten Texel heller; BALLONs AO trägt
   handförmige Verschattungen auf Griff- und Gehäusefeldern (Schatten der Ego-Hände). Frage an BALLON: gehören Handschatten in den
   Waffenatlas (sie liegen auch an Stellen, die in anderen Haltungen sichtbar sind)? Wunsch: `bake_weapon(root, objs, out_dir,
   atlas_key, skins, arms=True|False)` ohne Szenenobjekt und mit Zielordner. Beleg `~/Library/Caches/CubeEscapeFormgen2/0.6/belege/bake_check.json`.
3. **Waffenliste fest im Code.** `export_unity.WEAPONS`, `SKIN_WEAPONS`, `ATLAS_KEY` und `ego.CLASSES`/`profile` kennen nur BALLONs
   Module. Ein Eintrag in `ego.json` für eine Formgen-Variante (Haltungen, Griffe, Live-Teile, Auswurf) entsteht damit nicht.
   `export_unity.weapon_data(W, live)` läuft für Formgen-Varianten (geprüft für BASIC-01-v2.1 als Variante: identisch zum
   eingecheckten `ego.json`; 0.6: BA01 und BD01 liefern den Block im Paket), die übrigen Felder von `weapon_entry` (Haltungen,
   Griffe, Gameplay, Atlasname) nicht ohne Eintrag in `WEAPONS`/`ATLAS_KEY`. Wunsch: `weapon_entry(W, atlas_key)` für ein
   fremdes Modul und ein Einleseort für Formgen-Pakete (z. B. `Generated/Formgen/<ID>/`), aus dem der Unity-Import Material und
   Prefab erzeugt.
4. **Ego-Profil der Formstudien.** Die Klasse `auto_rifle` ist auf den Piloten abgestimmt: Mit der Formstudie BASIC-01
   (`basic/weapons/w01_auto_rifle.py`) liegt die Zielen-Kamera unter dem Visier (Beleg `ego_contact.png`, Spalte „ads · ego“).
   Für Spielvarianten auf Formstudien-Basis fehlt ein Ego-Profil; mit Piloten-Basis passt es. **0.6:** alle Linien stehen auf
   den Piloten; betroffen sind nur noch BASIC-16/17 (Schwert, Glefe), die ohnehin keine Ego-Klasse haben – BALLON-Piloten für
   16/17 würden die letzte Formstudien-Lücke schließen.
5. **Anker außerhalb von ANCHORS.** `EJECT['at']`, `EGO_GRIPS[..]['contact']` und Ähnliches stehen als Modulfelder in Autorenmaß.
   Wird eine Waffe gedehnt, wandern sie nicht mit. Wunsch: alle Weltpunkte als Anker mit Teilbezug (wie `ANCHORS`). 0.6: Der
   vordere Schnitt liegt zwischen Stützhand und Mündung, der hintere im Schaft – Auswurf (BASIC-01 f = 53 mm) und Griffkontakte
   liegen meist diesseits und bleiben richtig; bei gestauchten Linien (C, E, G) und Visier-/Schafttausch ist das nicht
   je Typ geprüft.
6. **Veraltete Ausgaben im BALLON-Cache.** `~/Library/Caches/CubeEscapeBallon/out/BASIC-01/BASIC-01.glb` (24.10.2026) hat dieselben
   5 852 Dreiecke an denselben Positionen wie ein Neubau am Pin, aber 9 432 statt 5 341 Vertices (Normalen-Splits vor 0.32
   „harden_normals“). `out/BASIC-01-v2.1/` (25.10.2026) passt nicht mehr zum Spec am Pin. Ein Neubau von `out/` würde das angleichen.
   0.6 gemessen (`tools/line_a_parity.py`): Linie A ist bei allen 17 Typen bytegleich zu einem Neubau am Pin; BALLONs Cache-GLB
   ist genau bei den sechs Typen gleich, deren Spec neben der GLB dem Pin entspricht (07, 13–17), bei den übrigen elf nicht.
7. **Texturablage bei kleinerem Atlas.** `store_texture` skaliert auf `TEXTURE_STORE[kind]['size']` – ein Atlas unter 4096² wird dabei
   hochskaliert (gesehen bei einem 512²-Probelauf). Kein Fehler im Spielbetrieb, aber ein Schalter „nicht vergrößern“ wäre sauberer.
8. **Skins im Atlas (0.6).** BALLON backt je Waffe den Standardatlas und für `SKIN_WEAPONS` je Skin Farbe/Glanz (`color_only`).
   Formgen backt je Blatt nur den Skin der Linie (vollständiger Atlas). Für Unity reicht das je Variante; soll eine Variante
   mehrere Skins tragen, braucht es BALLONs Skin-Schleife mit Zielordner (siehe Nr. 2).
9. **Bake-Dauer (0.6 gemessen).** BA01 + BD01: 695 s auf der M5-GPU (4096², 64 Samples), ≈ 5,8 min je Blatt mit Skin. Alle 136
   Blätter ≈ 13 h – deshalb nur auf Anforderung (`--bake`), gecacht.

## Was für Unity-Spielbarkeit noch BALLON-seitig fehlt (Stand 0.6)

| # | Fehlt | Wirkung | Wunsch an BALLON |
|---|---|---|---|
| a | Einleseweg für fremde Pakete (FBX + Atlas + Manifest) in `unity/` samt Material/Prefab/Icon | Paket liegt fertig vor, Unity kennt es nicht | Ordnerkonvention und Import im Editor-Skript (Nr. 3) |
| b | `ego.json`-Eintrag je Variante (Haltungen, Griffe, Gameplay) | Waffe nicht in der Ego-Auswahl | `weapon_entry(W, atlas_key)` ohne Liste `WEAPONS` (Nr. 3) |
| c | Weltpunkte als Anker (Auswurf, Griffkontakte, Mündungsfeuer) | gedehnte Varianten: Effekte/Hände evtl. versetzt | Anker mit Teilbezug (Nr. 5) |
| d | Bake ohne Ego-Szene, mit Zielordner, Arme wählbar | AO weicht ab (Handschatten), Formgen ruft Einzelschritte | `bake_weapon(…)`-Schnittstelle (Nr. 2) |
| e | Piloten für BASIC-16/17 | zwei Typen bleiben Formstudie | Piloten oder Entscheid „nur Konzept“ (Nr. 4) |
| f | Gameplay-Werte je Variante | Varianten erben die Werte des Typs | Felder im Modul oder in der Variante |
