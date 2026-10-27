# R02 „Frost“ – Baugruppenvertrag

Stand 27.10.2026. Vorlage: weiß/blaues Sechs-Ansichten-Blatt `~/Library/Caches/CubeEscapeFormgen/refs-r02/r02-blauweiss.svg`
(SHA256 `d997c46b…a4814`). Es gibt Silhouette **und** Schalengestaltung vor (Nutzerentscheidung 27.10.2026).
Ober- und Untersicht dienen nur als Gestaltungsreferenz, nicht zur Abnahme. R01 und sein [Vertrag](robot-contract.md) bleiben unverändert.

## Maßstab und Registrierung

- **Höhe 2000 mm (Vorgabe Nutzer).** Für alle Ansichten gilt ein gemeinsamer Frontmaßstab k = 2000/3665 mm/px
  (Raster `rsvg-convert -w 9803`, Frontscheitel y174, Frontboden-Kante y3839). Keine Ansicht wird einzeln skaliert.
  Alle vier Ansichten teilen dieselben Blattzeilen: u = (3839 − y)·k.
- Front/Rücken: x=0 an der gemessenen Symmetrieachse (maximale Spiegel-IoU 0,9947/0,9939). Anatomisch links = x+.
- Profile: f=0 an der Kniescheibenmitte (Schwerpunkt des schiefergrauen Rings, Profil A x5757,5 px, B x7068,0 px).
- **Profil A (→)** zeigt die rechte Seite → Rasterkamera `side_right`; **Profil B (←)** die linke → `side_left`.
  Das ist eine Namenszuordnung, keine Spiegelung der Geometrie.
- **Mask revision 1 (R02):** Vektor-Alpha > 127, Komponenten ≥ 0,2 % der größten (abgelöste Hände gehören dazu),
  closing 2, fill. Masken und Registrierung stehen mit SHA in `refs-r02/mask-provenance.json` und sind eingefroren
  (Werkzeug `tools/robot_reference_masks.py R02`; Test `tests/test_robot_reference_regression.py`).

## Schnittstelle

- Module `formgen/models/figures/r02_parts/{legs,lower_body,upper_body,head,arms}.py` exportieren `PARTS`, `ANCHORS`, `PROVENANCE`;
  gemeinsame Bausteine stehen in `common.py`. Montage in `r02_basic_robot.py`, das nur der Hauptagent ändert.
- Autorenraum mm (f,u,x), Boden u=0, vorn f+, anatomisch links x+. Teil-IDs beginnen mit der Baugruppe, Seiten enden auf `_l`/`_r`.
- Konturzeilen `(u, x_innen, x_außen, f_hinten, f_vorn)` sind gemessen (`tools/r02_measure.py`). Front und Profil werden je Seite
  gespiegelt gemittelt, Profil A/B gemittelt. **Die Front ist verbindlich** für Höhen und Breiten, die Profile für Tiefe und Fußlänge,
  der Rücken für das Rückenmodul. Verdeckte Kanten sind als Annahme markiert.
- Montageanker: Socket_Ground, Waist, Neck, Shoulder_L/R, Elbow_L/R, Hand_L/R, Hip_L/R, Knee_L/R, Ankle_L/R.

## Form

- Jedes Teil ist ein geschlossenes, positiv orientiertes Netz mit expliziten Dreiecken. Die rechte Seite entsteht aus der linken
  über `common.mirror` mit denselben Diagonalen.
- Segmente sind **massive Lofts** über achteckige Ringe mit exakter x- und f-Ausdehnung je Zeile. Gestapelte Segmente beginnen
  3 mm unter der Stoßzeile (eingesetzt, keine koplanaren Deckel). Hohle Schalen sind bei R02 nicht vorgeschrieben,
  weil kein Innenraum sichtbar ist (Abweichung zu R01).
- Gestaltung: Platten (`face_panel`) liegen 1,2–2,6 mm über einer Loftfläche und sind je Ringintervall eben. Sie ändern die
  gemessene Kontur höchstens um ihre Auflage. Gelenkscheiben stehen höchstens 1,5–4 mm über der Kontur.
- Materialrollen nur aus `skins.toml`: `frost_shell` (weiß), `frost_frame` (Unterbau dunkelgrau), `frost_slate` (Gurte/Taschen/Schal),
  `frost_joint` (Gelenkscheiben), leuchtend nur `frost_visor`, `frost_core` (Brustkern) und `frost_crystal`
  (Kristallfelder): Visier plus zwei Funktionen (Nutzerentscheidung 27.10.2026).
- Schnittregeln (Test `tests/test_r02_model.py`): Strukturteile überschneiden sich höchstens mit 12 % des kleineren Teils
  (eingesetzte Stöße). Platten und Scheiben sitzen höchstens bis zu ihrer Tiefe im Wirt. Koplanare Überdeckung ist verboten
  (`geo._coplanar`: ≤ 1°, < 0,5 mm, ≥ 1 mm²).

## Abnahme

- Front, Rücken, Profil A und Profil B jeweils IoU ≥ 0,90; zehn Höhenbänder je Ansicht (40 insgesamt) mit Breitenverhältnis
  0,92–1,08. Gemessen wird die mittlere äußere Zeilenspannweite über den gemeinsamen Front-u-Bereich 0..2000 mm.
- Abnahmemaske und Farbbeleg stammen aus demselben Rasterframe (`tools/robot_evidence.py --robot R02`, 1024² px, Skala
  3665/2/4 px/m). Grenzwerte, Masken und Registrierung werden nie zur Verbesserung eines Modells verändert.
- Bekannte Grenzen der Vorlage: Front und Rücken widersprechen sich an den Füßen (Front u10: x228..359, Rücken x138..266).
  Ein Körper kann nicht beide Silhouetten erzeugen; die Front gilt. Am Kopf sind die Profile um 12 mm in f gegeneinander versetzt,
  daher wird gemittelt. Details in der [Herkunft](herkunft-r02.md).
