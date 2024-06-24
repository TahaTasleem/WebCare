'''
Created on June 27, 2017

@author: holthjef
'''
import os
import unittest
from connector.wingempacket import WinGemPacket
from components.command import Command
from components.editor import Editor


class TestEditor(unittest.TestCase):
    ''' Testing Editor (WDE) Objects '''

    # Can't test case of good file given current restrictions
    # Unless temporarily build a file into static/data

    def buildpacket(self, action: str, filepath: str, option: str):
        ''' Build WDE packet '''
        # Option should be a list, but currently only one option

        testpacketstring = "WDE" + WinGemPacket.AM + action + WinGemPacket.AM + \
                           filepath + WinGemPacket.AM + option
        testpacket = WinGemPacket(testpacketstring)

        return testpacketstring, testpacket

    def testeditor_contenttype(self):
        ''' Test contenttype '''
        packetstr, packet = self.buildpacket("EDIT", "some path", "CONTENTTYPE=javascript")
        editor = Editor()
        processed, hostdata, cmd = editor.addpacket(packet)
        self.assertEqual(editor.contenttype, "javascript")

        packetstr, packet = self.buildpacket("EDIT", "some path", "CONTENTTYPE=")
        editor = Editor()
        processed, hostdata, cmd = editor.addpacket(packet)
        self.assertEqual(editor.contenttype, "")

        packetstr, packet = self.buildpacket("EDIT", "some path", "")
        editor = Editor()
        processed, hostdata, cmd = editor.addpacket(packet)
        self.assertEqual(editor.contenttype, "")

    def testeditor_readonly(self):
        ''' Test contenttype '''
        packetstr, packet = self.buildpacket("EDIT", "some path", "")
        editor = Editor()
        processed, hostdata, cmd = editor.addpacket(packet)
        self.assertEqual(editor.readonly, False)

        packetstr, packet = self.buildpacket("EDIT", "some path", "READONLY=Y")
        editor = Editor()
        processed, hostdata, cmd = editor.addpacket(packet)
        self.assertEqual(editor.readonly, True)

        packetstr, packet = self.buildpacket("EDIT", "some path", "READONLY=")
        editor = Editor()
        processed, hostdata, cmd = editor.addpacket(packet)
        self.assertEqual(editor.readonly, False)

        packetstr, packet = self.buildpacket("EDIT", "some path", "READONLY")
        editor = Editor()
        processed, hostdata, cmd = editor.addpacket(packet)
        self.assertEqual(editor.readonly, False)

    def testeditor_badlocation(self):
        ''' Test bad location '''
        packetstr, packet = self.buildpacket(
            "EDIT", os.sep + "components" + os.sep + "application.py", "")
        editor = Editor()
        processed, hostdata, cmd = editor.addpacket(packet)
        self.assertEqual(processed, True)
        self.assertEqual(hostdata[:13], "WDEC" + WinGemPacket.VM + "FAIL-GEN")
        self.assertEqual(cmd, None)

        packetstr, packet = self.buildpacket(
            "EDIT", os.sep + "components" + os.sep + "application.py", "READONLY=Y")
        editor = Editor()
        processed, hostdata, cmd = editor.addpacket(packet)
        self.assertEqual(processed, True)
        self.assertEqual(hostdata, None)
        self.assertEqual(cmd, None)

    def testeditor_nonexistentfile(self):
        ''' Test invalid file name (doesn't exist) '''
        packetstr, packet = self.buildpacket(
            "EDIT", "static" + os.sep + "data" + os.sep + "missingfilename.txt", "")
        editor = Editor()
        processed, hostdata, cmd = editor.addpacket(packet)
        self.assertEqual(processed, True)
        self.assertEqual(hostdata[:13], "WDEC" + WinGemPacket.VM + "FAIL-GEN")
        self.assertEqual(cmd, None)

        packetstr, packet = self.buildpacket(
            "EDIT", "static" + os.sep + "data" + os.sep + "missingfilename.txt", "READONLY=Y")
        editor = Editor()
        processed, hostdata, cmd = editor.addpacket(packet)
        self.assertEqual(processed, True)
        self.assertEqual(hostdata, None)
        self.assertEqual(cmd, None)

    # Would like the following cases, but can't do without a real file guaranteed
    # to exist under \static\data\...
        # bad location of second file in DIFF (needs first file to be valid)
        # nonexistent second file in DIFF (needs first file to be valid)
        # same file (needs a valid file)


if __name__ == "__main__":
    unittest.main()
