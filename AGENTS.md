# Formgen v2 – Regeln für alle Agenten

Es gelten die globalen Regeln (Quelle: cubeescape-nexogen). Der aktuelle Nutzerauftrag steht in `docs/auftrag-codex-formgen-v2.md`; direkte Nutzeranweisungen haben Vorrang.

## Harter Kern

Quelle: Nexogen `templates/kern.md`, nur dort ändern; gilt auch in Cloud-Sitzungen.

1. Kein Commit direkt auf `main`.
2. Kein Force-Push, keine überschriebenen Branches oder Tags.
3. Nichts Fremdes anfassen oder löschen: andere Sitzungen, Worktrees, Stash, Haupt-Checkout.
4. Merge nach `main` nur mit Ja des Nutzers, außer Patch bis 100 Zeilen ohne Format, Vertrag, Kernpfad bei grünem `merge-check`; Tag, Release, Repo öffentlich machen immer nur mit Ja.
5. Tests nie löschen oder abschwächen, um grün zu werden.
6. Keine Zugangsdaten, kein fremdes Material, keine großen Binärdaten nach außen (öffentliche Repos, fremde APIs).
7. Formate, Verträge und IDs nur mit Migration; IDs sind ewig.
8. Nichts als fertig melden, was nicht geprüft ist.

## Projekt

- Eine Pipeline unter `formgen/`: eigene Python-Modelle in ballons kit-Vokabular, keine v1-Modellsprache. Waffen ab 0.2 nur über `formgen.pipeline`: Grundform = BALLON-Typ per Quellhash (gepinnter Commit in `config.toml`), Varianten nur über Parameter im Register `data/variants.toml` ([Generator](docs/generator.md)).
- EXTENDED (0.15–0.28) sind eigene Modelle unter `formgen/models/extended/` (Blatt `EA<NN>`); ihre Linien EB–EN (0.38) nur im Register `data/extended_lines.toml` über `python -m formgen.extended_lines new`, ohne Verkleidung; Skins als Finish frei wählbar ([EXTENDED](docs/extended.md)).
- ZERO (0.46, Impulsgewehr ZA03 seit 0.49) sind eigene Modelle unter `formgen/models/zero/` (Blatt `ZA<NN>`), geladen und gerendert wie EXTENDED über `formgen.extended` (Kurzname `z<NN>`, NN = laufende ZERO-Nummer); noch ohne Linien, Blattweg und Website ([ZERO](docs/zero.md)).
- Designsprache für neue Waffen: [Design-Kanon](docs/design-kanon.md) (0.42); Zahlen nur über `python -m formgen.kanon messen`, Paket über `paket`.
- Serie DaVinci (0.52): eigene Serie neben EXTENDED, Modelle unter `formgen/models/davinci/`, Register `formgen/davinci.py` (Blatt `D<Linie><NN>`, je Modell ein Signature-Skin in `skins.toml`); Vorschau und Export über `python -m formgen.davinci` ([DaVinci](docs/davinci.md)).
- Roboter: Basic-Typen wie die Waffen, heute RoboterBasic-01 (Blatt `RA01`) und RoboterBasic-02 (`RA02`), weitere Typen über das Register. Quelle fest in diesem Repo unter `formgen/models/robot/`, Typen und Linien nur im Register `data/robots.toml`, Formvarianten je Einzelteil nur im Katalog `formgen/models/robot/catalog/` (Wahl je Linie in `[lines.parts]`, 0.14), Bau `python -m formgen.robot` ([Roboter](docs/robot.md)). Keine Verbindung zu Critic, weder Laufzeit noch Build; Brücke zu BALLON kommt später. Grundhaltung A-Position. Abnahme von RA01 in der Referenzhaltung gegen `RoboterBasic-01.glb` der Sicherung vom 05.11.2026: Front/Rücken/beide Seiten IoU ≥ 0,90; Bandbreite 0,92–1,08 (`python -m formgen.robot.silhouette <referenz.glb> --referenzhaltung`). R01/R02 und ihre Contour-Module erscheinen nicht auf der Website.
- KI-Generierung ist optional. Modelle und Standardbau dürfen davon nicht abhängen.

## Wahrheit und Aktualität

Code ist die Wahrheit, dann `docs/` und [CHANGELOG.md](CHANGELOG.md); der Stand kommt aus Git, nie aus alten Prompts.

- Formgen v1 und ballon sind ausschließlich Lesereferenzen; v1 ist eingefrorenes Archiv (keine Migration, kein Golden-Vergleich gegen v1). Vorschläge an ballon nur unter `docs/` hier.
- Bestehende v1-Waffen und Visiere ausschließlich als Geo-Export importieren. Keine alten Modellmodule kopieren.

## Befehle

- Bilder auf dem Mac, Sperre `ce lock blender -- …` (Waffen-Pipeline und `formgen.robot`, CPU-Rasterizer; Contour-Roboter weiter `gpu`); Hintergrund mittelgrau, kein Bloom.
- Vor Commit `./check` und gezielte Tests.

## Regeln

- Variantenregel (aus v1): Kennbuchstabe A–Z ohne I/O, englischer Name 1–3 Wörter ≤ 16 Zeichen, nichts doppelt; Eintrag nur über `python -m formgen.variants new`. Blatt-ID `B<Buchstabe><NN>`; vergebene IDs sind ewig. Blatt-Spec `formgenv2/weapon-sheet-spec` v1: Formatänderung nur mit Migration und Test.
- Erst `docs/modellsprache.md` und Mini-Modell, dann Cache-Abnahme mit echtem Dummy-Artefakt; vor deren Erfolg kein Rendering.
- Komponenten und Artefakte getrennt cachen; ohne `--force` nur Fehlendes/Veraltetes bauen. Nie ungefragt alles neu rendern.
- Jede Modellzahl hat eine Herkunft (Vorgabe, gemessen, Annahme). Farben nur in `skins.toml`.
- Hauptagent verantwortet Schnittstellen, VERSION-Konstanten, Integration und Commits. Jeder Unteragent schreibt nur zugewiesene Dateien.

## Definition of Done

- Viewer-Regel (aus v1): nach jeder Varianten-Sitzung Blätter, Vorschauen und `out/index.html` lokal bauen und sichten; nur Specs/Prompts/Golden committen; Lieferung als Release-Asset (`formgen.release_assets`), nie Blätter committen.
- Unabhängiger Prüfagent ohne Implementierung nimmt Ergebnisse vor Nutzermeldungen ab.
- Blätter, Ansichten, Vorschauen, Geo und Release-Zips sind gitignoriert. Specs/Prompts bleiben im Repo; Belege extern.
