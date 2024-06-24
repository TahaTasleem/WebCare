'''
Created on Nov 21, 2016

@author: holthjef
'''
import unittest
from connector.wingempacket import WinGemPacket
from components.button import Button


class TestButton(unittest.TestCase):
    ''' Testing Button (WDB) Objects '''

    def testbutton_extractpackets(self):
        ''' Test extracting multiple button definitions '''

        buttondefprefix = "WDB" + WinGemPacket.AM + WinGemPacket.AM

        firstbuttondef = "def1" + WinGemPacket.VM
        firstbuttondef = firstbuttondef + "item1" + WinGemPacket.VM
        firstbuttondef = firstbuttondef + "item2"

        secondbuttondef = "def2" + WinGemPacket.VM
        secondbuttondef = secondbuttondef + "item2.1" + WinGemPacket.VM
        secondbuttondef = secondbuttondef + "item2.2"

        thirdbuttondef = "def3" + WinGemPacket.VM
        thirdbuttondef = thirdbuttondef + "item3.1" + WinGemPacket.VM
        thirdbuttondef = thirdbuttondef + "item3.2"

        testpacketstring = buttondefprefix
        testpacketstring = testpacketstring + firstbuttondef + WinGemPacket.AM
        testpacketstring = testpacketstring + secondbuttondef + WinGemPacket.AM
        testpacketstring = testpacketstring + thirdbuttondef

        testpacket = WinGemPacket(testpacketstring)

        buttonpacketlist = Button.enumpackets(testpacket)
        self.assertEqual(buttonpacketlist[0].stringify(), buttondefprefix + firstbuttondef)
        self.assertEqual(buttonpacketlist[1].stringify(), buttondefprefix + secondbuttondef)
        self.assertEqual(buttonpacketlist[2].stringify(), buttondefprefix + thirdbuttondef)

    def testbutton_addpacket1(self):
        ''' Test creating Button object '''
        optionslist = list("C")
        optionslist.append('<img="canceltool.ico" >Delete')
        optionslist.append("E")
        optionslist.append("WGUF:1:3:DELETE")
        optionslist.append("Help, help, I'm being repressed")
        optionslist.append("Y")
        optionslist.append("")
        optionslist.append("")
        optionslist.append("DELETE")
        optionsstring = (WinGemPacket.VM).join(optionslist)
        buttonpacket = (WinGemPacket.AM).join(("WDB", "13", optionsstring))
        button = Button()
        success = button.addpacket(WinGemPacket(buttonpacket))[0]

        self.assertEqual(success, True)
        self.assertEqual(button.type, "C")
        self.assertEqual(button.tag, "Delete")
        self.assertEqual(button.sendtype, "E")
        self.assertEqual(button.sendtext, "WGUF:1:3:DELETE")
        self.assertEqual(button.help, "Help, help, I'm being repressed")
        self.assertEqual(button.enabled, True)
        self.assertEqual(button.row, 0.0)
        self.assertEqual(button.col, 0.0)
        self.assertEqual(button.name, "DELETE")
        self.assertEqual(button.height, button.DEFAULTBUTTONHEIGHT * Button.BUTTONSCALE)
        self.assertEqual(button.width, button.DEFAULTBUTTONWIDTH)

        self.assertEqual(button.filename, "wdres/canceltool.svg")
        self.assertEqual(button.stringrepresentation, buttonpacket)

        button.setheight(5)
        button.setwidth(17)
        self.assertEqual(button.height, 4.75)
        self.assertEqual(button.width, 17.0)

        self.assertEqual(button.getid(), "500_DELETE")

    def testbutton_addpacket2(self):
        ''' Test creating Button object '''
        optionslist = list("C")
        optionslist.append('<img="CANCELTOOL.ICO" >Delete')
        optionslist.append("E")
        optionslist.append("WGUF:1:3:DELETE")
        optionslist.append("Help, help, I'm being repressed")
        optionslist.append("Y")
        optionslist.append("10")
        optionslist.append("50")
        optionslist.append("")
        optionslist.append("")
        optionslist.append("")
        optionslist.append("")
        optionslist.append("")
        optionslist.append("2")
        optionslist.append("15")
        optionsstring = (WinGemPacket.VM).join(optionslist)
        buttonpacket = (WinGemPacket.AM).join(("WDB", "13", optionsstring))
        button = Button()
        success = button.addpacket(WinGemPacket(buttonpacket))[0]

        self.assertEqual(success, True)
        self.assertEqual(button.type, "C")
        self.assertEqual(button.tag, "Delete")
        self.assertEqual(button.sendtype, "E")
        self.assertEqual(button.sendtext, "WGUF:1:3:DELETE")
        self.assertEqual(button.help, "Help, help, I'm being repressed")
        self.assertEqual(button.enabled, True)
        self.assertEqual(button.row, 10.0)
        self.assertEqual(button.col, 50.0)
        self.assertEqual(button.name, "Delete")
        self.assertEqual(button.height, 2.0 * Button.BUTTONSCALE)
        self.assertEqual(button.width, 15.0)
        self.assertEqual(button.filename, "wdres/canceltool.svg")
        self.assertEqual(button.stringrepresentation, buttonpacket)

    def testbutton_addbadpacket(self):
        ''' Test creating Button object from bad packet'''
        optionslist = list("C")
        optionslist.append('<img="CancelTool.ico" >Delete')
        optionslist.append("E")
        optionslist.append("WGUF:1:3:DELETE")
        optionslist.append("Help, help, I'm being repressed")
        optionslist.append("Y")
        optionslist.append("A")  # Non-numeric value
        optionslist.append("B")  # Non-numeric value
        optionslist.append("")
        optionslist.append("")
        optionslist.append("")
        optionslist.append("")
        optionslist.append("")
        optionslist.append("2")
        optionslist.append("15")
        optionsstring = (WinGemPacket.VM).join(optionslist)
        buttonpacket = (WinGemPacket.AM).join(("WDB", "13", optionsstring))
        button = Button()
        success = button.addpacket(WinGemPacket(buttonpacket))[0]

        self.assertEqual(success, False)


if __name__ == "__main__":
    unittest.main()
