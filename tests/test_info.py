'''
Created on Nov 28, 2016

@author: bouchcla
'''
import os
import unittest

from components.info import Info
from connector.wingempacket import WinGemPacket


class TestInfo(unittest.TestCase):
    ''' Test Info Packets '''

    def testinfopackets(self):
        ''' test Info object '''
        info = Info()
        # Data Path
        packet = "WGI" + WinGemPacket.AM + "DATAPATH"
        handled, hostdata, _ = info.addpacket(WinGemPacket(packet))
        self.assertTrue(handled)
        self.assertEqual(hostdata, "static" + os.sep + "data" + os.sep)
        # Directory
        if __name__ == "__main__":
            os.chdir(".." + os.sep)
        packet = "WGI" + WinGemPacket.AM + "DIR" + WinGemPacket.AM + \
            WinGemPacket(hostdata).extract(1, 2)
        handled, hostdata, _ = info.addpacket(WinGemPacket(packet))
        self.assertTrue(handled)
        results = WinGemPacket(hostdata)
        self.assertTrue(results)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
