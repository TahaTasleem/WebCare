'''
Created on Nov 21, 2016

@author: holthjef
'''
import unittest
from connector.wingempacket import WinGemPacket
from components.text import Text


class TextTest(unittest.TestCase):
    ''' Testing Text (TX) Objects '''

    def testtext_regulargood(self):
        ''' Test regular Text object '''

        testscreenid = "502"
        testid = "1"
        testrow = 5
        testcol = 1
        testtext = "Some text"
        strpacket = (WinGemPacket.AM).join(["WT", testid, str(testrow), str(testcol), testtext])
        packet = WinGemPacket(strpacket)

        text = Text()
        self.assertEqual(text.addpacket(packet)[0], True)
        text.screenid = "502"

        self.assertEqual(text.getid(), "".join([testscreenid, "_T", testid]))
        self.assertEqual(text.row, testrow)
        self.assertEqual(text.col, testcol)
        self.assertEqual(text.tag, testtext)
        self.assertEqual(text.filename, "")
        self.assertEqual(text.texttype, "")
        self.assertEqual(text.stringrepresentation, strpacket)

    def testtext_image(self):
        ''' Test good image Text object '''

        # No handling, currently, for blank image text, or non-existent image file
        testscreenid = "502"
        testid = "1"
        testrow = 5
        testcol = 1
        testtext = "Akbar.ico"
        testtype = "IMAGE"
        strpacket = (WinGemPacket.AM).join(["WT", testid, str(testrow),
                                            str(testcol), testtext.upper(), testtype])
        packet = WinGemPacket(strpacket)

        text = Text()
        self.assertEqual(text.addpacket(packet)[0], True)
        text.screenid = "502"

        self.assertEqual(text.getid(), "".join([testscreenid, "_T", testid]))
        self.assertEqual(text.row, testrow)
        self.assertEqual(text.col, testcol)
        self.assertEqual(text.tag, "")
        self.assertEqual(text.filename, "wdres/" + testtext.lower())
        self.assertEqual(text.texttype, testtype)
        self.assertEqual(text.stringrepresentation, strpacket)

    def testtext_regularnegatives(self):
        ''' Test regular Text object with negative numbers'''

        # Negative positions ARE allowed
        # Negative IDs currently don't matter as the property is not used
        testscreenid = "502"
        testid = "-1"
        testrow = -5
        testcol = -1
        testtext = "Some text"
        strpacket = (WinGemPacket.AM).join(["WT", testid, str(testrow), str(testcol), testtext])
        packet = WinGemPacket(strpacket)

        text = Text()
        self.assertEqual(text.addpacket(packet)[0], True)
        text.screenid = "502"

        self.assertEqual(text.getid(), "".join([testscreenid, "_T", testid]))
        self.assertEqual(text.row, testrow)
        self.assertEqual(text.col, testcol)
        self.assertEqual(text.tag, testtext)
        self.assertEqual(text.filename, "")
        self.assertEqual(text.texttype, "")
        self.assertEqual(text.stringrepresentation, strpacket)

    def testtext_badpacket(self):
        ''' Test bad TX packet'''

        testid = "1"
        testrow = "Arow"
        testcol = "Bcol"
        testtext = "Some text"
        strpacket = (WinGemPacket.AM).join(["WT", testid, str(testrow), str(testcol), testtext])
        packet = WinGemPacket(strpacket)

        text = Text()
        self.assertEqual(text.addpacket(packet)[0], False)

    def testtext_regularnotext(self):
        ''' Test regular Text object, but without any parms '''

        strpacket = (WinGemPacket.AM).join(["WT"])
        packet = WinGemPacket(strpacket)

        text = Text()
        self.assertEqual(text.addpacket(packet)[0], False)

    def testtext_subhead(self):
        ''' Test subheading Text object '''
        # TODO: Build test for sub-heading TEXT object
        pass

if __name__ == "__main__":
    unittest.main()
