# Für Sightline: was Formgen v2 an BALLONs Bau- und Exportweg fehlt (0.3 „Forge“)

Status: Liste aus dem Machbarkeitsnachweis 0.3 (02.11.2026). BALLON wurde nicht geändert; gelesen am Pin
`dcdda603f6567d4d62a10d968d7987e1c5292643` (`basic/kit.py`, `tools/blender_build.py`, `tools/bake_unity.py`,
`tools/export_unity.py`, `tools/ego_build.py`, `basic/arms/ego.py`). Formgen ruft diese Dateien aus einem `git archive`-Schnappschuss
auf (`formgen/ballon_kit.py`, `formgen/blender/asset_build.py`).

1. **Datenübergabe an `blender_build.main`.** Das Werkzeug lädt die Waffe nur über den Modulnamen (`basic.<name>` bzw.
   `basic.weapons.<name>`). Formgen hängt dafür je Lauf ein erzeugtes Modul `basic.weapons.formgen_<ID>` in `sys.modules`.
   Wunsch: `main(W=None)` oder `build_weapon(W, out)` mit Modulobjekt bzw. Datensatz.
2. **Spielpaket ohne Ego-Szene.** `export_unity.bake_weapon(sc, e, …)` braucht eine `ego_build.Scene` (Arme, `set_weapon`,
   `rest_pose`) und schreibt fest nach `DST` (`unity/Assets/Ballon/Generated`). Formgen ruft deshalb die Einzelschritte
   (`apply_modifiers`, `unwrap`, `bake_atlas`, `mesh_bounds`, `export_fbx`, `store_textures`) selbst in derselben Reihenfolge auf –
   ohne Arme in der Szene. Offen: Die Arme liegen bei BALLON beim AO-Backen mit in der Szene; ob das den Waffenatlas verändert,
   ist nicht geprüft. Wunsch: `bake_weapon(root, objs, out_dir, atlas_key, skins)` ohne Szenenobjekt und mit Zielordner.
3. **Waffenliste fest im Code.** `export_unity.WEAPONS`, `SKIN_WEAPONS`, `ATLAS_KEY` und `ego.CLASSES`/`profile` kennen nur BALLONs
   Module. Ein Eintrag in `ego.json` für eine Formgen-Variante (Haltungen, Griffe, Live-Teile, Auswurf) entsteht damit nicht.
   `export_unity.weapon_data(W, live)` läuft für Formgen-Varianten (geprüft für BASIC-01-v2.1 als Variante: identisch zum
   eingecheckten `ego.json`), die übrigen Felder von `weapon_entry` nicht ohne Waffenmodul.
4. **Ego-Profil der Formstudien.** Die Klasse `auto_rifle` ist auf den Piloten abgestimmt: Mit der Formstudie BASIC-01
   (`basic/weapons/w01_auto_rifle.py`) liegt die Zielen-Kamera unter dem Visier (Beleg `ego_contact.png`, Spalte „ads · ego“).
   Für Spielvarianten auf Formstudien-Basis fehlt ein Ego-Profil; mit Piloten-Basis passt es.
5. **Anker außerhalb von ANCHORS.** `EJECT['at']`, `EGO_GRIPS[..]['contact']` und Ähnliches stehen als Modulfelder in Autorenmaß.
   Wird eine Waffe gedehnt, wandern sie nicht mit. Wunsch: alle Weltpunkte als Anker mit Teilbezug (wie `ANCHORS`).
6. **Veraltete Ausgaben im BALLON-Cache.** `~/Library/Caches/CubeEscapeBallon/out/BASIC-01/BASIC-01.glb` (24.10.2026) hat dieselben
   5 852 Dreiecke an denselben Positionen wie ein Neubau am Pin, aber 9 432 statt 5 341 Vertices (Normalen-Splits vor 0.32
   „harden_normals“). `out/BASIC-01-v2.1/` (25.10.2026) passt nicht mehr zum Spec am Pin. Ein Neubau von `out/` würde das angleichen.
7. **Texturablage bei kleinerem Atlas.** `store_texture` skaliert auf `TEXTURE_STORE[kind]['size']` – ein Atlas unter 4096² wird dabei
   hochskaliert (gesehen bei einem 512²-Probelauf). Kein Fehler im Spielbetrieb, aber ein Schalter „nicht vergrößern“ wäre sauberer.
