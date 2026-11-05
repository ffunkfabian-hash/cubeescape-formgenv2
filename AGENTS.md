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

## Formgen v2

- Eine Pipeline unter `formgen/`: eigene Python-Modelle in ballons kit-Vokabular, keine v1-Modellsprache. Waffen ab 0.2 nur über `formgen.pipeline`: Grundform = BALLON-Typ per Quellhash (gepinnter Commit in `config.toml`), Varianten nur über Parameter im Register `data/variants.toml` ([Generator](docs/generator.md)).
- Variantenregel (aus v1): Kennbuchstabe A–Z ohne I/O, englischer Name 1–3 Wörter ≤ 16 Zeichen, nichts doppelt; Eintrag nur über `python -m formgen.variants new`. Blatt-ID `B<Buchstabe><NN>`; vergebene IDs sind ewig. Blatt-Spec `formgenv2/weapon-sheet-spec` v1: Formatänderung nur mit Migration und Test.
- Viewer-Regel (aus v1): nach jeder Varianten-Sitzung Blätter, Vorschauen und `out/index.html` lokal bauen und sichten; nur Specs/Prompts/Golden committen; Lieferung als Release-Asset (`formgen.release_assets`), nie Blätter committen.
- Formgen v1 und ballon sind ausschließlich Lesereferenzen; v1 ist eingefrorenes Archiv (keine Migration, kein Golden-Vergleich gegen v1). Vorschläge an ballon nur unter `docs/` hier.
- Bestehende v1-Waffen und Visiere ausschließlich als Geo-Export importieren. Keine alten Modellmodule kopieren.
- Erst `docs/modellsprache.md` und Mini-Modell, dann Cache-Abnahme mit echtem Dummy-Artefakt; vor deren Erfolg kein Rendering.
- Hauptagent verantwortet Schnittstellen, VERSION-Konstanten, Integration und Commits. Jeder Unteragent schreibt nur zugewiesene Dateien.
- Unabhängiger Prüfagent ohne Implementierung nimmt Ergebnisse vor Nutzermeldungen ab.
- Komponenten und Artefakte getrennt cachen; ohne `--force` nur Fehlendes/Veraltetes bauen. Nie ungefragt alles neu rendern.
- Jede Modellzahl hat eine Herkunft (Vorgabe, gemessen, Annahme). Farben nur in `skins.toml`.
- Bilder auf dem Mac, Sperre `ce lock blender -- …` (Waffen-Pipeline und `formgen.robot`, CPU-Rasterizer; Contour-Roboter weiter `gpu`); Hintergrund mittelgrau, kein Bloom.
- Roboter: Basic-Typen wie die Waffen, heute RoboterBasic-01 (Blatt `RA01`), weitere Typen (`RA02`) über das Register. Quelle fest in diesem Repo unter `formgen/models/robot/`, Typen und Linien nur im Register `data/robots.toml`, Bau `python -m formgen.robot` ([Roboter](docs/robot.md)). Keine Verbindung zu Critic, weder Laufzeit noch Build; Brücke zu BALLON kommt später. Grundhaltung A-Position. Abnahme von RA01 in der Referenzhaltung gegen `RoboterBasic-01.glb` der Sicherung vom 05.11.2026: Front/Rücken/beide Seiten IoU ≥ 0,90; Bandbreite 0,92–1,08 (`python -m formgen.robot.silhouette <referenz.glb> --referenzhaltung`). R01/R02 und ihre Contour-Module erscheinen nicht auf der Website.
- KI-Generierung ist optional. Modelle und Standardbau dürfen davon nicht abhängen.
- Blätter, Ansichten, Vorschauen, Geo und Release-Zips sind gitignoriert. Specs/Prompts bleiben im Repo; Belege extern.
- Vor Commit `./check` und gezielte Tests. Branch je Sitzung: Patch (bis etwa 100 Zeilen ohne Format, Vertrag, Kernsystem) `./ce session patch <kurzname>`, Version `./ce session reserve <Name>`.
- Commits sind beauftragt. Kein Push, PR, Merge oder veröffentlichter Release ohne ausdrückliches Okay.
