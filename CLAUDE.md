# Formgen v2 – Regeln für alle Agenten

Es gelten die globalen Regeln in `~/.codex/AGENTS.md` (Quelle: cubeescape-nexogen).
Der aktuelle Nutzerauftrag steht in `docs/auftrag-codex-formgen-v2.md`; direkte Nutzeranweisungen haben Vorrang.

- Sprache Deutsch. Modellwahl nach aktuellster direkter Nutzerregel: gpt-6-luna für Routine, gpt-6.1-sol für große/heikle Diffs; keine neuen Astra-Starts.
- Eine Pipeline unter `formgen/`: eigene Python-Modelle in ballons kit-Vokabular, keine v1-Modellsprache.
- Formgen v1 und ballon sind ausschließlich Lesereferenzen. Vorschläge an ballon nur unter `docs/` hier.
- Bestehende v1-Waffen und Visiere ausschließlich als Geo-Export importieren. Keine alten Modellmodule kopieren.
- Erst `docs/modellsprache.md` und Mini-Modell, dann Cache-Abnahme mit echtem Dummy-Artefakt; vor deren Erfolg kein Rendering.
- Hauptagent verantwortet Schnittstellen, VERSION-Konstanten, Integration und Commits. Jeder Unteragent schreibt nur zugewiesene Dateien.
- Unabhängiger Prüfagent ohne Implementierung nimmt Ergebnisse vor Nutzermeldungen ab.
- Komponenten und Artefakte getrennt cachen; ohne `--force` nur Fehlendes/Veraltetes bauen. Nie ungefragt alles neu rendern.
- Jede Modellzahl hat eine Herkunft (Vorgabe, gemessen, Annahme). Farben nur in `skins.toml`.
- Bilder auf dem Mac und unter `~/Claude/cubeescape-nexogen/ce lock gpu -- …`; Hintergrund mittelgrau, kein Bloom.
- Vor Roboterbau beide Zielbilder beim Nutzer anfordern. Aktuell vier neue Orthos; Front/Rücken/beide Seiten IoU ≥ 0,90; Bandbreite 0,92–1,08.
- KI-Generierung ist optional. Modelle und Standardbau dürfen davon nicht abhängen.
- Blätter, Ansichten, Vorschauen, Geo und Release-Zips sind gitignoriert. Specs/Prompts bleiben im Repo; Belege extern.
- Vor Commit `./check` und gezielte Tests; nie auf main committen. Branch `codex/formgen-v2-first`.
- Commits sind beauftragt. Kein Push, PR, Merge oder veröffentlichter Release ohne ausdrückliches Okay.
- Bericht `docs/versions/`, Entscheidungen `docs/ENTSCHEIDUNGEN.md`, Lehren `docs/LESSONS.md` (≤ 60 Zeilen).
