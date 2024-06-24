'''
Created on Jan 16, 2017

@author: holthjef
'''
import inspect
import os
import unittest
from connector.logfilereader import LogFileReader
from connector.wingempacket import WinGemPacket
from connector import resource
from connector.configuration import CONFIG
from components.commandbar import CommandBar, CommandBarBand, CommandBarTool  # @UnusedImport


class TestCommandBar(unittest.TestCase):
    ''' Testing CommandBar (WDT) Objects '''

    def __init__(self, *args, **kwargs):
        ''' Constructor '''
        super(TestCommandBar, self).__init__(*args, **kwargs)
        self.commandbar = CommandBar()
        self.bandcount = 7
        self.testmenuname = "bndMenuTest"
        self.testtoolbarname = "bndToolbarTest"

    def testlogfile(self):
        ''' Run testcommandbar.txt log file '''
        # script filename (usually with path)
        logfilepath = os.path.dirname(inspect.getfile(inspect.currentframe()))
        testlog = LogFileReader(logfilepath + "/logs/testcommandbar.txt")
        cbobject = CommandBar()
        while True:
            packetdata = testlog.nextpacket(includestxetx=False)
            if packetdata:
                packet = WinGemPacket(packetdata)
                cbobject.addpacket(packet)
#                 if cbobject.iscomplete():
#                     break
            else:
                break
        testlog.close()
        #=======================================================================
        # print("*********" + chr(13) + chr(10))
        # print([x for x in cbobject.bands])
        # print(chr(13) + chr(10))
        #=======================================================================
        self.assertEqual(len(cbobject.bands), 8)
        self.assertEqual(len(cbobject.bands["bndMenuStandard"].tools), 4)
        self.assertEqual(len(cbobject.bands["bndPopupSession"].tools), 2)
        if CONFIG['PRODUCT'] == "AXIS":
            self.assertEqual(len(cbobject.bands["bndPopup&Commands"].tools), 15)
            self.assertEqual(len(cbobject.bands["bndPopupWindow"].tools), 2)
        self.assertEqual(len(cbobject.bands["bndPopupView"].tools), 1)
        self.assertEqual(len(cbobject.bands["bndPopupHelp"].tools), 6)
        self.assertEqual(len(cbobject.bands["bndToolbarStandard"].tools), 9)
        self.assertEqual(len(cbobject.bands["bndToolbarDebug"].tools), 4)

    def checkdefault(self):
        ''' Check results of default setup '''
        self.assertEqual(self.commandbar.getid(), "COMMANDBAR")
        # print([x for x in self.commandbar.bands])
        #=======================================================================
        # Seven default bands:
        #     ['bndMenuStandard',
        #      'bndPopupSession',
        #      'bndPopupHelp',
        #      'bndToolbarStandard',
        #      'bndPopupWindow',
        #      'bndToolbarDebug',
        #      'bndPopupView']
        #=======================================================================
        #self.assertEqual(len(self.commandbar.bands), self.bandcount)

    def addmenuitem(self):
        ''' Build TestTool on TestToolmenu '''
        toolmenuname = "&TestToolmenu"
        toolname = "&TestTool"
        optionslist = list("M")  # 1, Type
        optionslist.append("".join((chr(27), "<img=uptool.svg >")))  # 2, Image
        optionslist.append("E")  # 3, Send Type
        optionslist.append("F4")  # 4, Send Text
        optionslist.append("Test tool")  # 5, Help
        optionslist.append("Y")  # 6, Enabled (Y/N)
        optionslist.append("")  # 7, Unused
        optionslist.append("")  # 8, Unused
        optionslist.append("TestTool")  # 9, Name
        # 10, Menupath
        optionslist.append("/".join((toolmenuname, toolname)))
        optionslist.append("")  # 11, Toolbar
        optionslist.append("CTRL+T")  # 12, accelerator key
        optionslist.append("")  # 13, Unused
        optionslist.append("")  # 14, Unused
        optionslist.append("")  # 15, Unused
        optionslist.append("")  # 16, toolpos
        optionslist.append("")  # 17, menupos
        optionslist.append("")  # 18, begin group
        optionsstring = WinGemPacket.VM.join(optionslist)
        buttonpacket = WinGemPacket.AM.join(("WDT", "", optionsstring))
        self.commandbar.addpacket(WinGemPacket(buttonpacket))
        # Check for new popup menu
        self.bandcount = self.bandcount + 1
        newmenu = self.commandbar.bands["bndPopup" + toolmenuname]
        self.assertEqual(len(self.commandbar.bands), self.bandcount)
        self.assertEqual(newmenu.name, "bndPopup" + toolmenuname)
        self.assertEqual(newmenu.bandtype, CommandBarBand.BANDTYPEPOPUP)
        self.assertEqual(newmenu.getid(),
                         "COMMANDBAR_BAND_" + "bndPopup" + resource.removehotkey(toolmenuname)[0])
        # Check for new tool
        self.assertEqual(len(newmenu.tools), 1)
        newtool = newmenu.tools[0]
        #=======================================================================
        # print(newtool.type)
        # print(newtool.image)
        # print(newtool.sendtype)
        # print(newtool.sendtext)
        # print(newtool.help)
        # print(newtool.enabled)
        # print(newtool.name)
        # print(newtool.menupath)
        # print(newtool.toolbar)
        # print(newtool.toolpos)
        # print(newtool.menupos)
        # print(newtool.options)
        # print(newtool.tag)
        # print(newtool.filename)
        # print(newtool.subband)
        # print(newtool.checked)
        #=======================================================================
        self.assertEqual(newtool.type, "M")
        self.assertEqual(newtool.sendtype, "E")
        self.assertEqual(newtool.sendtext, "F4")
        self.assertEqual(newtool.help, "Test tool")
        self.assertEqual(newtool.enabled, True)
        self.assertEqual(newtool.name, resource.removehotkey("att" + toolname)[0])
        self.assertEqual(newtool.menupath, "/".join((toolmenuname, toolname)))
        self.assertEqual(newtool.toolbar, "")
        self.assertEqual(newtool.toolpos, "")
        self.assertEqual(newtool.menupos, "")
        self.assertEqual(newtool.options["img"], "uptool.svg")
        self.assertEqual(newtool.tag, resource.removehotkey(toolname)[0])
        self.assertNotEqual(newtool.filename, "")
        self.assertEqual(newtool.subband, "")
        self.assertEqual(newtool.checked, False)
        self.assertEqual(newtool.getid(), "COMMANDBAR_TOOL_" +
                         resource.removehotkey("att" + toolname)[0])
        # return toolmenuname, toolname, optionslist, optionsstring, buttonpacket, newmenu, newtool

    def addtoolbaritem(self):
        ''' Build TestIcon on StandardToolbar '''

        oldtoolbaritemcount = len(self.commandbar.bands["bndToolbarStandard"].tools)
        toolname = "&TestIcon"
        optionslist = list("T")  # 1, Type
        optionslist.append("".join((chr(27), "<img=uptool.svg >")))  # 2, Image
        optionslist.append("E")  # 3, Send Type
        optionslist.append("F4")  # 4, Send Text
        optionslist.append("Test icon")  # 5, Help
        optionslist.append("Y")  # 6, Enabled (Y/N)
        optionslist.append("")  # 7, Unused
        optionslist.append("")  # 8, Unused
        optionslist.append("TestIcon")  # 9, Name
        # 10, Menupath
        optionslist.append("")
        optionslist.append("WINGEM")  # 11, Toolbar
        optionslist.append("CTRL+T")  # 12, accelerator key
        optionslist.append("")  # 13, Unused
        optionslist.append("")  # 14, Unused
        optionslist.append("")  # 15, Unused
        optionslist.append("")  # 16, toolpos
        optionslist.append("")  # 17, menupos
        optionslist.append("")  # 18, begin group
        optionsstring = WinGemPacket.VM.join(optionslist)
        buttonpacket = WinGemPacket.AM.join(("WDT", "", optionsstring))
        self.commandbar.addpacket(WinGemPacket(buttonpacket))
        # Check that no new menus/bands
        self.assertEqual(len(self.commandbar.bands), self.bandcount)
        newmenu = self.commandbar.bands["bndToolbarStandard"]
        self.assertEqual(newmenu.name, "bndToolbarStandard")
        self.assertEqual(newmenu.bandtype, CommandBarBand.BANDTYPETOOLBAR)
        # Check for new tool
        self.assertEqual(len(newmenu.tools), oldtoolbaritemcount + 1)
        newtool = {tool.name: tool for tool in newmenu.tools}["attTestIcon"]
        #=======================================================================
        # print(newtool.type)
        # print(newtool.image)
        # print(newtool.sendtype)
        # print(newtool.sendtext)
        # print(newtool.help)
        # print(newtool.enabled)
        # print(newtool.name)
        # print(newtool.menupath)
        # print(newtool.toolbar)
        # print(newtool.toolpos)
        # print(newtool.menupos)
        # print(newtool.options)
        # print(newtool.tag)
        # print(newtool.filename)
        # print(newtool.subband)
        # print(newtool.checked)
        #=======================================================================
        self.assertEqual(newtool.type, "T")
        self.assertEqual(newtool.sendtype, "E")
        self.assertEqual(newtool.sendtext, "F4")
        self.assertEqual(newtool.help, "Test icon")
        self.assertEqual(newtool.enabled, True)
        self.assertEqual(newtool.name, resource.removehotkey("att" + toolname)[0])
        self.assertEqual(newtool.menupath, "")
        self.assertEqual(newtool.toolbar, "bndWINGEM")
        self.assertEqual(newtool.toolpos, "")
        self.assertEqual(newtool.menupos, "")
        self.assertEqual(newtool.options["img"], "uptool.svg")
        self.assertEqual(newtool.tag, resource.removehotkey(toolname)[0])
        self.assertNotEqual(newtool.filename, "")
        self.assertEqual(newtool.subband, "")
        self.assertEqual(newtool.checked, False)
        # return toolmenuname, toolname, optionslist, optionsstring, buttonpacket, newmenu, newtool

    def redefinemenuitem(self):
        ''' Redefine TestTool on TestToolmenu '''
        toolmenuname = "&TestToolmenu"
        toolname = "&TestTool"
        optionslist = list("M")  # 1, Type
        optionslist.append("".join((chr(27), "<img=uptool.svg >")))  # 2, Image
        optionslist.append("E")  # 3, Send Type
        optionslist.append("F5")  # 4, Send Text
        optionslist.append("Test tool2")  # 5, Help
        optionslist.append("Y")  # 6, Enabled (Y/N)
        optionslist.append("")  # 7, Unused
        optionslist.append("")  # 8, Unused
        optionslist.append("TestTool")  # 9, Name
        # 10, Menupath
        optionslist.append("/".join((toolmenuname, toolname)))
        optionslist.append("")  # 11, Toolbar
        optionslist.append("CTRL+U")  # 12, accelerator key
        optionslist.append("")  # 13, Unused
        optionslist.append("")  # 14, Unused
        optionslist.append("")  # 15, Unused
        optionslist.append("")  # 16, toolpos
        optionslist.append("")  # 17, menupos
        optionslist.append("")  # 18, begin group
        optionsstring = WinGemPacket.VM.join(optionslist)
        buttonpacket = WinGemPacket.AM.join(("WDT", "", optionsstring))
        self.commandbar.addpacket(WinGemPacket(buttonpacket))

        # Check for same number of popup menus
        self.assertEqual(len(self.commandbar.bands), self.bandcount)

        newmenu = self.commandbar.bands["bndPopup" + toolmenuname]
        self.assertEqual(newmenu.name, "bndPopup" + toolmenuname)
        self.assertEqual(newmenu.bandtype, CommandBarBand.BANDTYPEPOPUP)
        self.assertEqual(newmenu.getid(),
                         "COMMANDBAR_BAND_" + "bndPopup" + resource.removehotkey(toolmenuname)[0])

        # Check for updated tool
        self.assertEqual(len(newmenu.tools), 1)  # Still only one
        newtool = newmenu.tools[0]
        #=======================================================================
        # print(newtool.type)
        # print(newtool.image)
        # print(newtool.sendtype)
        # print(newtool.sendtext)
        # print(newtool.help)
        # print(newtool.enabled)
        # print(newtool.name)
        # print(newtool.menupath)
        # print(newtool.toolbar)
        # print(newtool.toolpos)
        # print(newtool.menupos)
        # print(newtool.options)
        # print(newtool.tag)
        # print(newtool.filename)
        # print(newtool.subband)
        # print(newtool.checked)
        #=======================================================================
        self.assertEqual(newtool.type, "M")
        self.assertEqual(newtool.sendtype, "E")
        self.assertEqual(newtool.sendtext, "F5")
        self.assertEqual(newtool.help, "Test tool2")
        self.assertEqual(newtool.enabled, True)
        self.assertEqual(newtool.name, resource.removehotkey("att" + toolname)[0])
        self.assertEqual(newtool.menupath, "/".join((toolmenuname, toolname)))
        self.assertEqual(newtool.toolbar, "")
        self.assertEqual(newtool.toolpos, "")
        self.assertEqual(newtool.menupos, "")
        self.assertEqual(newtool.options["img"], "uptool.svg")
        self.assertEqual(newtool.tag, resource.removehotkey(toolname)[0])
        self.assertNotEqual(newtool.filename, "")
        self.assertEqual(newtool.subband, "")
        self.assertEqual(newtool.checked, False)
        self.assertEqual(newtool.getid(), "COMMANDBAR_TOOL_" +
                         resource.removehotkey("att" + toolname)[0])

    def insertmenuitemmiddle(self):
        ''' Insert TestTool on TestToolmenu '''
        toolmenuname = "&Window"
        toolname = "&TestToolInsert"
        optionslist = list("M")  # 1, Type
        optionslist.append("")  # 2, Image
        optionslist.append("E")  # 3, Send Type
        optionslist.append("F5")  # 4, Send Text
        optionslist.append("Test tool insert")  # 5, Help
        optionslist.append("Y")  # 6, Enabled (Y/N)
        optionslist.append("")  # 7, Unused
        optionslist.append("")  # 8, Unused
        optionslist.append("")  # 9, Name (Will extract from menpath)
        # 10, Menupath
        optionslist.append("/".join((toolmenuname, toolname)))
        optionslist.append("")  # 11, Toolbar
        optionslist.append("CTRL+U")  # 12, accelerator key
        optionslist.append("")  # 13, Unused
        optionslist.append("")  # 14, Unused
        optionslist.append("")  # 15, Unused
        optionslist.append("")  # 16, toolpos
        optionslist.append("1")  # 17, menupos
        optionslist.append("")  # 18, begin group
        optionsstring = WinGemPacket.VM.join(optionslist)
        buttonpacket = WinGemPacket.AM.join(("WDT", "", optionsstring))
        self.commandbar.addpacket(WinGemPacket(buttonpacket))

        # Check for same number of popup menus
        self.assertEqual(len(self.commandbar.bands), self.bandcount)

        newmenu = self.commandbar.bands[resource.removehotkey("bndPopup" + toolmenuname)[0]]

        # Check for tool position (should be after Up and before View)
        self.assertEqual(newmenu.tools[1].name, resource.removehotkey("att" + toolname)[0])

        # Insertion Points shouldn't have changed
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsethead, 1)
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsettail, 1)

    def insertmenuitemfront(self):
        ''' Insert TestTool on TestToolmenu at absolute beginning '''
        toolmenuname = "&Window"
        toolname = "&TestToolInsertFront"
        optionslist = list("M")  # 1, Type
        optionslist.append("".join((chr(27), "<img=uptool.svg >")))  # 2, Image
        optionslist.append("E")  # 3, Send Type
        optionslist.append("F5")  # 4, Send Text
        optionslist.append("Test tool insert front")  # 5, Help
        optionslist.append("Y")  # 6, Enabled (Y/N)
        optionslist.append("")  # 7, Unused
        optionslist.append("")  # 8, Unused
        optionslist.append("")  # 9, Name (Will extract from icon path)
        # 10, Menupath
        optionslist.append("/".join((toolmenuname, toolname)))
        optionslist.append("")  # 11, Toolbar
        optionslist.append("CTRL+U")  # 12, accelerator key
        optionslist.append("")  # 13, Unused
        optionslist.append("")  # 14, Unused
        optionslist.append("")  # 15, Unused
        optionslist.append("")  # 16, toolpos
        optionslist.append("A1")  # 17, menupos
        optionslist.append("")  # 18, begin group
        optionsstring = WinGemPacket.VM.join(optionslist)
        buttonpacket = WinGemPacket.AM.join(("WDT", "", optionsstring))
        self.commandbar.addpacket(WinGemPacket(buttonpacket))

        # Check for same number of popup menus
        self.assertEqual(len(self.commandbar.bands), self.bandcount)

        newmenu = self.commandbar.bands[resource.removehotkey("bndPopup" + toolmenuname)[0]]

        # Check for tool position (should be first)
        self.assertEqual(newmenu.tools[0].name, resource.removehotkey("attuptool.svg")[0])

        # Head Insertion Points should have increased
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsethead, 2)
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsettail, 1)

    def insertmenuitemlast(self):
        ''' Insert TestTool on TestToolmenu at absolute > last '''
        toolmenuname = "&Window"
        toolname = "&TestToolInsertLast"
        optionslist = list("M")  # 1, Type
        optionslist.append("".join((chr(27), "<img=uptool.svg >")))  # 2, Image
        optionslist.append("E")  # 3, Send Type
        optionslist.append("F5")  # 4, Send Text
        optionslist.append("Test tool insert last")  # 5, Help
        optionslist.append("Y")  # 6, Enabled (Y/N)
        optionslist.append("")  # 7, Unused
        optionslist.append("")  # 8, Unused
        optionslist.append("TestToolInsertLast")  # 9, Name
        # 10, Menupath
        optionslist.append("/".join((toolmenuname, toolname)))
        optionslist.append("")  # 11, Toolbar
        optionslist.append("CTRL+U")  # 12, accelerator key
        optionslist.append("")  # 13, Unused
        optionslist.append("")  # 14, Unused
        optionslist.append("")  # 15, Unused
        optionslist.append("")  # 16, toolpos
        optionslist.append("A50")  # 17, menupos
        optionslist.append("")  # 18, begin group
        optionsstring = WinGemPacket.VM.join(optionslist)
        buttonpacket = WinGemPacket.AM.join(("WDT", "", optionsstring))
        self.commandbar.addpacket(WinGemPacket(buttonpacket))

        # Check for same number of popup menus
        self.assertEqual(len(self.commandbar.bands), self.bandcount)

        newmenu = self.commandbar.bands[resource.removehotkey("bndPopup" + toolmenuname)[0]]

        # Check for tool position (should be fifth)
        self.assertEqual(len(newmenu.tools), 5)
        self.assertEqual(newmenu.tools[4].name, resource.removehotkey("attTestToolInsertLast")[0])

        # Tail Insertion Points should have increased
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsethead, 2)
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsettail, 2)

    def insertmenuitemzero(self):
        ''' Insert TestTool on TestToolmenu at absolute = 0 (packet is 1-based) '''
        toolmenuname = "&Window"
        toolname = "&TestToolInsertZero"
        optionslist = list("M")  # 1, Type
        optionslist.append("".join((chr(27), "<img=uptool.svg >")))  # 2, Image
        optionslist.append("E")  # 3, Send Type
        optionslist.append("F5")  # 4, Send Text
        optionslist.append("Test tool insert zero")  # 5, Help
        optionslist.append("Y")  # 6, Enabled (Y/N)
        optionslist.append("")  # 7, Unused
        optionslist.append("")  # 8, Unused
        optionslist.append("TestToolInsertZero")  # 9, Name
        # 10, Menupath
        optionslist.append("/".join((toolmenuname, toolname)))
        optionslist.append("")  # 11, Toolbar
        optionslist.append("CTRL+U")  # 12, accelerator key
        optionslist.append("")  # 13, Unused
        optionslist.append("")  # 14, Unused
        optionslist.append("")  # 15, Unused
        optionslist.append("")  # 16, toolpos
        optionslist.append("A0")  # 17, menupos
        optionslist.append("")  # 18, begin group
        optionsstring = WinGemPacket.VM.join(optionslist)
        buttonpacket = WinGemPacket.AM.join(("WDT", "", optionsstring))
        self.commandbar.addpacket(WinGemPacket(buttonpacket))

        # Check for same number of popup menus
        self.assertEqual(len(self.commandbar.bands), self.bandcount)

        newmenu = self.commandbar.bands[resource.removehotkey("bndPopup" + toolmenuname)[0]]

        # Check for tool position (should be first of 6)
        self.assertEqual(len(newmenu.tools), 6)
        self.assertEqual(newmenu.tools[0].name, resource.removehotkey("attTestToolInsertZero")[0])

        # Head Insertion Points should have increased
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsethead, 3)
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsettail, 2)

    def badcbpacket(self):
        ''' Test bad WDT packet at CommandBar level '''
        success = self.commandbar.addpacket(WinGemPacket("WDT"))[0]
        self.assertEqual(success, True)

    def removetool(self, toolname: str):
        ''' Common logic for removing tool '''
        optionslist = list("")  # if #1 is empty, need this to get the vm
        optionslist.append("")  # 1, Type
        optionslist.append("")  # 2, Image
        optionslist.append("")  # 3, Send Type
        optionslist.append("")  # 4, Send Text
        optionslist.append("")  # 5, Help
        optionslist.append("X")  # 6, Enabled (Y/N)
        optionslist.append("")  # 7, Unused
        optionslist.append("")  # 8, Unused
        optionslist.append(toolname)  # 9, Name (Will extract from menpath)
        # 10, Menupath
        optionslist.append("")
        optionslist.append("")  # 11, Toolbar
        optionslist.append("")  # 12, accelerator key
        optionslist.append("")  # 13, Unused
        optionslist.append("")  # 14, Unused
        optionslist.append("")  # 15, Unused
        optionslist.append("")  # 16, toolpos
        optionslist.append("")  # 17, menupos
        optionslist.append("")  # 18, begin group
        optionsstring = WinGemPacket.VM.join(optionslist)
        buttonpacket = WinGemPacket.AM.join(("WCT", optionsstring))
        self.commandbar.addpacket(WinGemPacket(buttonpacket))

    def removemenuitemmiddle(self):
        ''' Remove item from middle (not near insertion points) '''
        toolmenuname = "&Window"
        toolname = "TestToolInsert"

        self.removetool(toolname)

        newmenu = self.commandbar.bands[resource.removehotkey("bndPopup" + toolmenuname)[0]]

        # Tool should no longer exist in collection
        self.assertEqual([name for name in self.commandbar._tools  # pylint:disable=protected-access
                          if name == "att" + toolname], [])

        # Tool should no longer exist in band
        self.assertEqual([tool.name for tool in newmenu.tools
                          if tool.name == "att" + toolname], [])

        # Insertion Points shouldn't have changed
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsethead, 3)
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsettail, 2)

    def removemenuitemfront(self):
        ''' Remove item from front (inside head insertion point) '''
        toolmenuname = "&Window"
        toolname = "uptool.svg"

        self.removetool(toolname)

        newmenu = self.commandbar.bands[resource.removehotkey("bndPopup" + toolmenuname)[0]]

        # Tool should no longer exist in collection
        self.assertEqual([name for name in self.commandbar._tools  # pylint:disable=protected-access
                          if name == "att" + toolname], [])

        # Tool should no longer exist in band
        self.assertEqual([tool.name for tool in newmenu.tools
                          if tool.name == "att" + toolname], [])

        # Head Insertion Point should have decreased
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsethead, 2)
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsettail, 2)

    def removemenuitemlast(self):
        ''' Remove last item (inside tail insertion point) '''
        toolmenuname = "&Window"
        toolname = "TestToolInsertLast"

        self.removetool(toolname)

        newmenu = self.commandbar.bands[resource.removehotkey("bndPopup" + toolmenuname)[0]]

        # Tool should no longer exist in collection
        self.assertEqual([name for name in self.commandbar._tools  # pylint:disable=protected-access
                          if name == "att" + toolname], [])

        # Tool should no longer exist in band
        self.assertEqual([tool.name for tool in newmenu.tools
                          if tool.name == "att" + toolname], [])

        # Tail Insertion Point should have decreased
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsethead, 2)
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsettail, 1)

    def removemenuitemmiddleagain(self):
        ''' Remove middle item inside head, against tail '''
        toolmenuname = "&Window"
        toolname = "CancelUp"

        self.removetool(toolname)

        newmenu = self.commandbar.bands[resource.removehotkey("bndPopup" + toolmenuname)[0]]

        # Tool should no longer exist in collection
        self.assertEqual([name for name in self.commandbar._tools  # pylint:disable=protected-access
                          if name == "att" + toolname], [])

        # Tool should no longer exist in band
        self.assertEqual([tool.name for tool in newmenu.tools
                          if tool.name == "att" + toolname], [])

        # Insertion Points shouldn't have changed
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsethead, 1)
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsettail, 1)

    def removemenuitemlastagain(self):
        ''' Remove last item inside tail, next to head '''
        toolmenuname = "&Window"
        toolname = "View"

        self.removetool(toolname)

        newmenu = self.commandbar.bands[resource.removehotkey("bndPopup" + toolmenuname)[0]]

        # Tool should no longer exist in collection
        self.assertEqual([name for name in self.commandbar._tools  # pylint:disable=protected-access
                          if name == "att" + toolname], [])

        # Tool should no longer exist in band
        self.assertEqual([tool.name for tool in newmenu.tools
                          if tool.name == "att" + toolname], [])

        # Tail Insertion Point should have decreased
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsethead, 1)
        self.assertEqual(self.commandbar.bands["bndPopupWindow"].offsettail, 0)

    def testcommandbar_main(self):
        ''' Test CommandBar'''

        # Tests being run from single test case method to control execution order
        self.checkdefault()
        self.addmenuitem()
        self.addtoolbaritem()
        self.redefinemenuitem()
        self.insertmenuitemmiddle()
        self.insertmenuitemfront()
        self.insertmenuitemlast()
        self.insertmenuitemzero()
        self.badcbpacket()
        self.removemenuitemmiddle()
        self.removemenuitemfront()
        self.removemenuitemlast()
        self.removemenuitemmiddleagain()
        self.removemenuitemlastagain()

        # Can't currently think of a way to break CommandBarTool.addpacket


if __name__ == "__main__":
    unittest.main()
