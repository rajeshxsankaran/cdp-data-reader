# Fetching Data from CDP

This plugin interfaces with the [Cloud Droplet Probe (CDP)](https://www.dropletmeasurement.com/product/cloud-droplet-probe/) and collects data which is uploaded to beehive in a compressed base64 printable format. 

# Fetching and Decoding the CDP Data from Beehive

This tool helps download and decode CDP data into a human-readable CSV format.

## Overview

The script `beehive-data-decoder.py` fetches and decodes CDP data for a specified date range. It produces a CSV file with decoded values for analysis or archival.

## Usage

Run the script using Python 3:

```bash
python3 beehive-data-decoder.py
```

Before running, set the desired node id and date range in the script:

```Python
node_id = "W097"
start_date = "2025-03-18T00:00:00Z"
end_date = "2025-03-21T23:59:59Z"
```

### The Script

Each run generates a new CSV file named:

```bash
decoded-data-<start>-<end>.csv
```

For example:

```bash
decoded-data-2025-03-18T000000-2025-03-21T235959.csv
```

## Output Format

The CSV file includes a header and 47 columns:
```css
time-stamp, value_1, value_2, ..., value_46
```

  - value_1 — U16 representing Laser Current / Housekeeping 1
  - value_2 through value_15 — Housekeeping and ADC Overflow values
  - value_16 through value_45 — U32 bin counts (BIN 1 to BIN 30)
  - value_46 — U16 checksum (CRC)

These columns follow the structure defined in _Table 6: CDP Response to Send Data Command – Data Packet_ in the CDP documentation.


