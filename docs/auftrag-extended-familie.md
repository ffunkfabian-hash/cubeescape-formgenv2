# Auftrag EXTENDED-Familie: neue Sci-Fi-Waffen für BASIC-02 bis BASIC-17

Stand 23.11.2026. Koordination: Sitzung „EXTENDED-01“ (Sightline-Rolle für diese Familie). Nutzerentscheide vom 23.11.2026:
**zwei Wellen zu je vier Sitzungen, je Sitzung zwei Waffentypen**; das Automatikgewehr EXTENDED-01 (0.15 „Spearhead“) wird in seiner
eigenen Sitzung fertiggestellt und ist **nicht Teil dieses Auftrags** – nicht ändern.

## Auftrag des Nutzers (Anforderungen)

Für jeden übrigen BASIC-Waffentyp (02–17) genau ein vollständig neues, eigenständiges Sci-Fi-Waffendesign als 3D-Modell. Kreative
Individualität von Formgen v1 + hochwertige 3D-Modellierung und Designqualität von Formgen v2.
- Eigene Silhouette, individuelle Proportionen, eigenständige Formarchitektur je Typ; Funktionsprinzip und Erkennbarkeit des Typs bleiben.
- Alle eindeutig dieselbe Produktfamilie wie BASIC; abwechslungsreich und charakteristisch, **nicht beliebig, nicht übertrieben futuristisch**.
- Jede Waffe geometrisch neu – nicht BASIC umbauen, keine angesetzten Zusatzteile.
- Hochwertige Hauptformen, differenzierte Gehäusestrukturen, harmonische Übergänge, sorgfältige Hard-Surface-Details.
- **Nicht** immer dieselben Gehäuseformen, Proportionen oder Motive über die Typen hinweg.
- Arbeitsweise je Typ: BASIC-Typ einzeln analysieren → mehrere unterschiedliche Formideen → überzeugendste wählen → mit den Formgen-v2-Werkzeugen
  vollständig bauen → echte Renderings aus mehreren Perspektiven → Schwächen selbst verbessern.
- Unabhängig von früheren EXTENDED-Experimenten; Referenzen nur: die jeweilige BASIC-Waffe, Formgen v1, Formgen v2.
- Leitgedanke: eine gemeinsame Designfamilie, unterschiedliche Waffencharaktere, individuelle Formen, höchste gestalterische Qualität.

**Tabu (nicht öffnen):** `~/Library/Caches/CubeEscapeFormgen2/extended-*` außer den eigenen neuen Belegordnern dieser Familie,
`extended-restart.*`, `extended-formlabor-06`, `bulkhead-abnahme.*`, Branch `claude/formgen-hybrid-rifle-9eb969`.

## Aufteilung

Ähnliche Typen liegen bewusst in **einer** Sitzung, damit sie sich dort gezielt voneinander absetzen; zwischen den Sitzungen trennen die Typen
sich von selbst. Welle 2 startet erst, wenn Welle 1 ihre Formen gewählt hat, und bekommt deren Motivtabelle.

| Welle | Sitzung | Typen (BASIC → Modul) |
|---|---|---|
| 1 | Gewehre | 02 Impulsgewehr → `e02_*`, 03 Spähergewehr → `e03_*` |
| 1 | Faustwaffen | 04 Handkanone → `e04_*`, 05 Seitenwaffe → `e05_*` |
| 1 | Fusion | 10 Fusionsgewehr → `e10_*`, 11 Lineares Fusionsgewehr → `e11_*` |
| 1 | Nahkampf | 16 Schwert → `e16_*`, 17 Glefe → `e17_*` |
| 2 | Dauerfeuer | 06 Maschinenpistole → `e06_*`, 15 Maschinengewehr → `e15_*` |
| 2 | Streuung | 08 Schrotflinte → `e08_*`, 13 Granatwerfer → `e13_*` |
| 2 | Schulter | 09 Scharfschützengewehr → `e09_*`, 14 Raketenwerfer → `e14_*` |
| 2 | Sonder | 07 Kampfbogen → `e07_*`, 12 Spurgewehr → `e12_*` |

## Familien-DNA (gilt für alle; aus BALLON-Stilhandbuch §2–4 und BASIC-01 v2.1)

Gemeinsam (das macht die Familie): Materialrollen und Zweiton (Creme `shell` über `graphite`, Teilung eher 70:30), `anodized`-Paneele mit
`trim`-Schrauben nur an Panzern/Paneelen, Fugen 1 mm (`SEAM`), Schichtung 2–3 mm, Radienstufen `R_BODY/R_MID/R_SMALL/R_FINE`, `R_SOFT` nur am
Griff, genau **ein** Blickfang (Leuchtfunktion), ≤ 3 Leuchtfunktionen, ein Grafikband, ein Schriftzug, ≤ 3 Orange-Bedienfunktionen,
mindestens eine Negativraum-Zone, mehrstufige lesbare Front, Akzente kameranah (Visier, Verschluss, linke Seite), Dreiecke Ziel 20 k / Grenze 50 k.
Genormte Schnittstellen dürfen Familienbausteine nutzen (Griff `grip_v21`, Visiere aus BALLONs Baukasten, Magazinschnittstelle) – das ist
Familie, kein Umbau. **Nicht gemeinsam** (je Typ neu): Silhouette, Gehäusearchitektur, Proportionen, Querschnitte, Leitmotiv.

