'''
Created on Oct 12, 2016

@author: bouchcla
'''
import copy
import unittest

from connector.wingempacket import WinGemPacket

class PacketTest(unittest.TestCase):
    '''
    Test for Packets
    '''

    def setUp(self):
        self.packetstring = "WGI" + WinGemPacket.AM + "GET" + \
            WinGemPacket.AM + "INFO" + WinGemPacket.VM + "a" + WinGemPacket.VM + \
            "b" + WinGemPacket.VM + "x" + \
            WinGemPacket.SM + "y" + WinGemPacket.SM + "z"
        self.packet = WinGemPacket(self.packetstring)

    def tearDown(self):
        pass

    def test_extract(self):
        '''
        test for extract
        '''
        self.assertEqual(self.packet.extract(1), "WGI")
        self.assertEqual(self.packet.extract(1, 1), "WGI")
        self.assertEqual(self.packet.extract(1, 1, 1), "WGI")
        self.assertEqual(self.packet.extract(2, 1, 1), "GET")
        self.assertEqual(self.packet.extract(2, 2, 2), "")
        self.assertEqual(self.packet.extract(1, sm=3), "")
        self.assertEqual(self.packet.extract(1, sm=1), "")
        self.assertEqual(self.packet.extract(3, 1), "INFO")
        self.assertEqual(self.packet.extract(3, 2, 1), "a")
        self.assertEqual(self.packet.extract(3, 3, 1), "b")
        self.assertEqual(self.packet.extract(3, 2, 2), "")
        self.assertEqual(self.packet.extract(3, 4, 1), "x")
        self.assertEqual(self.packet.extract(3, 4, 2), "y")
        self.assertEqual(self.packet.extract(3, 4, 3), "z")
        self.assertEqual(self.packet.extract(3, 4, 4), "")

    def test_extractfrom(self):
        ''' Test extractfrom function '''
        self.assertEqual(self.packet.extractfrom(-1), "")
        self.assertEqual(self.packet.extractfrom(1), self.packetstring)
        self.assertEqual(self.packet.extractfrom(1, 1), "WGI")
        self.assertEqual(self.packet.extractfrom(1, 2), "")
        self.assertEqual(self.packet.extractfrom(2), self.packetstring[4:])
        self.assertEqual(self.packet.extractfrom(2, 1), "GET")
        self.assertEqual(self.packet.extractfrom(2, 2), "")
        self.assertEqual(self.packet.extractfrom(3), self.packetstring[8:])
        self.assertEqual(self.packet.extractfrom(3, 1), self.packetstring[8:])
        self.assertEqual(self.packet.extractfrom(3, 2), self.packetstring[13:])
        self.assertEqual(self.packet.extractfrom(3, 3), self.packetstring[15:])
        self.assertEqual(self.packet.extractfrom(3, 3, 1), "b")
        self.assertEqual(self.packet.extractfrom(3, 3, 2), "")
        self.assertEqual(self.packet.extractfrom(3, 4), self.packetstring[17:])
        self.assertEqual(self.packet.extractfrom(3, 4, 1), self.packetstring[17:])
        self.assertEqual(self.packet.extractfrom(3, 4, 2), self.packetstring[19:])
        self.assertEqual(self.packet.extractfrom(3, 4, 3), self.packetstring[21:])
        self.assertEqual(self.packet.extractfrom(3, 4, 4), "")
        self.assertEqual(self.packet.extractfrom(4), "")

    def test_extractaslist(self):
        ''' Test extractfrom function '''

        self.assertEqual(self.packet.extractaslist(),
                        self.packet.stringify().split(WinGemPacket.AM))
        self.assertEqual(self.packet.extractaslist(1), (["WGI"]))
        self.assertEqual(self.packet.extractaslist(1, 1), (["WGI"]))
        self.assertEqual(self.packet.extractaslist(1, 2), ([]))

        self.assertEqual(self.packet.extractaslist(2), (["GET"]))
        self.assertEqual(self.packet.extractaslist(2, 1), (["GET"]))
        self.assertEqual(self.packet.extractaslist(2, 2), ([]))

        malist = self.packet.stringify().split(WinGemPacket.AM)
        mvlist = malist[2].split(WinGemPacket.VM)
        self.assertEqual(self.packet.extractaslist(3), mvlist)
        self.assertEqual(self.packet.extractaslist(3, 1), (["INFO"]))
        self.assertEqual(self.packet.extractaslist(3, 2), (["a"]))
        self.assertEqual(self.packet.extractaslist(3, 3), (["b"]))

        msvlist = mvlist[2].split(WinGemPacket.SM)
        self.assertEqual(self.packet.extractaslist(3, 3), msvlist)

        self.assertEqual(self.packet.extractaslist(5), ([]))

    def test_replace(self):
        ''' test replace function '''
        localpacket = copy.deepcopy(self.packet)
        localpacket.replace("ABC", 1)
        self.assertEqual(localpacket.extract(1), "ABC")
        localpacket = copy.deepcopy(self.packet)
        localpacket.replace("BOB", 3)
        self.assertEqual(localpacket.extract(3), "BOB")
        localpacket = copy.deepcopy(self.packet)
        localpacket.replace("BOB", 3, 1)
        self.assertEqual(localpacket.extract(3, 1), "BOB")
        localpacket = copy.deepcopy(self.packet)
        localpacket.replace("BOB", 3, 1, 2)
        self.assertEqual(localpacket.extract(3, 1, 2), "BOB")
        localpacket = copy.deepcopy(self.packet)
        localpacket.replace("BOB", 3, 4, 2)
        self.assertEqual(localpacket.extract(3, 4, 2), "BOB")

    def test_parseoptions(self):
        ''' Test parseoptions function '''

        # Tag Only
        tagonlystring = "What is your favourite colour?"

        # Options Only
        optionsonlystring = chr(27) + '<one=Blue two="Blue. No, yel...">'
        optionsdict = {"one":"Blue", "two":"Blue. No, yel..."}

        # Both
        tagoptionsstring = optionsonlystring + tagonlystring

        # Packetify strings
        tagoptions = WinGemPacket(tagoptionsstring)
        tagonly = WinGemPacket(tagonlystring)
        optionsonly = WinGemPacket(optionsonlystring)

        # Tag Only
        newtag, newoptions = tagonly.parseoptions(1)
        self.assertEqual(newtag, tagonlystring)
        self.assertEqual(newoptions, {})

        # Options Only
        newtag, newoptions = optionsonly.parseoptions(1)
        self.assertEqual(newtag, "")
        self.assertEqual(newoptions, optionsdict)

        # Both
        newtag, newoptions = tagoptions.parseoptions(1)
        self.assertEqual(newtag, tagonlystring)
        self.assertEqual(newoptions, optionsdict)

        # No value
        emptytag, emptyoptions = tagonly.parseoptions(2)
        self.assertEqual(emptytag, "")
        self.assertEqual(emptyoptions, {})

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
