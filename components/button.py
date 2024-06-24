'''
Created on Nov 24, 2016

@author: holthjef
'''
import logging
from components.wdobject import BaseWDObject
from connector import resource
from connector.wingempacket import WinGemPacket


class Button(BaseWDObject):
    ''' A button definition '''

    DEFAULTBUTTONHEIGHT = 1.35
    DEFAULTBUTTONWIDTH = 10.2857
    BUTTONSCALE = 0.95

    @staticmethod
    def enumpackets(packet: WinGemPacket):
        ''' Static function to expand multiple definitions from a single WDB, WCB packet'''
        packetlist = []
        packettype = packet.extract(1)

        # Could probably us a map (and maybe lambda) here
        if packettype == "WDB":
            for buttondef in WinGemPacket(packet.extractfrom(3)).extractaslist():
                packetlist.append(WinGemPacket((WinGemPacket.AM).join([packettype, "", buttondef])))
        else:
            for buttondef in WinGemPacket(packet.extractfrom(2)).extractaslist():
                packetlist.append(WinGemPacket((WinGemPacket.AM).join([packettype, buttondef])))

        return packetlist

    def __init__(self, packettype: str = "BUTTON"):
        ''' Constructor '''
        super(Button, self).__init__(packettype)
        self._cacheable = True

        self.type = ""
        self.tag = ""
        self.sendtype = ""
        self.sendtext = ""
        self.help = ""
        self.enabled = True
        self.deleted = False
        self.checked = False  # Currently only used by CommandBarTool sub-class
        self.row = 0.0
        self.col = 0.0
        self.name = ""
        self.height = self.DEFAULTBUTTONHEIGHT * Button.BUTTONSCALE
        self.width = self.DEFAULTBUTTONWIDTH
        self.filename = ""
        self.origfilename = ""
        self.screenid = "500"
        self.stringrepresentation = ""
        self.options = {}
        self.autoposition = False

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Configure button object from WinGem WDB or WCB packet '''
        success = False
        packettype = packet.packettype()

        if packettype in ("WDB", "WCB"):
            if packettype == "WDB":
                wdb = True
                defpos = 3
            else:
                wdb = False
                defpos = 2

            try:
                self.stringrepresentation = packet.stringify()

                newtype = packet.extract(defpos, 1)
                if newtype or wdb:
                    self.type = newtype

                newsendtype = packet.extract(defpos, 3)
                if newsendtype or wdb:
                    self.sendtype = newsendtype

                newsendtext = packet.extract(defpos, 4)
                if newsendtext or wdb:
                    self.sendtext = newsendtext

                newhelp = packet.extract(defpos, 5)
                if newhelp or wdb:
                    self.help = newhelp

                newenabled = packet.extract(defpos, 6)
                if newenabled or wdb:
                    if newenabled == "X" and not wdb:
                        self.enabled = False
                        self.deleted = True
                    elif newenabled == "N":
                        self.enabled = False
                        self.deleted = False
                    else:  # newenabled == "Y":
                        self.enabled = True
                        self.deleted = False

                temprow = packet.extract(defpos, 7)
                if temprow:
                    self.row = float(temprow)

                tempcol = packet.extract(defpos, 8)
                if tempcol:
                    self.col = float(tempcol)

                newname = packet.extract(defpos, 9)
                if newname or wdb:
                    self.name = newname

                if temprow and tempcol:
                    # Only allow height and width to be set when explicitly positioned
                    tempheight = packet.extract(defpos, 14)
                    if tempheight:
                        self.height = float(tempheight) * Button.BUTTONSCALE

                    tempwidth = packet.extract(defpos, 15)
                    if tempwidth:
                        self.width = float(tempwidth)

                rawtag = packet.extract(defpos, 2)
                if rawtag or wdb:
                    newtag, newoptions = WinGemPacket(rawtag).parseoptions()
                    self.tag, _ = resource.removehotkey(newtag)
                    self.options = newoptions
                    # Extract filename
                    self.filename = resource.loadimage(self.options.get("img", ""))

                # Calculate name and tag overrides on WDB only
                if wdb:
                    # Use tag if name not specified
                    if self.name:
                        self.name = self.name
                    else:
                        self.name = newtag

                # Because some developers think a button with no identifying features
                # is a good idea!
                # if not (self.tag == "" and self.filename == ""):
                success = True
            except Exception:  # pylint:disable=broad-except
                logging.error(" ".join(["Failed to parse", packettype,
                                        "packet:", self.stringrepresentation]))

        return success, None, self

    def getid(self):
        ''' override getid '''
        return str(self.screenid) + "_" + self.name.replace(" ", "_")

    def setheight(self, height: float):
        ''' Set the button height '''
        self.height = height * Button.BUTTONSCALE

    def setwidth(self, width: float):
        ''' Set the button width '''
        self.width = width
