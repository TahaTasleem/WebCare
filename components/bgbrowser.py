'''
Created on Mar 27, 2017

@author: cartiaar
'''

from components.wdobject import BaseWDObject
from components.command import Command
from connector.wingempacket import WinGemPacket


class BGBrowser(BaseWDObject):
    '''
    Background Browser object
    '''

    def __init__(self, browserid: str, startcomplete: bool):
        ''' Constructor '''
        super(BGBrowser, self).__init__("BGBROWSER")

        # default values
        self.tag = ""
        self.visible = False
        self.url = "about:blank"
        self.browserid = "WGBGB_" + browserid
        self.width = None
        self.zorder = None
        if startcomplete:
            self._complete = True

    def getid(self):
        ''' override getid '''
        return self.browserid

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Handle EBR packets'''
        if packet.packettype() == "EBR":
            options = packet.extractaslist(4)
            tag = [WinGemPacket(x).extract(1, 1, 2) for x in options
                   if WinGemPacket(x).extract(1, 1, 1) == "TAG"]
            tag = tag[0] if tag else ""
            browserid = tag[:5] + "_" + tag[6:]
            if browserid == self.browserid:
                if self.iscomplete():
                    tcmd = Command()
                    tcmd.addpacket(packet)
                    return True, None, tcmd
                else:
                    options = [[WinGemPacket(x).extract(1, 1, 1), WinGemPacket(x).extract(1, 1, 2)]
                               for x in options]
                    for opt in options:
                        optname = opt[0]
                        if optname == "SHOW":
                            self.visible = True
                        elif optname == "HIDE":
                            self.visible = False
                        elif optname == "ENABLE":
                            # enable?
                            pass
                        elif optname == "DISABLE":
                            # disable?
                            pass
                        elif optname == "ZORDER":
                            self.zorder = opt[1]
                        elif optname == "WWIDTH" and browserid == "WGBGB_1":
                            self.width = float(opt[1]) * 0.5
                    url = packet.extract(3)
                    if url:
                        self.url = url
                        self.visible = True
                    self._complete = True
                    return True, None, self
        return False, None, None
