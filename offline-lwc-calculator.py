#!/usr/bin/env python3

import sys
import base64
import zlib
import numpy as np
import math
from cdp_converter import CDPConverter
from CDP_decoder import CDP_decoder

# ---- Constants (same as original code) ----
LWC_FOG_THRESHOLD = 0.1     # g/m³
FLOW_RATE_SCFM = 5.5        # ft³/min
FLOW_RATE_M3_S = (FLOW_RATE_SCFM * (0.3048 ** 3)) / 60.0
BUFFER_DURATION_S = 15 * 60 # 15 min files. Modify as needed.
RHO_WATER = 1.0
CDP_BIN_BOUNDARIES_MICRON = np.array([
    2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 22,
    24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50
])

decoder = CDP_decoder()
converter = CDPConverter()


def calculate_LWC(df):
    try:
        bin_cols = list(range(15, 45))
        total_drop_count = np.sum(df[:, bin_cols], axis=0)
        print (total_drop_count)
        drop_diam_max_cm = CDP_BIN_BOUNDARIES_MICRON[1:] * 1e-4
        drop_diam_min_cm = CDP_BIN_BOUNDARIES_MICRON[:-1] * 1e-4

        drop_vol_mean_cm3 = (4 / 3) * math.pi * (
            ((drop_diam_max_cm / 2) ** 3 + (drop_diam_min_cm / 2) ** 3) / 2
        )
        # print(drop_vol_mean_cm3)
        total_drop_mass_g = np.sum(drop_vol_mean_cm3 * total_drop_count) * RHO_WATER
        sample_volume_m3 = FLOW_RATE_M3_S * BUFFER_DURATION_S
        LWC = total_drop_mass_g / sample_volume_m3
        return LWC
    except Exception:
        return 0.0


def process_saved_file(txt_file):
    buffer = []
    decoded_rows = []

    try:
        with open(txt_file, "r") as f:
            for line in f:
                try:
                    ts, raw = line.strip().split(",", 1)
                    buffer.append((int(ts), raw))
                except:
                    continue
    except FileNotFoundError:
        print(f"ERROR: File not found: {txt_file}")
        return

    if not buffer:
        print("No data in input file.")
        return

    print(f"Loaded {len(buffer)} records from {txt_file}")

    for ts, rawzb64 in buffer:
        try:
            raw = zlib.decompress(base64.b64decode(rawzb64))
            unpacked = decoder.decode(raw, "data")
            converted = converter.convertCDPMessage(unpacked)

            if isinstance(converted, dict):
                decoded_rows.append(list(converted.values()))
            elif isinstance(converted, list):
                decoded_rows.append(converted)
        except:
            continue

    if not decoded_rows:
        print("No valid decoded samples.")
        return

    df = np.array(decoded_rows)
    lwc = calculate_LWC(df)
    fog_present = lwc > LWC_FOG_THRESHOLD

    print("====================================================")
    print(f"Mean LWC: {lwc:.12f} g/m³")
    print(f"Fog detected? {fog_present}")
    print("====================================================")

    return lwc, fog_present


# ---------- Main Entry Point ----------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:")
        print(f"  {sys.argv[0]} /path/to/data_15min_rawzb64_data.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    process_saved_file(input_file)
