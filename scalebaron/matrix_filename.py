"""
Shared matrix filename parsing for ScaleBarOn and Muad'Data.

Filename convention (field order is fixed; tokens are otherwise opaque labels):

  {sample} {analyte}_{unit} matrix.(xlsx|csv)   — concentration or CPS
  {sample} {analyte} matrix.(xlsx|csv)          — raw counts (unit_type 'raw')

The analyte token is stored and displayed as written (e.g. Ca44, CaF602, CaF603,
278nm, TotalMo). The parser does not validate chemistry or infer whether trailing
digits are isotope mass, wavelength, or an instrument channel ID.
"""

import os
import re

_MATRIX_EXT = r"matrix\.(?:xlsx|csv)"

# Opaque analyte / channel label — not chemically validated.
# Order matters only among these alternatives (longest/most specific first).
_ANALYTE_PATTERN = (
    r"(?:"
    r"Total[A-Za-z]+"          # summed channel, e.g. TotalMo
    r"|\d{2,4}nm"              # wavelength-style, e.g. 278nm
    r"|[A-Za-z][A-Za-z0-9]*"   # e.g. Ca44, CaF, CaF602, CaF603, Mo98
    r")"
)

_UNIT_PATTERN = r"(?:ppm|CPS)"


def _normalize_unit(unit):
    if unit.upper() == "CPS":
        return "CPS"
    return "ppm"


def parse_matrix_filename(filename):
    """
    Parse a matrix filename.

    Returns:
        (sample, analyte, unit_type) where unit_type is 'ppm', 'CPS', or 'raw';
        None if the name does not match the convention.
    """
    basename = os.path.basename(filename)
    flags = re.IGNORECASE

    match = re.match(
        rf"(.+?)[ _]({_ANALYTE_PATTERN})_({_UNIT_PATTERN}) {_MATRIX_EXT}\s*$",
        basename,
        flags=flags,
    )
    if match:
        sample, analyte, unit_type = match.groups()
        return sample.strip(), analyte, _normalize_unit(unit_type)

    match = re.match(
        rf"(.+?) ({_ANALYTE_PATTERN}) {_MATRIX_EXT}\s*$",
        basename,
        flags=flags,
    )
    if match:
        sample, analyte = match.groups()
        return sample.strip(), analyte, "raw"

    return None
