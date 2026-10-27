# Herkunft R02 „Frost“

Stand 27.10.2026. Jede Modellzahl ist **Vorgabe**, **gemessen** oder **Annahme**. Die Zahl steht im Modul (`PROVENANCE`
oder Teil-`provenance`); hier stehen die Wege, Konflikte und Abweichungen.

## Quellen

| Quelle | SHA256 | Rolle |
|---|---|---|
| `refs-r02/r02-blauweiss.svg` | `d997c46b427cb13839cfe23a0241dce5745b143e23ead03796693802286a4814` | Vorlage (Original aus Downloads `Pasted-20261027-110039.svg`) |
| `refs-r02/r02-sheet-9803.png` | `97ccf96fe77e2daa9dd51a640624d0b1a3df43588294a65bdcd2b9e8b5077350` | Raster `rsvg-convert` 2.63.2 `-w 9803`, identisch mit der Referenzprobe |
| `refs-r02/markers.json` | `51ef70c0…cfcfc` | Codex-Arbeitsmarker, nur Hinweise (gestrichelt = Schätzung) |
| `refs-r02/mask-provenance.json` | in `tools/robot_reference_masks.py R02` erzeugt | Masken-SHAs (revision 1), Registrierung |
| `refs-r02/candidates/navygold.svg` | `fce6981d…0564d` | nur späterer Vergleich, nicht Teil von R02 (Nutzerangabe 27.10.2026) |

## Maßstab (Vorgabe) und Messweg (gemessen)

- Höhe **2000 mm**: Nutzervorgabe 27.10.2026. Daraus folgt k = 2000/3665 = 0,54570 mm/px (Frontscheitel y174 bis Bodenkante y3839).
- Konturzeilen: `tools/r02_measure.py` liest je Blattzeile die belegten Läufe der revision-1-Masken in mm aus (5-mm-Raster).
  Die Module übernehmen sie auf 1 mm gerundet, meist alle 10–20 mm, an Knicken dichter.
- Front gegenüber gespiegeltem Rücken: IoU 0,9746. Profil A gegenüber gespiegeltem Profil B: IoU 0,9769 (Referenzprobe).
  Front und Profile stimmen an Beinen und Rumpf auf etwa 1–2 mm überein.

## Gelenkhöhen (mm über Boden, Höhe 2000)

Die Codex-Marker sind auf 2000 mm umgerechnet (×2000/1924). Die eigene Messung stützt sich auf sichtbare Scheiben und
Konturknicke. Die Front ist verbindlich; jede Abweichung über 10 mm ist ausgewiesen.

| Gelenk | Codex Front | Codex Rücken | Codex Profil | verwendet | Herkunft / Abweichung |
|---|---:|---:|---:|---:|---|
| Hals | 1737 | 1775 | 1757 | 1760 | gemessen: Schaloberkante Front (Breitensprung ±118→±86). Rücken −15, Front +23 gegenüber Codex |
| Schulter | 1541 | 1515 | 1592 | 1560 | Annahme: Achse unter dem Polster verdeckt, Polstermitte u≈1600. Codex-Spanne 77 mm |
| Ellbogen | 1321 | 1303 | 1329 | 1329 | gemessen: sichtbare Profilscheibe (f−77). Rücken-Schätzung −26 |
| Handgelenk | 1036 | 1036 | 944 | 1036 | gemessen: schmalste Frontzeile Unterarm/Hand u1036..1040. **Profilmarker sitzt auf der Handmitte** (Sichtprüfung): Markerfehler, keine andere Armhaltung |
| Hüfte | 1099 | 1060 | 1093 | 1060 | Annahme: Gelenk verdeckt zwischen Schritt u975 und Oberschenkel-Außenoberkante u≈1090. Front-Schätzung −39 |
| Knie | 659 | 671 | 675 | 675 | gemessen: Kniescheibenring im Profil (A und B je u674,9). Frontblock u600..760, Mitte ≈680. Front-Schätzung +16 |
| Knöchel | 172 | 174 | 172 / 229 | 169 | gemessen: untere Profilscheibe A2 (Ring u168,5, f−21..−24). A1 ist eine zweite sichtbare Scheibe, nur gestalterisch |

## Konflikte der Vorlage

1. **Füße Front ↔ Rücken** (u0..40): Die Front zeigt Zehen bis x359 und eine abgeschrägte Innenkante (u10: x228..359), der Rücken
   schmalere Fersen (u10: x138..266). Orthografisch müssen beide Silhouetten Spiegelbilder sein. Das Modell folgt der Front,
   daher liegt Rücken-Band 0 bei 1,065 (Grenze 1,08) und die Rücken-IoU unter der Front-IoU.
2. **Kopf Profil A ↔ B:** Die Profile sind von u1790 bis u1990 um 12 mm in f gegeneinander versetzt (gleiche Tiefe 262 mm).
   Das Modell nutzt den Mittelwert, die Restabweichung beträgt ±6 mm.
3. **Profilmarker Handgelenk:** Der Codex-Marker W (u944) sitzt auf dem Handrücken. Die Hand hängt in Front und Profil gleich
   (Handfläche zum Oberschenkel, Fingerspitzen u≈860–872).
4. **Sohlenbogen:** Profil u10–20 zeigt getrennte Fersen- und Ballenläufe. Gebaut als zwei Sohlenteile mit einer 46-mm-Lücke.

## Annahmen (verdeckt)

- Rumpfrücken (Bauch −112, Brust −122, Becken −108..−112, Gürtel −116..−118): Er ist im Profil vollständig von Unterarm,
  Oberarm und Schulterpolster verdeckt.
- Arm-Vorderkanten (Polster ≈+87, Oberarm ≈+35, Unterarm +22..+49): Sie liegen in der Rumpfsilhouette und sind am Profil-Farbbild abgelesen.
- Oberschenkel-Innenkante über u980 und Beckenkern-Innenkante: verdeckt, an die Schrittkante angeschlossen.
- Brustbreite u1500..1660 ±200 hinter den Schulterpolstern (Nachbarzeilen u1500 und u1680).
- Einsetztiefe 3 mm der gestapelten Segmente, Plattenauflage 1,2–2,6 mm, Plattenstärke 2–4 mm, Querschnitt achteckig (Fase 22 %, Kopf 30 %, Brust vorn 8 %).
- Explosionsversätze nur zur Darstellung.

## Gestaltung (gemessen am Farbbild, gerundet)

Gestaltet sind Brustkern (Ring r49, Licht r33, u1543), Kristallfelder an Schulterpolstern (Profil-Oval, Front), Oberarm,
Unterarm, Schienbein und Oberschenkel-Außenseite sowie oben am Helm, dazu schiefergraue V-Gurte, Taschen und Schal,
die Rückenwirbelreihe (drei Sechsecke), Schulterblattplatten, Gesäßplatte, dunkle Kniegelenke mit weißer Kniescheibe,
Waden in Schiefer und dunkle Mittelfüße. Die Rollenfarben stammen aus den häufigsten Blattfarben
(#E4ECEC, #242C34, #444C64/#545C74, #343C44, #A4DCFC, #4C7C9C).
