'''
Created on Nov 18, 2016

@author: bouchcla
'''

from components.wdobject import BaseWDObject
from connector.wingempacket import WinGemPacket


class Application(BaseWDObject):
    '''
    Handles WA packets
    '''

    def __init__(self,):
        '''
        Constructor
        '''
        super(Application, self).__init__("APP")
        self.rowoffset = None
        self.coloffset = None
        self.colourchange = False
        self.stylearea = None
        self.target = None
        self.colour = None

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Add WA packet '''
        if packet.packettype() == "WA":
            apptype = packet.extract(2)
            hostdata = None
            if apptype in ("SET.FONT", "RESET.FONT"):
                hostdata = chr(27) + "WGBG" + WinGemPacket.AM + "FONT.METRICS" + WinGemPacket.AM + \
                    "Segoe UI" + WinGemPacket.VM + "8.25" + WinGemPacket.VM + "0" + \
                    WinGemPacket.VM + "0" + WinGemPacket.VM + "0" + WinGemPacket.VM + "0" + \
                    WinGemPacket.VM + "2" + WinGemPacket.VM + "8"
            elif apptype == "SET.SCREEN.OFFSET":
                self.rowoffset = float(packet.extract(3, 1)) * 0.7
                self.coloffset = float(packet.extract(3, 2)) * 0.9
            elif apptype in ["RESET.COLOUR", "SET.COLOUR"]:
                self.colourchange = True
                self.stylearea = packet.extract(3)
                self.colour = packet.extract(4)
                if self.colour:
                    self.colour = "#" + self.colour
                # set the jquery selectors for the elements we want to style
                # any elements that match will be processed.
                if self.stylearea == "TOOLBAR":
                    self.target = "#commandbarcontainer"
                elif self.stylearea == "BACKGROUND":
                    self.target = "#windowcontainer,.wdmenubar"  # React handles the rest now
                elif self.stylearea == "EDITABLE":
                    self.target = " "  # React handles this, but we need to send the packet
                elif self.stylearea == "SHOWFIELD":
                    self.target = " "  # React handles this, but we need to send the packet
                elif self.stylearea == "TEXT":
                    self.target = " "  # React handles this, but we need to send the packet
                elif self.stylearea == "FOCUS":
                    self.target = " "  # React handles this, but we need to send the packet
            self._complete = True
            return True, hostdata, None
        elif packet.packettype() == "WMA":
            hostdata = chr(27) + "WHIR: 0" + WinGemPacket.VM + " 0" + WinGemPacket.VM + \
                " 20050" + WinGemPacket.VM + " 11000" + WinGemPacket.VM + " 15210" + \
                WinGemPacket.VM + " 10350" + WinGemPacket.VM + " 7" + WinGemPacket.VM + " 17" + \
                WinGemPacket.VM + " 15" + WinGemPacket.VM + " 15" + WinGemPacket.VM + \
                "MS Sans Serif" + WinGemPacket.VM + " 8.25" + WinGemPacket.VM + " 0" + \
                WinGemPacket.VM + " 0" + WinGemPacket.VM + " 0" + WinGemPacket.VM + " 0"
            self._complete = True
            return True, hostdata, None
        elif packet.packettype() == "WMO":
            hostdata = chr(27) + "WHIR: 8" + WinGemPacket.VM + " 0" + WinGemPacket.VM + " 2" + \
                WinGemPacket.VM + " 8" + WinGemPacket.VM + " 1" + WinGemPacket.VM + " 1" + \
                WinGemPacket.VM + " 32" + WinGemPacket.VM + " 32" + WinGemPacket.VM + " 3" + \
                WinGemPacket.VM + " 3" + WinGemPacket.VM + " 4" + WinGemPacket.VM + " 4" + \
                WinGemPacket.VM + " 4" + WinGemPacket.VM + " 4" + WinGemPacket.VM + " 2" + \
                WinGemPacket.VM + " 2" + WinGemPacket.VM + " 3" + WinGemPacket.VM + " 3" + \
                WinGemPacket.VM + " 1" + WinGemPacket.VM + " 1" + WinGemPacket.VM + " 8" + \
                WinGemPacket.VM + " 8" + WinGemPacket.VM + " 1920" + WinGemPacket.VM + " 1017" + \
                WinGemPacket.VM + " 17" + WinGemPacket.VM + " 17" + WinGemPacket.VM + " 17" + \
                WinGemPacket.VM + " 32" + WinGemPacket.VM + " 32" + WinGemPacket.VM + " 75" + \
                WinGemPacket.VM + " 75" + WinGemPacket.VM + " 1936" + WinGemPacket.VM + " 1056" + \
                WinGemPacket.VM + " 3856" + WinGemPacket.VM + " 1096" + WinGemPacket.VM + " 15" + \
                WinGemPacket.VM + " 15" + WinGemPacket.VM + " 19" + WinGemPacket.VM + " 19" + \
                WinGemPacket.VM + " 136" + WinGemPacket.VM + " 39" + WinGemPacket.VM + " 160" + \
                WinGemPacket.VM + " 28" + WinGemPacket.VM + " 160" + WinGemPacket.VM + " 28" + \
                WinGemPacket.VM + " 136" + WinGemPacket.VM + " 39" + WinGemPacket.VM + " 1920" + \
                WinGemPacket.VM + " 1080" + WinGemPacket.VM + " 36" + WinGemPacket.VM + " 22" + \
                WinGemPacket.VM + " 8" + WinGemPacket.VM + " 8" + WinGemPacket.VM + " 16" + \
                WinGemPacket.VM + " 16" + WinGemPacket.VM + " 3840" + WinGemPacket.VM + " 1080" + \
                WinGemPacket.VM + " 17" + WinGemPacket.VM + " 17" + WinGemPacket.VM + " 23" + \
                WinGemPacket.VM + " 0" + WinGemPacket.VM + " 20" + WinGemPacket.VM + " 23" + \
                WinGemPacket.VM + " 17" + WinGemPacket.VM + " 0" + WinGemPacket.VM + " 0" + \
                WinGemPacket.VM + " 1" + WinGemPacket.VM + " 0" + WinGemPacket.VM + " 0" + \
                WinGemPacket.VM + " 1" + WinGemPacket.VM + " 1" + WinGemPacket.VM + " 3" + \
                WinGemPacket.VM + " 0" + WinGemPacket.VM + " 0" + WinGemPacket.VM + " 1" + \
                WinGemPacket.VM + " 0" + WinGemPacket.VM + " 0" + WinGemPacket.VM + " 0" + \
                WinGemPacket.VM + " 0" + WinGemPacket.VM + " 0" + WinGemPacket.VM + " 0" + \
                WinGemPacket.VM + "Single User" + WinGemPacket.VM + "Workstation"
            self._complete = True
            return True, hostdata, None
        return False, "", None

    def gettarget(self):
        '''returns target for colour changing'''
        return self.target

    def getcolour(self):
        '''returns colour'''
        return self.colour

    def getarea(self):
        '''returns style area'''
        return self.stylearea

    # TODO: proper implementation of application object
