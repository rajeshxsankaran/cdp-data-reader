#!/usr/bin/env python3
import sys
import os
import re
from datetime import datetime
import time
import csv
import zlib
import base64
import pandas as pd
import numpy as np
from struct import pack, unpack
import sage_data_client
import argparse

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cdp_converter import CDPConverter
from message_headers import *
from CDP_decoder import CDP_decoder


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
    parser = argparse.ArgumentParser(description="Read timestamp-value CSV and convert timestamps.")
    parser.add_argument("filename", help="Path to the input .txt or .csv file")
    args = parser.parse_args()
    # Extract base pattern (e.g., 1761439658428968191-data_)
    match = re.match(r"(\d+-data_)", args.filename)
    if match:
        output_file = f"{match.group(1)}decoded.csv"
    else:
        # fallback if pattern not matched
        output_file = args.filename.replace(".txt", "_decoded.csv")
    # Read the file
    df = pd.read_csv(args.filename, header=None, names=["timestamp", "value"])
    # Convert epoch nanoseconds to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ns", utc=True)
    #print(df.head())
    print("\u2714 Data ingestion completed. Now decoding and generating CSV file")
    decoder = cdp_beehive_data_decoder()
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

    print("\u2139 The data is being written to",output_file)
    # Write to CSV

    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        max_values = max(len(row) for row in rows) - 1
        header = ["timestamp"] + [f"value_{i}" for i in range(1, max_values + 1)]
        writer.writerow(header)
        # Write rows
        writer.writerows(rows)

    print("\u2714 Data writeout completed")
