import os
import glob
import numpy as np
import pandas as pd
import math

# ============================================================
# Constants and inputs
# ============================================================

# Directory containing decoded CDP CSVs
DATA_DIR = "./"

# Columns of the 30 droplet count bins in the decoded CSV file
BIN_COLS = list(range(16, 46))  # Python is 0-indexed (17–46 in R)

# Bin boundary diameters (microns) from CDP-2 manual (p.48)
CDP_BIN_BOUNDARIES_MICRON = np.array([
    2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 22,
    24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50
])

# Sampling parameters
DT = 1                    # seconds between samples
SAMPLE_PERIOD_S = 5 * 60  # 5 minutes
LWC_FOG_THRESHOLD = 0.1   # g/m^3
RHO_WATER = 1.0           # g/cm^3

# Flow rate (manual fixed flow rate in ft³/min)
FLOW_RATE_SCFM = 5.5
# Convert SCFM to m³/s
FLOW_RATE_M3_S = (FLOW_RATE_SCFM * (0.3048 ** 3)) / 60.0


# ============================================================
# Locate and read decoded CDP data
# ============================================================

pattern = os.path.join(DATA_DIR, "decoded-data_W097_2025-02-18T000000_2025-02-18T235959.csv")
files = glob.glob(pattern)

if not files:
    raise FileNotFoundError(f"No matching CDP decoded CSV files found in {DATA_DIR}")

cdp_fp = files[0]
print(f"Reading: {cdp_fp}")

df = pd.read_csv(cdp_fp)

# ============================================================
# Calculate total droplet mass
# ============================================================

# Total droplet counts per bin over the entire sampling period
total_drop_count = df.iloc[:, BIN_COLS].sum(axis=0).to_numpy()

# Bin boundary diameters (cm)
drop_diam_max_cm = CDP_BIN_BOUNDARIES_MICRON[1:] * 1e-4
drop_diam_min_cm = CDP_BIN_BOUNDARIES_MICRON[:-1] * 1e-4

# Mean droplet volume for each bin (cm³)
drop_vol_mean_cm3 = (4 / 3) * math.pi * (
    ((drop_diam_max_cm / 2) ** 3 + (drop_diam_min_cm / 2) ** 3) / 2
)

# Total droplet mass (g)
total_drop_mass_g = np.sum(drop_vol_mean_cm3 * total_drop_count) * RHO_WATER

# ============================================================
# Calculate sample air volume (m³)
# ============================================================

sample_volume_m3 = FLOW_RATE_M3_S * SAMPLE_PERIOD_S

# ============================================================
# Calculate mean liquid water content
# ============================================================

LWC = total_drop_mass_g / sample_volume_m3
print(f"Mean Liquid Water Content (LWC): {LWC:.4f} g/m³")

# ============================================================
# Determine fog presence
# ============================================================

is_fog_present = LWC > LWC_FOG_THRESHOLD
print(f"Fog present: {is_fog_present}")
