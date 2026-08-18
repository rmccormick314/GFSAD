import re
import csv
import sys
from pathlib import Path

INPUT  = Path(__file__).parent / "EnMAP_wavebands.txt"
OUTPUT = Path(__file__).parent / "EnMAP_wavebands.csv"

band_pattern = re.compile(
    r'<bandID number="(\d+)">\s*'
    r'<wavelengthCenterOfBand>([\d.]+)</wavelengthCenterOfBand>\s*'
    r'<FWHMOfBand>([\d.]+)</FWHMOfBand>\s*'
    r'<GainOfBand>([\d.]+)</GainOfBand>\s*'
    r'<OffsetOfBand>([\d.]+)</OffsetOfBand>\s*'
    r'</bandID>',
    re.DOTALL,
)

text = INPUT.read_text()
bands = band_pattern.findall(text)

with open(OUTPUT, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["band_number", "wavelength_center_nm", "fwhm_nm", "gain", "offset"])
    for band_num, wavelength, fwhm, gain, offset in bands:
        writer.writerow([int(band_num), float(wavelength), float(fwhm), float(gain), float(offset)])