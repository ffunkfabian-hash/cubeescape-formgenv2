"""Eigenständige Kit-Entwürfe außerhalb der BASIC-Variantenmatrix."""
from . import va01_longspan, volt01, volt02, volt03, volt04

AUTHORED = {va01_longspan.SHEET: va01_longspan, **volt01.SHEETS, **volt02.SHEETS, **volt03.SHEETS, **volt04.SHEETS}
SERIES = {series.SERIES: tuple(series.SHEETS) for series in (volt01, volt02, volt03, volt04)}
