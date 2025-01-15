#!/usr/bin/env python3

"""
This script is a simple test of the CDP over serial port. CDP responses are
printed to terminal.

Author: Alex Hirst (https://www.linkedin.com/in/alex-hirst95/
"""

import serial
import time
from struct import pack, unpack
from datetime import datetime
from binascii import hexlify
from CDP_decoder import CDP_decoder


# Open serial port to CDP
ser = serial.Serial('/dev/ttyUSB0', 57600, timeout=3) # open serial port

# Create CDP message decoder
decoder = CDP_decoder()


# Create initialization essage
b1 = 27
b2 = 1
b3 = 60
b4 = 0
b5 = 30
b6 = [1, 0, 128, 0, 0, 1]

data = [b1, b2, b3, b4, b5] + b6

bin_boundaries = [83, 105, 173, 219, 265, 307, 353, 367, 407,
                  428, 445, 502, 593, 726, 913, 1100, 1258,
                  1396, 1523, 1661, 1803, 2008, 2274, 2533,
                  2782, 3017, 3252, 3477, 3716, 4025, 4095,
                  4095, 4095, 4095, 4095, 4095, 4095, 4095,
                  4095, 4095]

data = data + bin_boundaries
n_elements = len(data) - 2

msg_format = '<' + '2B' + str(n_elements) + 'H'
msg = pack(msg_format, *data)

checksum = sum(list(msg))

data = data + [checksum]
n_elements = len(data) - 2

msg_format = '<' + '2B' + str(n_elements) + 'H'
msg = pack(msg_format, *data)

# Create initialization message manually
init_msg = [0x1B, 0x01, 0x3C, 0x00, 0x00, 0x00, 0x1E, 0x00, 0x01, 0x00, 0x00,
0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x53, 0x00, 0x69, 0x00,
0xAD, 0x00, 0xDB, 0x00, 0x09, 0x01, 0x33, 0x01, 0x61, 0x01, 0x6F, 0x01, 0x97,
0x01, 0xAC, 0x01, 0xBD, 0x01, 0xF6, 0x01, 0x51, 0x02, 0xD6, 0x02, 0x91, 0x03,
0x4C, 0x04, 0xEA, 0x04, 0x74, 0x05, 0xF3, 0x05, 0x7D, 0x06, 0x0B, 0x07, 0xD8,
0x07, 0xE2, 0x08, 0xE5, 0x09, 0xDE, 0x0A, 0xC9, 0x0B, 0xB4, 0x0C, 0x95, 0x0D,
0x84, 0x0E, 0xB9, 0x0F, 0xFF, 0x0F, 0xFF, 0x0F, 0xFF, 0x0F, 0xFF, 0x0F, 0xFF,
0x0F, 0xFF, 0x0F, 0xFF, 0x0F, 0xFF, 0x0F, 0xFF, 0x0F, 0xFF, 0x0F, 0x04, 0x1E]

init = 0

while init == 0:
    print('sent init message')
    ser.flushInput()
    ser.flushOutput()
    ser.write(msg)
    time.sleep(1)
    print(ser.in_waiting)
    line = ser.read(4)
    if line != b'':

        print('INIT MESSAGE RESPONSE')
        print(line)
        line_unpacked = decoder.decode(line, 'confirm')
        print(line_unpacked)
        if line_unpacked[0] == 6 and line_unpacked[1] == 6:
            print('CDP is initialized')
            init = 1
    else:
        print('no response')
    time.sleep(1)


msg = [27, 2, 29]
msg = pack('<2BH', *msg)  # send data command

while True:
    ser.flush()
    print('requesting CDP data...')
    ser.write(msg)
    line = ser.read(156)
    if line != b'':
        print('cdp response:')
        print(line)
        unpacked_line = decoder.decode(line, 'data')
        print('unpacked response:')
        print(unpacked_line)
    else:
        print('no message')

    time.sleep(1)
