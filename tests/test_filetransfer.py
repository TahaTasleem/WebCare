'''
Created on Oct 20, 2016

@author: bouchcla
'''
# pylint: disable=broad-except, wrong-import-position

# import logging
import base64
import inspect
import os
import unittest

from components.filetransfer import FileTransfer, getfiletuple
from connector.logfilereader import LogFileReader
from connector.wingempacket import WinGemPacket


def getpath():
    ''' get path of current module '''
    # script filename (usually with path)
    return os.path.splitdrive(inspect.getfile(inspect.currentframe()))[1]


class TestFileTransfer(unittest.TestCase):
    ''' Test WFT Packets '''

    def tearDown(self):
        ''' Cleanup after tests '''
        unittest.TestCase.tearDown(self)
        self._cleanupfiles()

    def setUp(self):
        ''' Cleanup before tests '''
        unittest.TestCase.setUp(self)
        self._cleanupfiles()

    def _cleanupfiles(self):
        ''' Cleanup File Data '''
        testfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        try:
            os.remove("target.png")
        except Exception:
            pass
        try:
            os.remove("testfile.txt")
        except Exception:
            pass
        import shutil
        # remove the test static
        shutil.rmtree(testfilepath + '/static/data/', ignore_errors=True)
        # remove the fake abc session
        shutil.rmtree('static/data/abc', ignore_errors=True)

    def testopenclose(self):
        ''' Test Open/Close Packets '''
        # open file we know to be there
        packet = WinGemPacket("WFT" + WinGemPacket.AM + "OPEN" + WinGemPacket.AM +
                              "HOLD" + WinGemPacket.AM + "READ" + WinGemPacket.AM + getpath())
        x = FileTransfer("abc")
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(WinGemPacket(hostdata).extract(1, 1), "1")
        packet = WinGemPacket(
            "WFT" + WinGemPacket.AM + "CLOSE" + WinGemPacket.AM + "HOLD")
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(WinGemPacket(hostdata).extract(1, 1), "1")

    def testwrite(self):
        ''' Test Write Packets '''
        # open packet
        try:
            os.remove("static/data/abc/testfile.txt")
        except Exception:
            pass
        packet = WinGemPacket(
            "WFT" + WinGemPacket.AM + "OPEN" + WinGemPacket.AM + "HOLD" +
            WinGemPacket.AM + "WRITE" + WinGemPacket.AM + "testfile.txt")
        x = FileTransfer("abc")
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(WinGemPacket(hostdata).extract(1, 1), "1")
        # Write Data
        data = base64.b64encode("".join(map(str, range(0, 1024))
                                ).encode()).decode("ISO-8859-1")
        packet = WinGemPacket("WFT" + WinGemPacket.AM + "WRITE" +
                              WinGemPacket.AM + "HOLD" + WinGemPacket.AM + data)
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(hostdata, None)
        # Close
        packet = WinGemPacket(
            "WFT" + WinGemPacket.AM + "CLOSE" + WinGemPacket.AM + "HOLD")
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(WinGemPacket(hostdata).extract(1, 1), "1")
        self.assertTrue(os.path.isfile("static/data/abc/testfile.txt"))

    def testwriteuue(self):
        ''' Test Write of UUEncoded Files '''
        # open packet
        try:
            os.remove("static/data/abc/target.png.uue")
            os.remove("static/data/abc/target.png")
        except Exception:
            pass
        packet = WinGemPacket(
            "WFT" + WinGemPacket.AM + "OPEN" + WinGemPacket.AM + "HOLD" + WinGemPacket.AM +
            "WRITE" + WinGemPacket.AM + "target.png.uue")
        x = FileTransfer("abc")
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(WinGemPacket(hostdata).extract(1, 1), "1")
        # Write Data
        uuedata = "begin 644 target.png" + chr(10) + \
            "MB5!.1PT*&@H````-24A$4@```!@````8\"`8```#@=SWX```!I4E$051XVKW6" + chr(10) + \
            "M32@$81S'\\6<E>^+F(!<.'+124C8WCE(HY+455Y27O.7@XN5`\\G(EDM*VM2DY" + chr(10) + \
            "M<M,J*=D<.'#!Q45.)'RG_4U-:UN[&/_ZM-/NS/SF^3\\SSZS'I%=#^,!2J@=X" + chr(10) + \
            "MT@R8COO\\=8`7S6A`!?+U_1U.$48(+S\\):,$\"HMC!,7KUVSJJT`$?1A!,-2`#" + chr(10) + \
            "M*ZA!#R+?M,B/#1QB`._?!:RA!/5X1IX.K$.Q]KG\"OB[D`=G8PR7ZD@6TZ.HJ" + chr(10) + \
            "M=?(V+&-;;6K2?B&UITOANPHYT?'!1`'6A%XK)**3S^G*H]IG4)_V;>K32,85" + chr(10) + \
            "MXM?)BXPFWAG0B7;4JBWGFH>H25X^];],[3K0:'?B`ZQAA_6#=>59&#:IU2)>" + chr(10) + \
            "M,:'6-=KM=`;<HAHWN$``9W'S%=#VEHD]T7:5Z[M2%.((!?9!5E]S,(5YO&'2" + chr(10) + \
            "MQ)Z!1T>_N]&O[55L.N8E5Z.U1IZ)4<SBR:V`,<S8`:ZWZ-\\FV?7;U/4'S9BO" + chr(10) + \
            "M2T6KB:TW?[)4V.7J8F>5Z\\NULUVNO'\"<Y57?K=O.?F5:]_^]^8-79J)*U**D" + chr(10) + \
            "<E6Y`VG];/@%)SIO[\\EH,XP````!)14Y$KD)@@@``" + chr(10) + \
            "`" + chr(10) + \
            "end" + chr(10)
        uuedata = base64.b64encode(uuedata.encode()).decode("ISO-8859-1")
        packet = WinGemPacket("WFT" + WinGemPacket.AM + "WRITE" +
                              WinGemPacket.AM + "HOLD" + WinGemPacket.AM + uuedata)
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(hostdata, None)
        # Close
        packet = WinGemPacket(
            "WFT" + WinGemPacket.AM + "CLOSE" + WinGemPacket.AM +
            "HOLD" + WinGemPacket.AM + "UUDECODE")
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(WinGemPacket(hostdata).extract(1, 1), "1")
        self.assertTrue(os.path.isfile("static/data/abc/target.png"))

    def testlog(self):
        ''' Test against a log file '''
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/edgescreen.txt")
        ftobject = FileTransfer("abc")
        while True:
            packetdata = testlog.nextpacket(includestxetx=False)
            if packetdata:
                packet = WinGemPacket(packetdata)
                if packet.extract(1) == "WFT":
                    ftobject.addpacket(packet)
            else:
                break
            if ftobject.iscomplete():
                break
        testlog.close()

    def testread(self):
        ''' Test Read Packets '''
        # open packet
        packet = WinGemPacket(
            "WFT" + WinGemPacket.AM + "OPEN" + WinGemPacket.AM + "HOLD" + WinGemPacket.AM +
            "READ" + WinGemPacket.AM + getpath())
        x = FileTransfer("abc")
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(WinGemPacket(hostdata).extract(1, 1), "1")
        # Write Data
        packet = WinGemPacket(
            "WFT" + WinGemPacket.AM + "READ" + WinGemPacket.AM + "HOLD")
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(WinGemPacket(hostdata).extract(1, 1), "WFTREAD")
        # Close
        packet = WinGemPacket(
            "WFT" + WinGemPacket.AM + "CLOSE" + WinGemPacket.AM + "HOLD")
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(WinGemPacket(hostdata).extract(1, 1), "1")

    def testfiletuple(self):
        ''' Test Directory Determination '''
        # test file paths
        directory, filename = getfiletuple("V20171/313/test.file", "", "abc")
        self.assertEqual(directory, "static" + os.sep + "data" +
                         os.sep + "V20171" + os.sep + "abc" + os.sep)
        self.assertEqual(filename, "test.file")
        directory, filename = getfiletuple("V20171/test.file", "", "abc")
        self.assertEqual(directory, "static" + os.sep + "data" + os.sep + "V20171" + os.sep)
        directory, filename = getfiletuple("test.file", "", "abc")
        self.assertEqual(directory, "static" + os.sep + "data" + os.sep + "abc" + os.sep)
        directory, filename = getfiletuple("313/test.file", "", "abc")
        self.assertEqual(directory, "static" + os.sep + "data" + os.sep + "abc" + os.sep)
        directory, filename = getfiletuple("313/bob/test.file", "", "abc")
        self.assertEqual(directory, "static" + os.sep + "data" +
                         os.sep + "abc" + os.sep + "bob" + os.sep)
        directory, filename = getfiletuple("./V20171/314/started.flg", "", "abc")
        self.assertEqual(directory, "static" + os.sep + "data" +
                         os.sep + "V20171" + os.sep + "abc" + os.sep)
        directory, filename = getfiletuple("static/V20171/css/", "", "abc")
        self.assertEqual(directory, "static" + os.sep + "V20171" + os.sep + "css" + os.sep)
        directory, filename = getfiletuple(r"./V20171/images/error.gif", "", "abc")
        self.assertEqual(directory, "static" + os.sep + "data" +
                         os.sep + "V20171" + os.sep + "images" + os.sep)
        directory, filename = getfiletuple("static/V20171\\", "", "abc")
        self.assertEqual(directory, "static" + os.sep + "V20171" + os.sep)
        directory, filename = getfiletuple(".\\V20171\\scripts\\", "", "abc")
        self.assertEqual(directory, "static" + os.sep + "data" +
                         os.sep + "V20171" + os.sep + "scripts" + os.sep)
        directory, filename = getfiletuple("c:\\bob\\bob.pgm", "", "abc")
        self.assertEqual(directory[0:13].upper(), ("static" +
                                                   os.sep + "data" + os.sep + "v").upper())
        self.assertEqual(directory[18:], os.sep + "abc" + os.sep)
        self.assertEqual(filename, "bob.pgm")
        directory, filename = getfiletuple("boo\\hoo.txt", "", "abc")
        self.assertEqual(directory, "static" + os.sep + "data" +
                         os.sep + "abc" + os.sep + "boo" + os.sep)
        self.assertEqual(filename, "hoo.txt")
        directory, filename = getfiletuple("static\\data\\v20171\\315\\navbar.htm", "", "abc")
        self.assertEqual("static" + os.sep + "data" + os.sep +
                         "v20171" + os.sep + "abc" + os.sep, directory)
        directory, filename = getfiletuple(
            "static\\data\\v18\\8\\sys.pgm_edge.apply.action.sgx", "", "abc")
        self.assertEqual("static" + os.sep + "data" + os.sep +
                         "v18" + os.sep + "abc" + os.sep, directory)
        directory, filename = getfiletuple(
            "/\/\cmwls-rhaxis.csi.campana.com/\home/\mwh/\hullsmik_1803.csv", "", "abc")
        self.assertEqual(directory[0:13].upper(), ("static" +
                                                   os.sep + "data" + os.sep + "v").upper())
        self.assertEqual(filename, "hullsmik_1803.csv")
        directory, filename = getfiletuple(
            "uploads/v18/cc9708db-bf33-488c-83e1-bf872b921676/new-sbc_19nov18_1025.rtf", "", "abc")
        self.assertEqual(filename, "new-sbc_19nov18_1025.rtf")

    def testbase64read(self):
        ''' Test base64 file transfers '''
        if __name__ == "__main__":
            os.chdir("..\\")
        packet = WinGemPacket("WFT" + WinGemPacket.AM + "OPEN" + WinGemPacket.AM + "HOLD" +
                              WinGemPacket.AM + "READ" + WinGemPacket.AM +
                              "static/js/xterm.js")
        x = FileTransfer("abc")
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(WinGemPacket(hostdata).extract(1, 1), "1")
        for _ in range(1, 5):
            packet = WinGemPacket("WFT" + WinGemPacket.AM + "READ" + WinGemPacket.AM +
                                  "HOLD" + WinGemPacket.AM + "BASE64" + WinGemPacket.AM + "")
            processed, hostdata, _ = x.addpacket(packet)
            self.assertTrue(processed)
        packet = WinGemPacket("WFT" + WinGemPacket.AM + "READ" + WinGemPacket.AM +
                              "HOLD" + WinGemPacket.AM + "BASE64" + WinGemPacket.AM + "")
        processed, hostdata, _ = x.addpacket(packet)
        # Close
        packet = WinGemPacket(
            "WFT" + WinGemPacket.AM + "CLOSE" + WinGemPacket.AM + "HOLD")
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(WinGemPacket(hostdata).extract(1, 1), "1")

    def testlargefile(self):
        ''' Test writing a large file'''
        packet = WinGemPacket("WFT" + WinGemPacket.AM + "OPEN" + WinGemPacket.AM + "HOLD" +
                              WinGemPacket.AM + "WRITE" + WinGemPacket.AM +
                              "bigfile.txt")
        x = FileTransfer("abc")
        processed, hostdata, _ = x.addpacket(packet)
        zeedata = base64.b64encode(("X" * (2 ^ 16)).encode()).decode("ISO-8859-1")
        self.assertTrue(processed)
        packet = WinGemPacket("WFT" + WinGemPacket.AM + "WRITE" +
                              WinGemPacket.AM + "HOLD" + WinGemPacket.AM + zeedata)
        packet = WinGemPacket("WFT" + WinGemPacket.AM + "WRITE" +
                              WinGemPacket.AM + "HOLD" + WinGemPacket.AM + zeedata)
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        # Close
        packet = WinGemPacket(
            "WFT" + WinGemPacket.AM + "CLOSE" + WinGemPacket.AM + "HOLD")
        processed, hostdata, _ = x.addpacket(packet)
        self.assertTrue(processed)
        self.assertEqual(WinGemPacket(hostdata).extract(1, 1), "1")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testwrite']
    # logging.basicConfig(level=logging.INFO)
    unittest.main()
