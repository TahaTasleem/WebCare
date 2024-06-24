'''
Created on Jan 24, 2017

@author: cartiaar
'''
from components.wdobject import BaseWDObject
from components.command import Command
from connector.wingempacket import WinGemPacket
from connector import utility


class MenuBar(BaseWDObject):
    ''' A prompt definition '''

    def __init__(self):
        ''' Constructor '''
        super().__init__("MENUBAR")
        self._cacheable = True

        self.live = False
        self.currenttab = -1
        self.tabs = []
        self.subtabs = []
        self.packet = ""
        self.draw = False

        self.promptnum = 0
        self.justification = "L"
        self.maxlength = 150
        self.displaywidth = 10
        self.displayheight = 1
        self.edittype = "ALPHA"
        self.promptliteral = ""
        self.prompttype = "P"
        self.tag = ""
        self.screenid = "500"
        self.stringrepresentation = ""
        self.value = []
        self.definitions = []

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Add a packet to the menubar object '''
        if packet.packettype() == "WP":
            if self.stringrepresentation == packet.stringify():
                # redefined the exact same menubar, just make sure it's shown
                if self.tabs:
                    tcmd = Command()
                    tcmd.setcommand("type", "MENUBAR")
                    tcmd.setcommand("action", "SHOW")
                    self.draw = True
                else:
                    tcmd = None
                return True, None, tcmd
            elif self.stringrepresentation != "":
                # store current menubar definition
                self.definitions.append((self.screenid, self.stringrepresentation, self.currenttab))
            handled = self._parsewp(packet)
            if handled:
                self._complete = True
                self.draw = True
            return handled, None, self
        elif packet.packettype() in ["WD", "WPD"] and int(packet.extract(2, 1)) == self.promptnum:
            screenid = extras.get('screenid', "0")
            # set the selected tab, if any
            if packet.packettype() == "WPD":
                self.draw = True
            else:
                if screenid == self.screenid:
                    self.draw = True
            value, _ = packet.parseoptions(3)
            try:
                self.currenttab = [x.upper() for x in self.tabs].index(value.upper())
            except ValueError:
                pass
            tcmd = Command()
            tcmd.setcommand('type', "MENUBAR")
            tcmd.setcommand("value", value)
            tcmd.setcommand("action", "SHOW")
            tcmd.addpacket(packet)
            return True, None, tcmd
        elif packet.packettype() == "WMB":
            # menubar command
            tcmd = Command()
            tcmd.addpacket(packet)
            if tcmd.getcommand()['action'] == "HIDE":
                self.draw = False
                tcmd.setcommand('target', self.promptid())
            if tcmd.getcommand()['action'] == "SHOW":
                self.draw = True
            return True, None, tcmd
        return False, None, None

    def getid(self):
        ''' override getid '''
        return self.promptid()

    def close(self, level: int):
        ''' Possible close menubar, restore old one based on close level '''
        if level <= int(self.screenid):
            if self.definitions:
                mblevel, mbpacket, value = self.definitions.pop()
                if int(mblevel) < level:
                    self._parsewp(WinGemPacket(mbpacket))
                    self.screenid = mblevel
                    self.currenttab = value
                    return self
                else:
                    # try again with next item
                    return self.close(level)
            else:
                self.__init__() #pylint:disable=unnecessary-dunder-call
        return None

    def promptid(self, row=None):
        '''
        returns the prompt id
        separate function to handle row requests in grid
        '''
        promptid = str(self.screenid) + "_" + str(self.promptnum)
        if row:
            promptid += "_" + str(row)
        return promptid

    def _parsewp(self, packet: WinGemPacket):
        prompttype = packet.extract(9)
        if prompttype in ("P", "PL"):
            # Parse a WP WinGem Packet
            self.stringrepresentation = packet.stringify()
            self.promptnum = int(packet.extract(2))
            self.packet = packet  # not clear if we have to do this
            menutext = utility.extractfromdelimiter(packet.extract(5), 1, "\\")
            self.tabs = [x.strip() for x in menutext.strip().split("|")
                         if x.strip() and x.strip().upper() != "FINISHED"]
            self.subtabs = []  # reinitialize
            for index, _ in enumerate(self.tabs):
                submenutext = utility.extractfromdelimiter(packet.extract(5), index + 2, "\\")
                if submenutext:
                    self.subtabs.append(
                        [x.strip() for x in submenutext.split("|")
                         if x.strip() and x.strip().upper() != "FINISHED"])
                else:
                    self.subtabs.append("")
            if prompttype == "PL":
                self.live = True
                self.currenttab = 0
            return True
        else:
            return False

    def applyfilemap(self, filemap: dict):
        ''' Check to see if our value is in the file map '''
        self.value = [filemap[value] if value in filemap else value for value in self.value]
