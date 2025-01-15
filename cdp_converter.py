"""
A class that implements conversion of CDP messages (list of bytes) to proper units.

Author: Alex Hirst (https://www.linkedin.com/in/alex-hirst95/)
"""
import numpy as np

class CDPConverter:

    def __init__(self):
        pass 
    
    def convertCDPMessage(self, msg):
        """ Converts ad values in list to proper units
        Args:
            msg: (list) list of ad values from CDP
        Returns:
            out: (list) list of measurement values in proper units
        """
        LaserCurrent = self.adToMA(msg[0])
        DumpSpotMonitor = self.adToVolts(msg[1])
        WingboardTemp = self.adToCelcius(msg[2])
        LaserTemp = self.adToCelcius(msg[3])
        SizerBaseline = self.adToVolts(msg[4])
        QualifierBaseline = self.adToVolts(msg[5])
        Monitor5V = self.adTo5VMonitor(msg[6])
        ControlBoardTemp = self.adTo_Control_Board_T(msg[7])

        out = [
            LaserCurrent,
            DumpSpotMonitor,
            WingboardTemp,
            LaserTemp,
            SizerBaseline,
            QualifierBaseline,
            Monitor5V,
            ControlBoardTemp
        ] + msg [8:]

        return out

    def adToVolts(self, ad):
        V = 5 * (ad / 4095)  # volts
        return V

    def adTo5VMonitor(self, ad):
        # From Sam. As using adToVolts * 2e10 before! 
        V = ad * 0.00244  # 5 volt monitor
        return V
    
    def adToMA(self, ad):
        mA = 0.061 * ad  # milliamps
        return mA
    
    def adToCelcius(self, ad):
        V = self.adToVolts(ad)
        C = (np.log((5/V) - 1) / 3750 + 1 / 298) ** (-1) - 273  # Celcius
        return C
    
    def adTo_Control_Board_T(self, ad):
        # C = (0.06401 * ad) - 50  # old equation

        # From Sam:
        C = 153.973297 - 0.047819 * ad - 8.609166e-7 * (ad **2)  # Celcius
        return C


if __name__ == '__main__':

    data = [1256, 4001, 1644, 1783, 97, 102, 2010, 2322, 0, 12, 102, 0, 6, 97, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1447]

    decoder = CDPConverter()

    out = decoder.convertCDPMessage(data)

    print(data)
    print(out)
    print(out[6], out[7])

