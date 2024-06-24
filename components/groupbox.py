'''
Created on Mar 27, 2017

@author: bouchcla
'''
import components
from components.wdobject import BaseWDObject
from connector.wingempacket import WinGemPacket


class GroupBox(BaseWDObject):
    '''
    Handle groupbox definition
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.caption = ""
        self.name = ""
        self.startrow = 0
        self.startcol = 0
        self.endrow = 0
        self.endcol = 0
        self.height = 0
        self.width = 0
        self.singleline = 0
        super().__init__("GROUPBOX")

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Add packet for GroupBox '''

        if packet.packettype() == "WGB":
            self._parsewgb(packet)
            return True, None, self

        return False, None, None

    def getid(self):
        ''' return id for groupbox '''
        return self.name

    def _parsewgb(self, packet: WinGemPacket):
        ''' Parse WGB Packet '''
        self.name = packet.extract(2)
        self.singleline = (packet.extract(3) == packet.extract(5))
        self.startrow = float(packet.extract(3)) + 0.35
        self.startcol = float(packet.extract(4)) + 0.35
        self.endrow = float(packet.extract(5)) + 0.42
        self.endcol = float(packet.extract(6)) + 0.75

        self.height = components.applyscaling(self.endrow - self.startrow, True)
        self.width = components.applyscaling(self.endcol - self.startcol, False)

        # Parse Options
        options = packet.extractaslist(7)
        for option in options:
            opacket = WinGemPacket(option)
            optiontype = opacket.extract(1, 1, 1)
            if optiontype == "TEXT":
                self.caption = opacket.extract(1, 1, 2)
            else:
                self.caption = opacket.extract(1, 1, 1)
