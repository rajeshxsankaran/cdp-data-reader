
"""
This is a class to decode CDP messages.

Author: Alex Hirst (https://www.linkedin.com/in/alex-hirst95/)
"""

from struct import pack, unpack


class CDP_decoder:
    def __init__(self):
        self.receive_data_format = [2, 2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 2, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4,
        4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 2]
        self.receive_data_format = [i * 2 for i in self.receive_data_format]

        self.receive_confirm_format = [2, 2, 2, 2]


    def decode(self, msg, type):
        """
        Inputs: msg in byte string format

        Outputs: a decoded list of integers
        """
        if type == 'data':
            format = self.receive_data_format
        elif type == 'confirm':
            format = self.receive_confirm_format

        hex_str = msg.hex()  # turn bytes to hex string
        parsed_hex_str = []
        i = 0
        for n in format:
            if n == 8:
                h = hex_str[i+4:i+8] + hex_str[i:i+4]  # parse hex str according to format
                parsed_hex_str.append(h)
            else:
                parsed_hex_str.append(hex_str[i:i+n])
            i = i + n

        parsed_bytes = []
        for x in parsed_hex_str:
            parsed_bytes.append(bytes.fromhex(x))  # turn hex string back to bytes

        # decode by little endianess
        parsed_decoded_bytes = []
        for x in parsed_bytes:
            if len(x) == 1:
                parsed_decoded_bytes.append(unpack('B', x)[0])
            elif len(x) == 2:
                parsed_decoded_bytes.append(unpack('<H', x)[0])
            elif len(x) == 4:
                parsed_decoded_bytes.append(unpack('<L', x)[0])
            else:
                print('ERROR!')
                break

        return parsed_decoded_bytes


    def create_init_msg(self):
        """
        Creates a bytestring to send to CDP over serial port with initialization
        settings.
        """
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
        return msg


    def create_data_msg(self):
        """
        Creates a bytestring to send to CDP over serial port to request data.
        """
        msg = [27, 2, 29]
        msg = pack('<2BH', *msg)  # send data command
        return msg
