from __future__ import annotations

import re

INN_10_RE = re.compile(r"(?<!\d)(\d{10})(?!\d)")
INN_12_RE = re.compile(r"(?<!\d)(\d{12})(?!\d)")


def extract_inn(text: str | None) -> str | None:
    if not text:
        return None
    match_12 = INN_12_RE.search(text)
    if match_12:
        return match_12.group(1)
    match_10 = INN_10_RE.search(text)
    if match_10:
        return match_10.group(1)
    return None


def validate_inn(inn: str) -> bool:
    if not inn.isdigit():
        return False
    if len(inn) == 10:
        return _validate_10(inn)
    if len(inn) == 12:
        return _validate_12(inn)
    return False


def _validate_10(inn: str) -> bool:
    coefficients = (2, 4, 10, 3, 5, 9, 4, 6, 8)
    checksum = sum(int(d) * c for d, c in zip(inn[:9], coefficients, strict=True)) % 11 % 10
    return checksum == int(inn[9])


def _validate_12(inn: str) -> bool:
    coefficients_1 = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
    coefficients_2 = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
    checksum_1 = sum(int(d) * c for d, c in zip(inn[:10], coefficients_1, strict=True)) % 11 % 10
    checksum_2 = sum(int(d) * c for d, c in zip(inn[:11], coefficients_2, strict=True)) % 11 % 10
    return checksum_1 == int(inn[10]) and checksum_2 == int(inn[11])
