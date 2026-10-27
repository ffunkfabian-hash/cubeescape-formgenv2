# Übergabe R02 „Frost“ – Formgenauigkeit (für frische Sitzung)

Stand 27.10.2026, geschrieben von der Sitzung `pensive-nobel-7aa725` (Claude Opus). Für eine **frische Sitzung ohne Verlauf/Fork**.
Erste Zeile des Prompts: `Opus, Denkaufwand high – Grund: Kernmodell R02 auf Formgenauigkeit des Blatts umbauen`.
Auftrag weiterhin [auftrag-r02.md](auftrag-r02.md); Entscheidungen in [ENTSCHEIDUNGEN](ENTSCHEIDUNGEN.md) (27.10.2026); Bericht [0.2](versions/0.2.md).

## Stand

- Lokaler Branch `claude/formgenv2-0.2-frost`, Worktree `.claude/worktrees/pensive-nobel-7aa725`. Commits `a1eacd8`, `792a003`, danach der WIP-Commit
  mit dieser Datei. **Kein Push, PR, Merge oder Release.** Codex-Kontingent leer: Prüfung durch Opus-Richter (`ce-judge`).
- Silhouetten-Gates sind grün (IoU 0,958–0,975, 40/40 Bänder, Grenzwerte unverändert). **Der Nutzer lehnt die Form ab:** Achteckige Lofts
  mit aufgeklebten Platten sind zu grob. Ziel ist jetzt die Formgenauigkeit des Blatts in Front, Rücken und Profil.
- Pilot (nur Arme, WIP): `tools/r02_regions.py arms` zerlegt das Blatt nach Farbklassen in Plattenpolygone (generiert
  `formgen/models/figures/r02_parts/arms_regions.py`). `common.projected()` teilt jede Segmenthülle in einen dunklen Kern (4 mm eingerückt) und
  eine Außenschicht und schneidet die in Blickrichtung extrudierten Regionen mit der Schicht im passenden Sektor. Ergebnis: Plattenaufteilung wie
  im Blatt, Fugen dunkel. Raster-Stil `ink` (Opt-in über `INFO.line_style`, `RASTER` 6). Der Nutzer hat den Pilot gesehen und
  einen Weiterbau mit Meshy-Querschnitten gewählt.
- Zwei R02-Tests sind im WIP rot (siehe unten). R02-Goldens stehen auf `792a003` und müssen nach Sichtprüfung neu eingetragen werden.

## Referenzen (extern, `~/Library/Caches/CubeEscapeFormgen/refs-r02/`)

| Datei | SHA256 | Rolle |
|---|---|---|
| `r02-blauweiss.svg` / `r02-sheet-9803.png` | `d997c46b…a4814` / `97ccf96f…77350` | **verbindlich**: Umriss, Höhen, Plattenumrisse, Farben |
| `mask-provenance.json`, `ortho-*-mask.png` | in der Datei | mask revision 1, Registrierung (eingefroren) |
| `meshy/r02-meshy-split9.glb` | `29c8dd04a633ebba1cd82278f84f6ab4b2bbbda9f0f363f30df0e7146516e896` | **Formquelle**: 11 Netzteile an Blattposition |
| `meshy/r02-meshy.glb` | `4714ed9907bf4cf75092c60c57936979abbbf3d41d17dd98dde47132bbaf861f` | texturiertes Gesamtnetz, Kontrolle |
| `meshy/r02-meshy-edit.glb` | `0cae35fa1dc06975d1bd1e9f6ae14194872002c82e56a6f57967181535b85dba` | verschobene, umproportionierte Teile – **nicht verwenden** |

Meshy-Netze sind KI-Referenzen vom Nutzer (27.10.2026). Regel: KI ist optional, **Modell und Standardbau dürfen nicht davon abhängen**. Daraus
gemessene Zahlen werden in Module geschrieben (Herkunft „gemessen an KI-Referenz, eingepasst auf das Blatt“), nie zur Laufzeit gelesen.

GLB lesen ohne Fremdbibliothek: Header 12 B, JSON-Chunk, BIN-Chunk; Accessor `POSITION` (float32), `indices` (uint32). Y oben, +Z vorn, +X anatomisch
links. Skalierung: Gesamthöhe → 2000 mm, u = (y − y_min)·s, x = x·s, f = (z − z_mitte)·s. Registrierung auf das Blatt: Front/Rücken ohne Versatz
(IoU 0,948/0,945), Profil f-Versatz **+32 mm** (Profil A, IoU 0,939) bzw. **+36 mm** (Profil B, 0,930) → +34 mm verwenden und dokumentieren.

