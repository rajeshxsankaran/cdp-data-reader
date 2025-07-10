#!/usr/bin/env python3

from datetime import datetime
import time
import csv
import zlib
import base64
import pandas as pd
import numpy as np
from cdp_converter import CDPConverter
from message_headers import *
from CDP_decoder import CDP_decoder
from struct import pack, unpack
import sage_data_client


class cdp_beehive_data_decoder:

    def __init__(self):
        self.cdp_decoder = CDP_decoder()
        self.cdp_converter = CDPConverter()
        self.cdp_init_msg = self.cdp_decoder.create_init_msg()
        self.cdp_data_msg = self.cdp_decoder.create_data_msg()

    def decode_rawzb64(self, rawzb64_data):
        compressed_data = base64.b64decode(rawzb64_data)
        line = zlib.decompress(compressed_data)
        unpacked_line = self.cdp_decoder.decode(line, 'data')
        converted_line = self.cdp_converter.convertCDPMessage(unpacked_line)
        return converted_line


# Utility: Recursively convert numpy types to native Python types
def convert_numpy_types(obj):
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    elif isinstance(obj, np.generic):
        return obj.item()  # Converts np.float64, np.int64, etc.
    else:
        return obj

if __name__ == "__main__":

    node_id = "W097"
    start_date = "2025-02-18T00:00:00Z"
    end_date = "2025-02-18T23:59:59Z"

    print("\u2139 Fetching data from",start_date,"to",end_date,"from beehive for node",node_id)

    decoder = cdp_beehive_data_decoder()
    df = sage_data_client.query(
        start=start_date,
        end=end_date,
        filter={
            "plugin": "registry.sagecontinuum.org/rajesh/cpd-data-reader:0.1.3.*",
            "vsn": node_id
        }
    )

    print("\u2714 Data download completed. Now decoding and generating CSV file")
    rows = []
    for _, row in df.iterrows():
        timestamp = row["timestamp"]
        value = row["value"]
        try:
            decoded = decoder.decode_rawzb64(value)
            decoded_clean = convert_numpy_types(decoded)

            # Handle dict or list
            if isinstance(decoded_clean, dict):
                values = list(decoded_clean.values())
            elif isinstance(decoded_clean, list):
                values = decoded_clean
            else:
                values = [decoded_clean]

            rows.append([timestamp] + values)

        except Exception as e:
            print(f"[ERROR] Failed to decode at {timestamp}: {e}")

    filename = f"decoded-data_{node_id}_{start_date}_{end_date}".replace(":", "").replace("Z", "").replace(".", "")
    filename = filename+'.csv'
    print("\u2139 The data is being written to",filename)
    # Write to CSV

    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        max_values = max(len(row) for row in rows) - 1
        header = ["timestamp"] + [f"value_{i}" for i in range(1, max_values + 1)]
        writer.writerow(header)
        # Write rows
        writer.writerows(rows)

    print("\u2714 Data writeout completed")
