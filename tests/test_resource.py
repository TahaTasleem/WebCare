'''
Created on Nov 21, 2016

@author: holthjef
'''
import unittest
import os
from connector import resource
# Need private function to complete code coverage
from connector.resource import _loadimagefrom


class TestResource(unittest.TestCase):
    ''' Testing Resources '''

    def testresource_string(self):
        ''' Test string resources '''

        # Test default language strings (english)
        self.assertEqual(resource.getlanguage(), resource.LANG_EN)
        self.assertEqual(resource.loadstring("IDS_CAP0001"), "OK")
        self.assertEqual(resource.loadstring("IDS_CAP0006"), "Cancel")
        self.assertEqual(resource.loadstring("JUNK_KEY"), "")

        # Test french strings
        resource.setlanguage("fr")
        self.assertEqual(resource.getlanguage(), resource.LANG_FR)
        self.assertEqual(resource.loadstring("IDS_CAP0012"), "Serveur:")
        self.assertEqual(resource.loadstring("IDS_ERROR0017"), "La variable")
        self.assertEqual(resource.loadstring("JUNK_KEY2"), "")

        # Test setting language back to english
        resource.setlanguage("en")
        self.assertEqual(resource.getlanguage(), "en")

        # Test hotkey
        self.assertEqual(resource.removehotkey("ABCDEFG"), ("ABCDEFG", ""))
        self.assertEqual(resource.removehotkey("&ABCDEFG"), ("ABCDEFG", "A"))
        self.assertEqual(resource.removehotkey("ABCDEF&G"), ("ABCDEFG", "G"))
        self.assertEqual(resource.removehotkey("ABCDEFG&"), ("ABCDEFG", ""))
        self.assertEqual(resource.removehotkey("ABC && DEFG"), ("ABC &amp; DEFG", ""))
        self.assertEqual(resource.removehotkey("&ABC && DEFG"), ("ABC &amp; DEFG", "A"))
        self.assertEqual(resource.removehotkey("ABC && DEF&G"), ("ABC &amp; DEFG", "G"))
        self.assertEqual(resource.removehotkey("ABC && DEFG&"), ("ABC &amp; DEFG", ""))
        self.assertEqual(resource.removehotkey("ABC && D && EFG"), ("ABC &amp; D &amp; EFG", ""))
        self.assertEqual(resource.removehotkey("&ABC && D && EFG"), ("ABC &amp; D &amp; EFG", "A"))
        self.assertEqual(resource.removehotkey("ABC && D && EF&G"), ("ABC &amp; D &amp; EFG", "G"))
        self.assertEqual(resource.removehotkey("ABC && D && EFG&"), ("ABC &amp; D &amp; EFG", ""))

    def testresource_image(self):
        ''' Test image resources '''

        # Bad resource ID (filename)
        self.assertEqual(resource.loadimage("NOT.IN.LIST"), "")

        # Good filename / bad case
        self.assertEqual(resource.loadimage("CaNcEltOoL.iCo"), "wdres/canceltool.svg")

        # Bad search folder location
        self.assertEqual(_loadimagefrom("canceltool.ico", os.sep.join(["xxstaticxx", "wdres"])), "")


if __name__ == "__main__":
    unittest.main()