Teile `split9` (u, x in mm nach Skalierung): 0 Bein rechts (u0–1116), 3 Bein links, 1 Becken mit Gürtel/Taschen (945–1389), 2 Kopf (1672–2000),
10 Rumpf mit Schal (1220–1838), 8/9 Arm links/rechts (853–1640), 4+7 / 5+6 Schulterpolster links/rechts (je zwei Schalen, 1479–1738).

## Vorgehen (empfohlen, mit dem Nutzer abgestimmt)

1. **Segmente schneiden:** Aus `split9` die 19 Gelenksegmente mit ebenen Schnitten an den gemessenen Blatthöhen bilden (Knie u675, Knöchel u169,
   Ellbogen u1329, Handgelenk u1036, Hals u1760, Taille u1265, Brust/Bauch ≈1360; Hüfte 1060 Annahme). Liste und Begründung im Chat 27.10.: Helm, Hals,
   Brustkorb, Bauch, Becken mit Gürtel, je Seite Polster, Oberarm, Ellbogen, Unterarm, Hand (ein Block, keine Fingerglieder ohne Greifpose),
   Oberschenkel, Knie, Unterschenkel, Fuß.
2. **Querschnitte messen:** Je Segment und Zeile (5–10 mm) den Meshy-Schnitt als Ring (z. B. 24–32 Punkte über Winkel um den Zeilenmittelpunkt)
   bestimmen und **affin auf die Blattmaße der Zeile** (x_innen, x_außen, f_hinten, f_vorn aus `tools/r02_measure.py`) einpassen. So bleibt der
   Umriss exakt (Gates) und die Form kommt aus dem Netz. Ergebnis als generiertes Modul je Baugruppe (wie `arms_regions.py`) mit Quell-SHA.
3. **Platten:** `tools/r02_regions.py` auf alle Baugruppen erweitern (ZONES) und `common.projected()` auf die neuen Ring-Lofts anwenden.
   Regionen nur auf Flächen projizieren, die in der Zeichnung zum selben Teil gehören (Sektor plus Teilmaske), sonst landen fremde Flächen
   auf der Hülle (Pilot: Oberschenkel-Kristall zwischen den Fingern).
4. Erst danach: Fasen und Hände mit sichtbaren Fingern (Netzform), Gestaltungsabweichungen 6c des Richters.

## Offene Punkte

- **Rot:** `tests/test_r02_model.py` – (a) Splitterdreieck ≈1e-5 mm² aus manifold3d-Schnitt (`simplify(.01)` hilft nicht; Ursache beheben, z. B.
  Regionen leicht nach außen versetzen statt Grenzen auf Ringkanten fallen zu lassen); (b) `test_no_coplanar_overlap_between_parts` ist mit
  132 000 Dreiecken zu langsam (> 35 CPU-min) – auf Teilpaare mit überlappender Hüllbox einschränken, Grenzwerte nicht lockern.
- Richterbefunde zu `792a003` (Bericht 0.2, Abschnitt Prüfung): 4a–4d Testschärfe, 5a `provenance.kind` je Teil, 5c Herkunft Emission, 6b Kniescheibe.
- `RASTER` 6 invalidiert alle Bildcaches; andere Modelle bleiben pixelgleich (Stil ist Opt-in), Stichprobe vor dem Golden-Update wiederholen.
- Nach Umbau: Cache-Zweitlauf 0 gebaut, zwei Seeds pixelgleich, R02-Goldens nach Sichtprüfung, Kontaktbogen, Opus-Richter, Bericht 0.2.

## Werkzeuge im Repo

`tools/robot_reference_masks.py R02` (Masken, eingefroren) · `tools/r02_measure.py` (Konturzeilen) · `tools/r02_regions.py <gruppe>` (Plattenpolygone) ·
`tools/robot_evidence.py --robot R02 [--force] legs lower_body upper_body head arms` (Gates, Belege; unter `~/Claude/cubeescape-nexogen/ce lock gpu -- …`).
Vergleichsbild Blatt/Modell: Skript in der Sitzungsnotiz (`side-session-notes/…/r02-frost-status.md`), leicht nachzubauen aus Registrierung und Frames.
