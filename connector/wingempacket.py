'''
Created on Oct 12, 2016

@author: bouchcla
'''

import re
from csipyutils.uv.varlenarray import VarLenArray


class WinGemPacket(VarLenArray):
    ''' Class to manage a WinGem packet '''

    def parseoptions(self, am: int = 1, vm: int = None, sm: int = None):
        ''' Separate tag text from embedded options list '''
        tagstring = self.extract(am, vm, sm)

        try:
            if tagstring[0:2] == chr(27) + "<":
                tagpieces = tagstring[2:].split(">")

                #===================================================================
                # Build options:
                # Regular expression, loop, and strip are
                #   1) Breaking on any space not inside quotes to get parms
                #   2) Breaking each parm on equals sign to get keyword value pair
                #   3) Stripping quotes from value
                #   4) Storing value in a dictionary keyed by keyword
                #===================================================================
                optionstring = tagpieces[0]
                options = {k: v.strip('"') for k, v in re.findall(r'(\S+)=(".*?"|\S+)',
                                                                  optionstring)}

                # Handle case of ">" appearing in caption text, otherwise would be simpler
                tag = ">".join(tagpieces[1:])
            else:
                tag = tagstring
                options = {}
        except Exception:  # pylint:disable=broad-except
            tag = tagstring
            options = {}

        return tag, options

    def packettype(self):
        ''' get packet type '''
        return self._packet[0]

    def islocalpacket(self):
        ''' returns true if local packet, false otherwise '''
        localpackets = ["WGI", "WMA"]
        return self.packettype() in localpackets

    def isignorepacket(self):
        ''' returns true if ignore packet, false otherwise '''
        ignorepackets = ["WAC", "DDI"]
        return self.packettype() in ignorepackets

    def stringify(self):
        ''' return string representation '''
        return WinGemPacket.AM.join(self._packet)

    def __str__(self) -> str:
        return self.stringify()
