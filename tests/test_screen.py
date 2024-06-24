'''
Created on Oct 19, 2016

@author: bouchcla
'''
import inspect
import os
import unittest
from components.screen import Screen
from connector.logfilereader import LogFileReader
from connector.wingempacket import WinGemPacket


class ScreenTest(unittest.TestCase):
    ''' Testing Screens '''

    def testscreen(self):
        ''' Screen test '''
        # script filename (usually with path)
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/testscreen.txt")
        screenobject = Screen()
        while True:
            packetdata = testlog.nextpacket(includestxetx=False)
            if packetdata:
                packet = WinGemPacket(packetdata)
                screenobject.addpacket(packet)
                if screenobject.iscomplete():
                    break
            else:
                break
        testlog.close()
        self.assertEqual(len(screenobject.prompts), 21)
        self.assertEqual(len(screenobject.grids), 2)
        self.assertEqual(len(screenobject.grids[0].prompts), 1)
        # valid tests
        self.assertEqual(screenobject.screenid, 502)
        self.assertTrue(screenobject.iscomplete())

    def testscreen2(self):
        ''' test 2 screens in a log '''
        # test 2 screens in log
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/test2screens.txt")
        screens = []
        screencnt = 0
        while True:
            packetdata = testlog.nextpacket(includestxetx=False)
            if packetdata:
                packet = WinGemPacket(packetdata)
                if packet.extract(1) == "WS":
                    screencnt += 1
                    screens.append(Screen())
                if len(screens) > 0:
                    screens[screencnt - 1].addpacket(packet)
            else:
                break
        testlog.close()
        # valid tests for 2nd screen
        self.assertEqual(len(screens[1].prompts), 11)
        self.assertEqual(screens[1].screenid, 502)
        self.assertTrue(screens[1].iscomplete())

    def testscreen_text(self):
        ''' Test TEXT objects '''
        # script filename (usually with path)
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/testscreen_text.txt")
        screenobject = Screen()
        while True:
            packetdata = testlog.nextpacket(includestxetx=False)
            if packetdata:
                packet = WinGemPacket(packetdata)
                screenobject.addpacket(packet)
                if screenobject.iscomplete():
                    break
            else:
                break
        testlog.close()

        # 5 text objects (one redefines another, but gets added as new)
        self.assertEqual(len(screenobject.texts), 5)

    def testscreen_text_headingredefine(self):
        ''' Test TEXT objects with a redefined heading (AWD-270) '''
        # script filename (usually with path)
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/headingredefine.txt")
        screenobject = Screen()
        while True:
            packetdata = testlog.nextpacket(includestxetx=False)
            if packetdata:
                packet = WinGemPacket(packetdata)
                screenobject.addpacket(packet)
            else:
                break
        testlog.close()

        # 4 text objects (5 are processed, but two are headings: There can be only one.)
        self.assertEqual(len(screenobject.texts), 4)
        self.assertEqual(len([text for text in screenobject.texts if text.heading]), 1)

    def testscreen_button(self):
        ''' Test BUTTON objects '''
        # script filename (usually with path)
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/testscreen_button.txt")
        screenobject = Screen()
        while True:
            packetdata = testlog.nextpacket(includestxetx=False)
            if packetdata:
                packet = WinGemPacket(packetdata)
                screenobject.addpacket(packet)
                if screenobject.iscomplete():
                    break
            else:
                break
        testlog.close()

        self.assertEqual(len(screenobject.buttons), 7)

    def testscreen_button2(self):
        ''' Test BUTTON objects #2 '''
        # script filename (usually with path)
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/testscreen_button2.txt")
        screenobject = Screen()
        while True:
            packetdata = testlog.nextpacket(includestxetx=False)
            if packetdata:
                packet = WinGemPacket(packetdata)
                screenobject.addpacket(packet)
                if screenobject.iscomplete():
                    break
            else:
                break
        testlog.close()

        self.assertEqual(len(screenobject.buttons), 19)

    def testscreen_button_horizontal(self):
        ''' Test BUTTON objects #2 '''
        # script filename (usually with path)
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/testscreen_button_horizontal.txt")
        screenobject = Screen()
        while True:
            packetdata = testlog.nextpacket(includestxetx=False)
            if packetdata:
                packet = WinGemPacket(packetdata)
                screenobject.addpacket(packet)
                if screenobject.iscomplete():
                    break
            else:
                break
        testlog.close()

        self.assertEqual(len(screenobject.buttons), 8)

    def testscreen_button_disable(self):
        ''' Test BUTTON object disabling '''
        # script filename (usually with path)
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/buttons-clientscreen.txt")
        screenobject = Screen()
        while True:
            packetdata = testlog.nextpacket(includestxetx=False)
            if packetdata:
                packet = WinGemPacket(packetdata)
                screenobject.addpacket(packet)
            else:
                break
        testlog.close()

        # Total button count
        self.assertEqual(len(screenobject.buttons), 17)

        # Total enabled button count
        self.assertEqual(len([button for button in screenobject.buttons if button.enabled]), 3)

    def testscreen_button_delete(self):
        ''' Test BUTTON object removing '''
        # script filename (usually with path)
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/removebuttonsafter.txt")
        screenobject = Screen()
        checkcomplete = True
        while True:
            packetdata = testlog.nextpacket(includestxetx=False)
            if packetdata:
                packet = WinGemPacket(packetdata)
                screenobject.addpacket(packet)
                if checkcomplete and screenobject.iscomplete():
                    # Total button count is 3 at completion
                    self.assertEqual(len(screenobject.buttons), 3)
                    checkcomplete = False
            else:
                break
        testlog.close()

        # Total button count is 1 after deletions happen
        self.assertEqual(len(screenobject.buttons), 1)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testScreen']
    unittest.main()
