'''
Created on Nov 28, 2016

@author: rosenada
'''
import inspect
import os
import unittest
from components.menu import MenuObject
from connector.logfilereader import LogFileReader
from connector.wingempacket import WinGemPacket

class MenuTest(unittest.TestCase):
    ''' UnitTest class for building menus'''

    def createmenu(self, menulog):
        ''' creates a menu off of a log file based on passed in text '''
        # script filename (usually with path)
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/" + menulog)
        menuobj = MenuObject()
        while True:
            packetdata = testlog.nextpacket(includestxetx=False)
            if packetdata:
                packet = WinGemPacket(packetdata)
                menuobj.addpacket(packet)
                if menuobj.iscomplete():
                    break
            else:
                break
        testlog.close()
        return menuobj

    def testcreate4(self):
        ''' tests creating a menu with 4 sections '''
        menuobj = self.createmenu("menu4.txt")
        self.assertTrue(menuobj.iscomplete())

    def testcreate1(self):
        ''' tests creating a menu with 1 section '''
        menuobj = self.createmenu("menu1.txt")
        self.assertTrue(menuobj.iscomplete())

    def testcreate2(self):
        ''' tests creating a menu with 2 sections '''
        menuobj = self.createmenu("menu2.txt")
        self.assertTrue(menuobj.iscomplete())

    def testcreate3(self):
        ''' tests creating a menu with 3 sections '''
        menuobj = self.createmenu("menu3.txt")
        self.assertTrue(menuobj.iscomplete())

    def testcreatesx(self):
        ''' tests creating a menu with 1 section '''
        menuobj = self.createmenu("sxmenu.txt")
        self.assertTrue(menuobj.iscomplete())

    def testcreategc(self):
        ''' tests creating a menu with 1 section '''
        menuobj = self.createmenu("gcmenu.txt")
        self.assertTrue(menuobj.iscomplete())

    def testbadcreate(self):
        ''' tests creating a bad/incomplete menu packet '''
        menuobj = self.createmenu("garbagemenu.txt")
        self.assertFalse(menuobj.iscomplete())

    def testbackupicons(self):
        '''
        tests it defaulting if custom icon isnt found, based on
        the packet containing extra information if menu item
        has child menu or normal screen
        '''
        menuobj = self.createmenu("menubackupdefault.txt")
        self.assertTrue(menuobj.iscomplete())


    def testparsesections(self):
        ''' creates a menu and verifies sections and count within section '''
        menuobj = self.createmenu("menu4.txt")
        self.assertTrue(menuobj.sections["Client Services"])
        self.assertEqual(len(menuobj.sections["Client Services"].menuitems), 9)
        self.assertTrue(menuobj.sections["Corporate Operations"])
        self.assertEqual(len(menuobj.sections["Corporate Operations"].menuitems), 8)
        self.assertTrue(menuobj.sections["AXIS Utilities"])
        self.assertEqual(len(menuobj.sections["AXIS Utilities"].menuitems), 3)
        self.assertTrue(menuobj.sections["Marketing and Reporting"])
        self.assertEqual(len(menuobj.sections["Marketing and Reporting"].menuitems), 8)
    
    def testemptymenu(self):
        ''' tests creating a menu that's a real menu but has no items in it'''
        menuobj = self.createmenu("emptymenu.txt")
        self.assertEqual(menuobj.menuitemtitles,[])

    def testgetid(self):
        ''' creates a menu and tests its hardcoded id to pass code coverage '''
        menuobj = self.createmenu("menu4.txt")
        self.assertEqual((menuobj.executelevel * 1000) + menuobj.calllevel,
                          menuobj.getid())

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