**Schon vergeben – nicht wiederholen:** EXTENDED-01 „Speerspitze“: fallende Oberlinie + steigende Unterlinie zur Spitze, Draufsicht-Verjüngung,
Fuller-Schlitz als Negativraum, Sechseck-Kern, Fachwerkschaft mit Puffer, Sechskant-Kompensator. Serien J–M aus 0.8 (Facetten-Keil, Werkbank,
Rasterblöcke, Perlschale) sind Linien, keine EXTENDED-Formen – ebenfalls nicht als Leitmotiv nehmen.

## Technik (Grundlage: 0.15 „Spearhead“)

Lies `docs/uebergabe-0.15-spearhead.md` (Vokabular, Renderweg, Sperren) und die 0.15-Dateien `formgen/extended.py`,
`formgen/models/extended/e01_spearhead.py`, `tools/extended_render.py`, `tests/test_extended.py` als Muster.
- Modell je Typ `formgen/models/extended/eNN_<englischer_name>.py`, META `id = 'EXTENDED-NN'`, `type` wie BASIC-NN, Docstring mit
  Formsprache-Checkliste (Stilhandbuch §3), jede Zahl mit Herkunft (Vorgabe/gemessen/Annahme). BASIC-Referenz: neuester Pilot im Snapshot
  `~/Library/Caches/CubeEscapeFormgen2/ballon/fe4a5dc4…-85ed1991/basic/pilot/wNN_*_v21.py` (16/17: `basic/weapons/wNN_*.py`); BALLONs
  Leitmerkmal je Typ im Stilhandbuch §1 (`~/Claude/cubeescape-ballon/docs/stilhandbuch.md`). Formgen v1: Typnummern weichen ab – Modul über
  `rg -n "name='<Typname>'" ~/Claude/cubeescape-formgen/claude/generator/` finden.
- `formgen/extended.py` und `tools/extended_render.py` nur **additiv** ändern (das Gewehr darf sich nicht ändern; 0.15-Tests müssen grün bleiben).
- Tests je Sitzung in eigener Datei `tests/test_extended_<sitzung>.py` (vermeidet Konflikte): Felder/`variant.problems`, Budgets,
  Visierlinie (wo der Typ ein Visier hat), Zusammenhang, **Seiten-IoU < 0,85 gegen den eigenen BASIC-Typ und gegen jedes vorhandene
  EXTENDED-Modell gleicher Größenklasse**, Gegenproben.
- Renders nur unter `~/Claude/cubeescape-nexogen/ce lock gpu|blender -- …` mit absoluten Pfaden. Belege außerhalb des Repos:
  `~/Library/Caches/CubeEscapeFormgen2/<Version>/belege/eNN/`.

## Ablauf und Abnahme je Typ

1. BASIC-Typ analysieren (Funktion, Leitmerkmal, Anker, Mechanik) → mindestens **drei** unterschiedliche Formideen als Seitenskizze,
   IoU gegen BASIC-NN und gegen die anderen EXTENDED-Modelle; Wahl begründen (Tabelle im Bericht).
2. Bauen; AAA-Renders aus mindestens fünf Perspektiven (Hero, Perspektive, beide Seiten, oben, vorn) + Clay; Kontaktbogen neben BASIC-NN.
3. Mindestens zwei Nachbesserungsrunden mit Liste „gesehen → geändert“.
4. Zum Abschluss eine Zeile für die **Motivtabelle** (Typ · Leitmotiv · Silhouette · Querschnitt · Blickfang · Negativraum · Front),
   damit Welle 2 bzw. die Familie Dopplungen erkennt.

Je Sitzung eine **Version** (`./ce session reserve <Name> --about … --model …`, Opus `high`), `./check`, Richter `./ce judge`
(`~/.claude/templates/pruefung.md`), PR auf den eigenen Branch, Bericht als PR-Beschreibung mit Belegpfaden. Kein Merge ohne Ja des Nutzers.
Keine Blatt-ID, keine Website-Aufnahme (Entscheidung des Nutzers steht aus). **Kontextlänge ist irrelevant** (Nutzer 23.11.2026):
bei der Hook-Meldung > 150 000 Tokens nicht übergeben, in derselben Sitzung bis zum PR weiterarbeiten.
