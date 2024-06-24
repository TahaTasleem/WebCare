'''
Created on Jan 9, 2017

@author: bouchcla
'''

from connector.wingempacket import WinGemPacket

from components.prompt import Prompt
from components.wdobject import BaseWDObject


class Grid(BaseWDObject):
    '''     Handles MV Windows    '''

    def __init__(self):
        '''
        Constructor
        '''
        super().__init__("GRID")
        self.startcol = 0
        self.endcol = 0
        self.startrow = 0
        self.endrow = 0
        self.startprompt = 0
        self.endprompt = 0
        self.controltype = ""
        self.verticallines = "N"
        self.horizontallines = "N"
        self.vertical = False
        self.sortable = False
        self.wrapoption = "Y"
        self.headingstyle = ""
        self.headingjoinlist = []
        self.prompts = []
        self.column = []
        self.gridid = "0_grid"
        self._selectedrow = 1
        self.lastdisplayedprompt = 0
        self._complete = True
        self.screenid = "500"
        self.small = False
        self.stringrepresentation = ""
        self.totalwidth = 0
        self.freezecols = 0
        self.freezerows = 0

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Add WW Packet '''
        processed = False
        retobj = self
        hostdata = None
        if packet.packettype() == "WW":
            self._parseww(packet)
            processed = True
        elif packet.packettype() == "WDD":
            processed = self._parsewdd(packet)
            retobj = None
        elif packet.packettype() == "WC":
            processed, hostdata, retobj = self._parsewc(packet)
        elif packet.packettype() == "WIV":
            self._parsewiv(packet)
            retobj = None
        elif packet.packettype() == "WDV":
            self._parsewdv(packet)
            retobj = None
        elif packet.packettype() == "WMG":
            processed = self._parsewmg(packet)
            retobj = None
        return processed, hostdata, retobj

    def getid(self):
        ''' return grid id '''
        return self.gridid

    def getprompt(self, promptnum: int):
        ''' return prompt that matches prompt num '''
        promptmatches = [prompt for prompt in self.prompts if prompt.promptnum == promptnum]
        if promptmatches:
            return promptmatches[0]
        else:
            return None

    def getwidth(self):
        ''' get width of the grid for drawing '''
        self.totalwidth = 0
        for prompt in self.prompts:
            if prompt.visible():
                self.totalwidth += prompt.displaywidth
        if self.small and self.totalwidth:
            return self.totalwidth

        return self.endcol - self.startcol

    def _parseww(self, packet: WinGemPacket):
        ''' Parse WW packet '''
        self.stringrepresentation = packet.stringify()
        self.startrow = float(packet.extract(2))
        self.endrow = float(packet.extract(4))
        self.startcol = float(packet.extract(3))
        self.endcol = float(packet.extract(5))
        self.startprompt = int(packet.extract(6))
        self.endprompt = int(packet.extract(7))
        self.controltype = packet.extract(8)
        if self.controltype == "D":
            # treat D and empty as the same
            self.controltype = ""
        gridoptions = packet.extractaslist(9)
        for item in gridoptions:
            pitem = WinGemPacket(item)
            if item == "VERTICAL":
                self.vertical = True
            elif item == "SORTABLE":
                self.sortable = True
            elif pitem.extract(1, 1, 1) == "LINES":
                if pitem.extract(1, 1, 2)[0]:
                    self.horizontallines = pitem.extract(1, 1, 2)[0]
                if pitem.extract(1, 1, 2)[1]:
                    self.verticallines = pitem.extract(1, 1, 2)[1]
        if packet.extract(10):
            self.wrapoption = packet.extract(10)
        headingjoinlist = ""
        if packet.extract(11):
            self.headingstyle = packet.extract(11)
            if self.headingstyle[0] == "C":
                headingjoinlist = self.headingstyle[1:]
                self.headingstyle = self.headingstyle[0:1]
        self._parseheadingjoin(headingjoinlist)

    def _parsewdd(self, packet: WinGemPacket):
        ''' handle data from browser '''
        if packet.extract(2) == "ROW":
            if self.startprompt == int(packet.extract(3)):
                self._selectedrow = int(packet.extract(4))
                return True
        return False

    def _parsewmg(self, packet: WinGemPacket):
        ''' Parse Modify Grid Packet '''
        if self.startprompt == int(packet.extract(2)):
            freezecols = packet.extract(3, 1)
            if freezecols:
                self.freezecols = int(freezecols)
            freezerows = packet.extract(3, 2)
            if freezerows:
                self.freezerows = int(freezerows)
            return True
        return False

    def _parsewdv(self, packet: WinGemPacket):
        ''' handle WDV '''
        if self.prompts[0].promptnum == int(packet.extract(2, 1)):
            rowtodel = int(packet.extract(2, 2))
            for prompt in self.prompts:
                prompt.deleterow(rowtodel)

    def _parsewiv(self, packet: WinGemPacket):
        ''' handle WIV '''
        if self.prompts[0].promptnum == int(packet.extract(2, 1)):
            rowtoinsert = int(packet.extract(2, 2))
            for prompt in self.prompts:
                prompt.insertrow(rowtoinsert)

    def _parsewc(self, packet: WinGemPacket):
        ''' handle request from host '''
        wctype = packet.extract(2)
        handled = False
        hostdata = None
        retobj = None
        if not self.prompts:
            # grid with no prompts yet
            pass
        elif wctype == "QUERYROW":
            if self._selectedrow > len(self.getprompt(self.startprompt).value):
                # grid may have been reset
                self._selectedrow = 1
            if self.controltype == "MS":
                if self.startprompt == int(packet.extract(3, 1)):
                    handled = True
                    hostdata = str(self._selectedrow)
            elif self.controltype:
                if self.startprompt == int(packet.extract(3, 1)):
                    handled = True
                    hostdata = str(self._selectedrow)
            else:
                # edit grid, just return current row
                if int(packet.extract(3, 1)) in range(self.startprompt, self.endprompt + 1):
                    handled = True
                    hostdata = str(self._selectedrow)
        elif wctype == "SETROW":
            prompt = self.prompts[0]
            if prompt.promptnum == int(packet.extract(3, 1)):
                self._selectedrow = int(packet.extract(3, 2))
                handled = True
        elif wctype == "CLEARALL":
            if self.startprompt == int(packet.extract(3, 1)):
                for prompt in self.prompts:
                    prompt.cleardata()
                handled = True
                retobj = self
            self._selectedrow = 1
        return handled, hostdata, retobj

    def _parseheadingjoin(self, headingjoinlist):
        ''' build heading join list '''
        for x in range(self.startprompt, self.endprompt + 1):
            self.column.append([x])
        if headingjoinlist:
            headings = headingjoinlist.split(",")
            for heading in headings:
                headerjoin = heading.split("-")
                headerjoinlist = list(range(int(headerjoin[0]), int(headerjoin[1]) + 1))
                # find current location of start item
                for i, lst in enumerate(self.column):
                    for item in lst:
                        if item in headerjoinlist:
                            self.column[i].remove(item)
                        if item == int(headerjoin[0]):
                            self.column[i] = headerjoinlist
            # clean the list
            self.column = [x for x in self.column if x]

    def addprompt(self, prompt: Prompt):
        ''' add a prompt to the grid '''
        if prompt.promptnum in range(self.startprompt, self.endprompt + 1):
            if prompt.edittype == "CHECKBOX":
                # grid may NOT be marked as MS
                # and self.controltype == "MS":
                # for a multi-select grid, move a checkbox to the start
                prompt.checkedvalue = "*"
                prompt.uncheckedvalue = ""
                self.prompts.insert(0, prompt)
                # join the checkbox prompt if C is set
                if self.headingstyle == "C" and (not prompt.tag or (
                        len(self.prompts) > 1
                        and not self.prompts[1].tag)):
                    self.column[0].append(prompt.promptnum)
                    self.prompts[1].checkbox = True
                elif prompt.promptnum not in self.column[0]:
                    self.column.insert(0, [prompt.promptnum])
                for i, _ in enumerate(self.column):
                    if i > 0:
                        try:
                            self.column[i].remove(prompt.promptnum)
                        except ValueError:
                            pass
                self.column = [x for x in self.column if x]
            else:
                self.prompts.append(prompt)
            if prompt.promptnum == self.endprompt:
                self.finishgrid()
            if prompt.edittype in ("WP", "WORDWRAP"):
                self.horizontallines = "Y"
            return True
        return False

    def finishgrid(self):
        ''' complete grid '''
        numeditprompts = sum([1 if prompt.prompttype != "S" and prompt.prompttype != "X"
                              else 0 for prompt in self.prompts])

        if self.controltype == "MS" and not self.prompts[0].edittype == "CHECKBOX":
            # convert to multi-select, single style
            if numeditprompts:
                self.controltype = ""
            else:
                self.controltype = "MSS"

        if len(self.prompts) == 1 and not self.controltype \
                and not self.headingstyle:
            if self.prompts[0].edittype in ("WORDWRAP", "WP") and not self.headingstyle:
                # if we are a single column grid with a wordwrwap prompt,
                # convert heading to float
                self.headingstyle = "F"
            if self.prompts[0].tagcol != self.startcol:
                # For single prompt grids that don't start in the same spot as the grid
                # convert heading to float
                self.headingstyle = "F"
            if not self.prompts[0].tag:
                # if no heading and single prompt, don't show heading
                self.headingstyle = "N"
        if self.startrow == self.endrow and not self.headingstyle:
            # single row grids do not have any heading
            self.headingstyle = "F"

        # put tagrows of promots into tagrows and tags into prompttags
        tagrows, prompttags = zip( *((p.tagrow, p.tag) for p in self.prompts) )
        if not self.controltype and self.startrow not in tagrows \
                and not self.headingstyle:
            # if our labels don't match the grid start
            # convert heading to float (but not for select style grids)
            self.headingstyle = "F"

        if not self.controltype and self.headingstyle not in ("F", "N") \
                and not any(prompttags):
            # if there are no labels (tags) in prompts header should not be displayed
            self.headingstyle = 'N'

        # if we have editable prompts in a show select
        # it's not a show select grid
        if self.controltype == "SS" and numeditprompts:
            self.controltype = "ES"

        if self.controltype == "MS" and numeditprompts:
            self.controltype = "MES"

        if self.controltype == "SS" and self.prompts[0].origprompttype == "DS":
            # convert to direct select
            self.controltype = "DS"

        # may have definitions for columns that don't exist!
        for i in range(0, len(self.column)): # pylint: disable=C0200
            self.column[i] = [x for x in self.column[i] if self.getprompt(x) is not None]

        # determine last column to be displayed
        # determine total size of grid and if it is too large
        self.totalwidth = 0
        for prompt in self.prompts:
            if prompt.visible():
                self.lastdisplayedprompt = prompt.promptnum
                self.totalwidth += prompt.displaywidth
        if self.totalwidth + self.startcol <= self.endcol:
            self.small = True
        else:
            self.small = False

    def setrow(self, rownum):
        ''' Set currently active row '''
        try:
            self._selectedrow = int(rownum)
        except ValueError:
            pass

    def getnumrows(self):
        ''' get number of rows '''
        # first prompt should be controlling prompt
        # get number of rows from it?
        pindex = 0
        try:
            if self.controltype == "MS" or self.prompts[0].edittype == "CHECKBOX":
                pindex = 1
        except IndexError:
            return 0
        # the number of rows is actually the largest list across all prompts
        rows = max(len(l.value) for l in self.prompts)
        hassomething = sum([1 if (prompt.value and prompt.value[0]) else 0
                            for prompt in self.prompts])
        if rows == 1 and hassomething < 1:
            # do we really have any data, or is just a count of blank data
            rows = 0
        # add blank row for non-select rows
        # if they're controlling prompt is not a show and not already blank
        if not self.controltype and self.prompts[pindex].prompttype != "S" and \
                self.prompts[pindex].value and \
                (rows == 0 or
                 (len(self.prompts[pindex].value) == rows and self.prompts[pindex].value[rows - 1])
                ):
            rows += 1
        return rows

    def __str__(self) -> str:
        """ Display String for Grid """
        # show only 5 prompts
        prompts = (self.prompts or [])[:5]
        return f"Grid - id = {self.gridid or ''}, wrapoption = {self.wrapoption or ''}, prompts = {prompts}" # pylint:disable=line-too-long

    def __repr__(self) -> str:
        """ Display Representation using __str__ method """
        return self.__str__()
