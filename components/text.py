'''
Created on Nov 17, 2016

@author: holthjef
'''
import logging
from components.wdobject import BaseWDObject
from connector.wingempacket import WinGemPacket
from connector import resource

class Text(BaseWDObject):
    ''' A text definition '''

    # Constants
    TEXT_TYPE_TEXT = ""
    TEXT_TYPE_IMAGE = "IMAGE"

    def __init__(self):
        ''' Constructor '''
        super(Text, self).__init__("TEXT")
        self._cacheable = True

        self.textnum = 0
        self.row = 0.0
        self.col = 0.0
        self.tag = ""
        self.filename = ""
        self.texttype = ""
        self.screenid = "500"
        self.stringrepresentation = ""
        self.heading = False

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Configure Text object from WinGem WT packet '''

        success = False

        if packet.packettype() == "WT":
            try:
                self.stringrepresentation = packet.stringify()
                self.textnum = packet.extract(2)

                temprow = packet.extract(3)
                if temprow:
                    self.row = float(temprow)

                tempcol = packet.extract(4)
                if tempcol:
                    self.col = float(tempcol)

                self.tag = packet.extract(5)

                self.texttype = packet.extract(6)
                if self.texttype == self.TEXT_TYPE_IMAGE:
                    #===============================================================
                    # GUICommandSet notes more parameters in subsequent values which are not
                    #   supposed to be implemented
                    # Limit to first value, just in case
                    #===============================================================
                    imgname = packet.extract(5, 1)
                    self.filename = resource.loadimage(imgname)
                    if imgname and not self.filename:
                        # Image not found, display icon name
                        self.filename = ""
                        self.tag = imgname
                        self.texttype = self.TEXT_TYPE_TEXT
                    else:
                        self.tag = ""
                else:
                    self.texttype = self.TEXT_TYPE_TEXT  # Treat all unsupported types as plain TEXT

                if not (self.tag == "" and self.filename == ""):
                    success = True
            except ValueError:
                logging.error("Failed to parse WT packet: " + self.stringrepresentation)

        if success:
            self._complete = True
        return success, None, self

    def makeheading(self):
        ''' Make Text object a screen heading '''
        self.heading = True

    # Note that WinGem doesn't currently handle text item redefining

    # Discussed with Clayton.
    # We are thinking that at some point, this object will know at least the starting
    #   row of the screen it is in so that it can make the determination and
    #   then draw the itself different (likely inside a div with a particular class to
    #   facilitate styling)

    def getid(self):
        ''' override getid '''
        if self.heading:
            return str(self.screenid) + "_heading"
        else:
            return str(self.screenid) + "_T" + str(self.textnum)
