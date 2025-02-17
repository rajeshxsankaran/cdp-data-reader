#!/usr/bin/env python3

"""
This is code to initialize a connection to CDP, and ping it for data every
~1 second. Logs data to a CSV file. This is a simplified version of a script
we ran to process and log the CDP data in flight.

Original Author: Alex Hirst (https://www.linkedin.com/in/alex-hirst95/)
Extended by: Raj Sankaran (rajesh@anl.gov)

Update Notes:


"""
from waggle.plugin import Plugin
import serial
#import yaml
from datetime import datetime
import time
import csv
import zlib
import base64
from cdp_converter import CDPConverter
from message_headers import *
from CDP_decoder import CDP_decoder
from struct import pack, unpack



class cdp_client:

    def __init__(self,  ports):

        """
        Argument:
            ports: [dict] containing path to serial port to cdp sensor
        """

        self.ON = True  # if False, kills all threads

        ### Sensor Setup ###
        self.cdp_port = ports["cdp"]  # sensor port on cdp

        ### CDP Utilities Initialization ###
        self.cdp_decoder = CDP_decoder()
        self.cdp_converter = CDPConverter()
        self.cdp_init_msg = self.cdp_decoder.create_init_msg()
        self.cdp_data_msg = self.cdp_decoder.create_data_msg()


    def start_cdp_thread(self):
        cdp_connected = False
        cdp_initialized = False
        init_msg = self.cdp_decoder.create_init_msg()
        request_msg = self.cdp_decoder.create_data_msg()
        while self.ON:
            try:
                ser = serial.Serial(self.cdp_port, 57600, timeout = 1) # open serial port
                ser.flushInput()
                ser.flushOutput()
                print('Created CDP Serial Connection')
                cdp_connected = True
            except Exception as e:
                print('FAILED TO OPEN CDP SERIAL CONNECTION %s ' % e)
            while self.ON and cdp_connected and not cdp_initialized:
                try:
                    # send init msg until initialized
                    ser.flushInput()
                    ser.flushOutput()
                    ser.write(init_msg)
                    time.sleep(1)  # give CDP time to think
                    line = ser.read(4)
                    if line != b'':
                        unpacked_line = self.cdp_decoder.decode(line, 'confirm')
                        print (str(time.time()) + ',')
                        print (''.join((str(e)+',') for e in unpacked_line) + '\n')
                        if unpacked_line[0] == 6 and unpacked_line[1] == 6:
                            cdp_initialized = True
                            print('CDP initialized!')
                        else:
                            print('Rejected CDP initialization command')
                    else:
                        print('No response to CDP init command')
                    time.sleep(1)  # Give CDP time to think
                except Exception as e:
                    print('FAILED TO INITIALIZE CDP %s ' % e)
                    cdp_connected = False

            while self.ON and cdp_connected and cdp_initialized:
                try:
                    time.sleep(5)
                    ser.flushInput()
                    ser.flushOutput()
                    ser.write(request_msg)
                    line = ser.read(156)
                    if line != b'':
                        acquisition_timestamp=time.time_ns()
                        unpacked_line = self.cdp_decoder.decode(line, 'data')
                        # converted_line = self.cdp_converter.convertCDPMessage(unpacked_line)
                        # self.cdp_data = converted_line
                        # print (str(line))  #  write data to screen
                        # print (time.time(), str(line))  #  write data to screen
                        rawzb64_data = base64.b64encode(zlib.compress(line)).decode()
                        # print (time.time(), rawzb64_data)  #  write data to screen
                        with Plugin() as plugin:
                                # plugin.publish("decoded.data", converted_line, timestamp=acquisition_timestamp)
                                # plugin.publish("raw.data", str(line), timestamp=acquisition_timestamp)
                                plugin.publish("rawzb64.data", rawzb64_data, timestamp=acquisition_timestamp)
                        # self.cdp_file.flush()
                except Exception as e:
                    print('FAILED TO GET DATA FROM CDP, RESTARTING... %s' % e)
                    cdp_connected = False
                    cdp_initialized = False
                


    def main(self):

        self.start_cdp_thread()


if __name__ == "__main__":

    ports = {'cdp':'/host/dev/ttyUSB0'}
    print (ports, flush=True)
    client = cdp_client(ports)
    client.main()
