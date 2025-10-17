#!/usr/bin/env python3
"""
CDP Reader with power control integration.

- Turns ON CDP and pump, waits for stabilization.
- Collects CDP data in 5-minute buffers.
- Computes mean LWC and fog presence.
- If no fog is detected (LWC < threshold), turns OFF power and exits.

Author: Raj Sankaran (rajesh@anl.gov)
"""

import serial
import time
import base64
import zlib
from waggle.plugin import Plugin
from datetime import datetime
from cdp_converter import CDPConverter
from CDP_decoder import CDP_decoder
from struct import unpack
import numpy as np
import math

# Import power control module
import power_switch

# ============================================================
# Configurable parameters
# ============================================================

BUFFER_DURATION_S = 5 * 60  # seconds
LWC_FOG_THRESHOLD = 0.1     # g/m³
FLOW_RATE_SCFM = 5.5        # ft³/min
FLOW_RATE_M3_S = (FLOW_RATE_SCFM * (0.3048 ** 3)) / 60.0
RHO_WATER = 1.0             # g/cm³
CDP_BIN_BOUNDARIES_MICRON = np.array([
    2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 22,
    24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50
])

# ============================================================
# CDP Client Class
# ============================================================

class CDPClient:
    def __init__(self, ports):
        self.ON = True
        self.cdp_port = ports["cdp"]
        self.cdp_decoder = CDP_decoder()
        self.cdp_converter = CDPConverter()
        self.buffer = []
        self.last_process_time = time.time()
        self.plugin = Plugin()

    def start(self):
        print("Powering on CDP and pump...")
        power_switch.turn_on_cdp()
        power_switch.turn_on_pump()
        time.sleep(30)  # wait for stabilization

        while self.ON:
            try:
                ser = serial.Serial(self.cdp_port, 57600, timeout=1)
                ser.flushInput()
                ser.flushOutput()
                print("CDP serial connection established")
                self.collect_data(ser)
            except Exception as e:
                print(f"Failed to open CDP serial connection: {e}")
                time.sleep(2)

    def collect_data(self, ser):
        init_msg = self.cdp_decoder.create_init_msg()
        request_msg = self.cdp_decoder.create_data_msg()

        if not self.initialize_sensor(ser, init_msg):
            print("Sensor initialization failed.")
            return

        print("CDP initialized, starting data collection...")
        while self.ON:
            try:
                time.sleep(0.97)
                ser.flushInput()
                ser.flushOutput()
                ser.write(request_msg)
                line = ser.read(156)
                if line:
                    timestamp = time.time_ns()
                    rawzb64_data = base64.b64encode(zlib.compress(line)).decode()
                    self.plugin.publish("rawzb64.data", rawzb64_data, timestamp=timestamp)
                    self.buffer.append((timestamp, rawzb64_data))
                    print(time.asctime(),rawzb64_data)
                    if len(self.buffer) >= 300:
                        fog_present = self.process_buffer()
                        self.buffer.clear()
                        if not fog_present:
                            print("No fog detected — turning off CDP and pump.")
                            power_switch.turn_off_cdp()
                            power_switch.turn_off_pump()
                            self.ON = False
                else:
                    print("No response from CDP during data read")
            except Exception as e:
                print(f"Error reading CDP data: {e}")
                break

    def initialize_sensor(self, ser, init_msg):
        for _ in range(5):
            ser.flushInput()
            ser.flushOutput()
            ser.write(init_msg)
            time.sleep(1)
            line = ser.read(4)
            if line:
                try:
                    unpacked_line = self.cdp_decoder.decode(line, "confirm")
                    if unpacked_line[0] == 6 and unpacked_line[1] == 6:
                        return True
                except Exception:
                    pass
        return False

    def process_buffer(self):
        if not self.buffer:
            print("No data to process.")
            return True

        print(f"Processing {len(self.buffer)} samples...")
        decoded_rows = []
        for ts, rawzb64 in self.buffer:
            try:
                line = zlib.decompress(base64.b64decode(rawzb64))
                unpacked = self.cdp_decoder.decode(line, "data")
                converted = self.cdp_converter.convertCDPMessage(unpacked)
                if isinstance(converted, dict):
                    decoded_rows.append(list(converted.values()))
                elif isinstance(converted, list):
                    decoded_rows.append(converted)
            except Exception:
                continue

        self.buffer.clear()
        if not decoded_rows:
            print("No valid decoded samples.")
            return True

        df = np.array(decoded_rows)
        lwc = self.calculate_LWC(df)
        fog_present = lwc > LWC_FOG_THRESHOLD

        print(f"Mean LWC = {lwc:.4f} g/m³ | Fog present: {fog_present}")
        timestamp = time.time_ns()
        self.plugin.publish("cdp.lwc", lwc, timestamp=timestamp)
        self.plugin.publish("cdp.fog_present", fog_present, timestamp=timestamp)

        return fog_present

    def calculate_LWC(self, df):
        try:
            bin_cols = list(range(16, 46))
            total_drop_count = np.sum(df[:, bin_cols], axis=0)
            drop_diam_max_cm = CDP_BIN_BOUNDARIES_MICRON[1:] * 1e-4
            drop_diam_min_cm = CDP_BIN_BOUNDARIES_MICRON[:-1] * 1e-4
            drop_vol_mean_cm3 = (4 / 3) * math.pi * (
                ((drop_diam_max_cm / 2) ** 3 + (drop_diam_min_cm / 2) ** 3) / 2
            )
            total_drop_mass_g = np.sum(drop_vol_mean_cm3 * total_drop_count) * RHO_WATER
            sample_volume_m3 = FLOW_RATE_M3_S * BUFFER_DURATION_S
            LWC = total_drop_mass_g / sample_volume_m3
            return LWC
        except Exception:
            return 0.0


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    ports = {"cdp": "/host/dev/ttyUSB0"}
    print(f"Starting CDP client on port {ports['cdp']}")
    client = CDPClient(ports)
    client.start()
