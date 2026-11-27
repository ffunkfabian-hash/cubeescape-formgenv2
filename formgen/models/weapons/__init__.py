"""Eigenständige Kit-Entwürfe außerhalb der BASIC-Variantenmatrix."""
from . import va01_longspan, volt01, volt02

AUTHORED = {va01_longspan.SHEET: va01_longspan, **volt01.SHEETS, **volt02.SHEETS}
SERIES = {volt01.SERIES: tuple(volt01.SHEETS), volt02.SERIES: tuple(volt02.SHEETS)}
