"""Register der eigenständigen Kit-Entwürfe (VA01, Serien Volt-01 bis Volt-11): Blatt-ID → Modul, Serie → Blätter.

Eigenes Modul statt Paket-`__init__` (0.60): `formgen.models.weapons` wird auch vom Generator (Linie T) importiert; ein Register im
`__init__` zöge VA01 → `extended_lines` → Raster und Website in die Code-Closure der Geometrie-Stufe."""
from . import va01_longspan, volt01, volt02, volt03, volt04, volt05, volt06, volt07, volt08, volt09, volt10, volt11

AUTHORED = {va01_longspan.SHEET: va01_longspan, **volt01.SHEETS, **volt02.SHEETS, **volt03.SHEETS, **volt04.SHEETS, **volt05.SHEETS, **volt06.SHEETS, **volt07.SHEETS, **volt08.SHEETS, **volt09.SHEETS, **volt10.SHEETS, **volt11.SHEETS}
SERIES = {series.SERIES: tuple(series.SHEETS) for series in (volt01, volt02, volt03, volt04, volt05, volt06, volt07, volt08, volt09, volt10, volt11)}
