'''
Created on Oct 17, 2016

@author: bouchcla
'''
import inspect
import os
import unittest
from connector.logfilereader import LogFileReader
from connector.packetprocessor import PacketProcessor
from connector.wingempacket import WinGemPacket

class TestPacketProcesser(unittest.TestCase):
    ''' Test Packet Processor '''

    def testlog(self):
        ''' tests! '''
        # script filename (usually with path)
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/testscreen.txt")
        pprocessor = PacketProcessor("abc", [], [], None)
        while True:
            packetdata = testlog.nextpacket(includestxetx=True)
            if packetdata:
                _, y = pprocessor.processinput(packetdata)
                self.assertFalse(y)
            else:
                break
        testlog.close()

    def testoddcases(self):
        ''' test badly broken up data '''
        pprocessor = PacketProcessor("abc", [], [], None)
        # Full Packet, just returns host data
        rawdata = chr(2) + "WA" + WinGemPacket.AM + "GETSTART" + chr(3)
        rdata, hostdata = pprocessor.processinput(rawdata)
        self.assertEqual(len(hostdata), 1)
        self.assertEqual(len(rdata), 0)
        # TCL data, incomplete packet, returns just TCL data
        rawdata = "abc" + chr(2) + "WA" + WinGemPacket.AM + "GETSTART"
        rdata, hostdata = pprocessor.processinput(rawdata)
        self.assertEqual(len(hostdata), 0)
        self.assertEqual(len(rdata), 1)
        # rest of packet, returns full packet object
        rawdata = chr(3)
        rdata, hostdata = pprocessor.processinput(rawdata)
        self.assertEqual(len(hostdata), 1)
        self.assertEqual(len(rdata), 0)
        # big string with multiple objects
        rawdata = chr(2) + "WA" + WinGemPacket.AM + "GETSTART" + \
            chr(3) + chr(2) + "WA" + WinGemPacket.AM + "GETSTART" + chr(3)
        rdata, hostdata = pprocessor.processinput(rawdata)
        self.assertEqual(len(hostdata), 2)
        self.assertEqual(len(rdata), 0)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
