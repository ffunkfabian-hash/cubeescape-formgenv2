"""Eigenständige Kit-Entwürfe außerhalb der BASIC-Variantenmatrix."""
from . import va01_longspan, volt01, volt02, volt03, volt04, volt05, volt06, volt07, volt08, volt09, volt10

AUTHORED = {va01_longspan.SHEET: va01_longspan, **volt01.SHEETS, **volt02.SHEETS, **volt03.SHEETS, **volt04.SHEETS, **volt05.SHEETS, **volt06.SHEETS, **volt07.SHEETS, **volt08.SHEETS, **volt09.SHEETS, **volt10.SHEETS}
SERIES = {series.SERIES: tuple(series.SHEETS) for series in (volt01, volt02, volt03, volt04, volt05, volt06, volt07, volt08, volt09, volt10)}
