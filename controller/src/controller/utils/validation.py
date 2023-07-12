# -*- coding: utf-8 -*-
from controller.constants import ALL_VALID_BARCODE_HEADERS
from controller.constants import BARCODE_HEADERS
from controller.constants import BARCODE_LEN


def check_barcode_for_errors(barcode: str, barcode_type: str | None = None) -> str:
    """Return error message if barcode contains an error.

    barcode_type kwarg should always be given unless checking a scanned
    barcode value.
    """
    if len(barcode) != BARCODE_LEN:
        return "barcode is incorrect length"
    if (header := barcode[:2]) not in BARCODE_HEADERS.get(barcode_type, ALL_VALID_BARCODE_HEADERS):
        return f"barcode contains invalid header: '{header}'"
    return (_check_new_barcode if "-" in barcode else _check_old_barcode)(barcode)


def _check_new_barcode(barcode: str) -> str:
    for char in barcode[2:10] + barcode[-1]:
        if not char.isnumeric():
            return f"barcode contains invalid character: '{char}'"
    if int(year := barcode[2:4]) < 22:
        return f"barcode contains invalid year: '{year}'"
    if not 0 < int(julian_date := barcode[4:7]) < 366:
        return f"barcode contains invalid Julian date: '{julian_date}'"
    if not 0 <= int(experiment_id := barcode[7:10]) < 300:
        return f"barcode contains invalid experiment id: '{experiment_id}'"
    # Tanner (4/26/23): all barcodes at the moment have 2 as the final digit
    if (last_digit := int(barcode[-1])) != 2:
        return f"barcode contains invalid last digit: '{last_digit}'"
    return ""


def _check_old_barcode(barcode: str) -> str:
    for char in barcode[2:]:
        if not char.isnumeric():
            return f"barcode contains invalid character: '{char}'"
    if int(year := barcode[2:6]) < 2021:
        return f"barcode contains invalid year: '{year}'"
    if not 0 < int(julian_date := barcode[6:9]) < 366:
        return f"barcode contains invalid Julian date: '{julian_date}'"
    return ""
