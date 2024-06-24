'''
Created on Jan 26, 2017

@author: rosenada
'''
import inspect
import os
import unittest
from components.command import Command
from connector.logfilereader import LogFileReader
from connector.wingempacket import WinGemPacket
from connector.configuration import CONFIG


class TestCommands(unittest.TestCase):
    ''' UnitTest class for building commands'''

    def createcommand(self, cmdlog):
        ''' creates a command object based on passed in logs' text'''
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/" + cmdlog)
        command = Command()
        while True:
            packetdata = testlog.nextpacket(includestxetx=False)
            if packetdata:
                packet = WinGemPacket(packetdata)
                command.addpacket(packet)
                if command.iscomplete():
                    break
            else:
                break
        testlog.close()
        return command

    def testmail(self):
        ''' Tests mail command parsing '''
        mailcmd = self.createcommand("mail1.txt").getcommand()
        self.assertEqual(mailcmd['unreadnum'], "1")
        self.assertEqual(mailcmd['iconname'], "wdres/envelope.svg")
        self.assertTrue(mailcmd['visible'])
        mailcmd = self.createcommand("mail2.txt").getcommand()
        self.assertEqual(mailcmd['unreadnum'], "100")
        self.assertEqual(mailcmd['iconname'], "wdres/users.svg")
        self.assertTrue(mailcmd['visible'])
        mailcmd = self.createcommand("mail3.txt").getcommand()
        self.assertEqual(mailcmd['unreadnum'], "50")
        self.assertEqual(mailcmd['iconname'], "wdres/envelope.svg")
        self.assertEqual(mailcmd['totalnum'], "100")
        self.assertTrue(mailcmd['visible'])
        mailcmd = self.createcommand("mail4.txt").getcommand()
        self.assertEqual(mailcmd['unreadnum'], "99")
        self.assertEqual(mailcmd['iconname'], "wdres/envelope.svg")
        self.assertEqual(mailcmd['message'], "DAR CUSTOM MSG")
        self.assertTrue(mailcmd['visible'])
        mailcmd = self.createcommand("mail5.txt").getcommand()
        self.assertEqual(mailcmd['iconname'], "wdres/envelope.svg")
        self.assertEqual(mailcmd['message'], "FLASH DEFAULT ICON")
        self.assertTrue(mailcmd['flash'])
        self.assertTrue(mailcmd['visible'])
        mailcmd = self.createcommand("mail6.txt").getcommand()
        self.assertEqual(mailcmd['iconname'], "wdres/users.svg")
        self.assertEqual(mailcmd['message'], "FLASH CUSTOM ICON")
        self.assertTrue(mailcmd['flash'])
        self.assertTrue(mailcmd['visible'])
        mailcmd = self.createcommand("mailhide.txt").getcommand()
        self.assertFalse(mailcmd['visible'])

    def teststatusinfo(self):
        ''' tests creation of status info about port and user/account '''
        statuscmd = self.createcommand("statusbar.txt").getcommand()
        self.assertEqual(statuscmd['target'], ["#userinfo", "#portinfo"])
        if CONFIG["PRODUCT"] == "AXIS":
            self.assertEqual(statuscmd['value'],
                             ["DAR on CAA.DEV",
                              "Line: 822 on cmwls-rhaxis/dev/pts/41"])
        elif CONFIG["PRODUCT"] == "GoldCare":
            self.assertEqual(statuscmd['value'],
                             ["DAR on CAA.DEV",
                              "Port: 822 on cmwls-rhaxis/dev/pts/41"])
        # flip config to GC to test it getting the other string resource
        CONFIG["PRODUCT"] = "GoldCare"
        statuscmd = self.createcommand("statusbar.txt").getcommand()
        if CONFIG["PRODUCT"] == "AXIS":
            self.assertEqual(statuscmd['value'],
                             ["DAR on CAA.DEV",
                              "Line: 822 on cmwls-rhaxis/dev/pts/41"])
        elif CONFIG["PRODUCT"] == "GoldCare":
            self.assertEqual(statuscmd['value'],
                             ["DAR on CAA.DEV",
                              "Port: 822 on cmwls-rhaxis/dev/pts/41"])
        # default config back to AXIS
        CONFIG["PRODUCT"] = "AXIS"

    def testmessages(self):
        ''' Tests creation of various message types '''
        messagecmd = self.createcommand("testflash.txt").getcommand()
        self.assertEqual(messagecmd['msg'], "TEST MSG")
        messagecmd = self.createcommand("testflashposition.txt").getcommand()
        self.assertEqual(messagecmd['msg'], "POSITION MSG")
        self.assertEqual(messagecmd['xpos'], 60 * 1.75 * 0.4)
        self.assertEqual(messagecmd['ypos'], 10 * 1.75)
        messagecmd = self.createcommand("testflashnoposition.txt").getcommand()
        self.assertEqual(messagecmd['msg'], "POSITION MSG")
        self.assertFalse('xpos' in messagecmd)
        self.assertFalse("ypos" in messagecmd)
        messagecmd = self.createcommand("testattention.txt").getcommand()
        self.assertEqual(messagecmd['msg'], "BODY MESSAGE")
        self.assertEqual(messagecmd['header'], "heading msg")
        self.assertEqual(messagecmd['image'], "wdres/exclamation.svg")
        messagecmd = self.createcommand("testtellmessage.txt").getcommand()
        self.assertEqual(messagecmd['msg'], "BODY MESSAGE")
        self.assertEqual(messagecmd['header'], "heading msg")
        self.assertEqual(messagecmd['image'], "wdres/info.svg")
        messagecmd = self.createcommand("testexplainmessage.txt").getcommand()
        self.assertEqual(messagecmd['msg'], "BODY MESSAGE")
        self.assertEqual(messagecmd['header'], "heading msg")
        self.assertEqual(messagecmd['image'], "wdres/info.svg")
        messagecmd = self.createcommand("testfatalmessage.txt").getcommand()
        self.assertEqual(messagecmd['msg'], "BODY MESSAGE")
        self.assertEqual(messagecmd['header'], "heading msg")
        self.assertEqual(messagecmd['image'], "wdres/exclamation.svg")
        messagecmd = self.createcommand("testerrormessage.txt").getcommand()
        self.assertEqual(messagecmd['msg'], "BODY MESSAGE")
        self.assertEqual(messagecmd['header'], "heading msg")
        self.assertEqual(messagecmd['image'], "wdres/exclamation.svg")
        messagecmd = self.createcommand("testerroricon.txt").getcommand()
        self.assertEqual(messagecmd['msg'], "SOME MESSAGE")
        self.assertEqual(messagecmd['header'], "HEADING MESSAGE")
        self.assertEqual(messagecmd['image'], "wdres/info.svg")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
