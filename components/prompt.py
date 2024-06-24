'''
Created on Oct 17, 2016

@author: bouchcla
'''
import math
import string

from connector import resource
from connector.utility import charcount
from connector.wingempacket import WinGemPacket

from components.command import Command
from components.wdobject import BaseWDObject


class Prompt(BaseWDObject):
    ''' A prompt definition '''

    def __init__(self):
        ''' Constructor '''
        super(Prompt, self).__init__("PROMPT")
        self._cacheable = True

        self.promptnum = 0
        self.tagcol = 0.0
        self.tagrow = 0.0
        self.datacol = 0.0
        self.datarow = 0.0
        self.justification = "L"
        self.maxlength = 150
        self.displaywidth = 10
        self.displayheight = 1
        self.edittype = "ALPHA"
        self.promptliteral = ""
        self.optionlist = ""
        self.prompttype = ""
        self.origprompttype = ""
        self.tag = ""
        self.screenid = "500"
        self.stringrepresentation = ""
        self.radiobuttonposition = "VERTICAL"
        self.radiobuttonitems = []
        self.value = []
        self.tlb = False
        self.tlbleft = False
        self.tlbicon = ""
        self.checkedvalue = ""
        self.uncheckedvalue = ""
        self.title = ""
        self.aclist = ""
        self.textcolour = []
        self.bgcolour = []
        self.fullscreen = False
        self.required = False

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Add a packet to the prompt object '''
        retobj = None
        processed = False
        if packet.packettype() == "WP":
            screenendrow = extras.get('screenendrow', 0.0)
            self._parsewp(packet, screenendrow)
            self._complete = True
            processed = True
            retobj = self
        elif packet.packettype() in ["WD", "WPD"]:
            processed, retobj = self._parsewd(packet)
        elif packet.packettype() == "WC":
            if packet.extract(2) == "CLEARALL" and int(packet.extract(3)) == self.promptnum:
                self.value = []
                processed = True
        return processed, None, retobj

    def _parsewd(self, packet: WinGemPacket):
        ''' Parse WD/WPD packets '''
        updateid = int(packet.extract(2, 1))
        rowid = None
        origvalue = self.value

        if packet.packettype() == "WPD":
            pass
            #self.required = (packet.extract(4) or '') == "MANDATORY"

        if packet.extract(2, 2):
            rowid = int(packet.extract(2, 2))
        if updateid == self.promptnum:
            packetlist = [WinGemPacket(x) for x in packet.extractaslist(3)]
            tuplelist = [x.parseoptions(1) for x in packetlist]
            # remove any multi-sub-valued items
            valuelist = [WinGemPacket(x[0]).extract(1, 1, 1) for x in tuplelist]
            commandlist = [x[1] for x in tuplelist]
            singleitemupdate = True
            if rowid:
                # if rowid is larger than grid size, treat as list of data
                # to append to the set
                if rowid > len(self.value) and len(valuelist) > 1:
                    singleitemupdate = False
                    self.value += valuelist
                    origvaluelen = len(self.value)
                    for index, packetdatacommand in enumerate(commandlist):
                        self.bgcolour.insert(
                            index + origvaluelen, resource.getcolorref(
                                packetdatacommand.get('bgcolor', "")))
                        self.textcolour.insert(
                            index + origvaluelen, resource.getcolorref(
                                packetdatacommand.get('color', "")))
                elif rowid < 0:
                    # do nothing in this case
                    pass
                else:
                    while len(self.value) < rowid:
                        # we may be setting a value for something
                        # in the list with no intervening values
                        self.value.append("")
                        self.bgcolour.append("")
                        self.textcolour.append("")
                    self.value[rowid - 1] = valuelist[0]
                    self.bgcolour[rowid - 1] = resource.getcolorref(
                        commandlist[0].get('bgcolor', ""))
                    self.textcolour[rowid - 1] = resource.getcolorref(
                        commandlist[0].get('color', ""))
            else:
                self.value = valuelist
                self.bgcolour = []
                self.textcolour = []
                for index, packetdatacommand in enumerate(commandlist):
                    self.bgcolour.insert(
                        index, resource.getcolorref(packetdatacommand.get('bgcolor', "")))
                    self.textcolour.insert(
                        index, resource.getcolorref(packetdatacommand.get('color', "")))
                if len(valuelist) > 1:
                    # AWD-2021 - can get multivalued data w/o a row value
                    singleitemupdate = False
            tcmd = None
            if self.edittype == "BROWSER" and origvalue == self.value:
                if packet.packettype() == "WPD":
                    tcmd = Command()
                    tcmd.setcommand('targetid', updateid)
                    tcmd.setcommand('required', self.required)
                    tcmd.setcommand('mvndx', rowid)
                    tcmd.setcommand('type', "DISPLAY")
                    tcmd.setcommand("focus", True)
                else:
                    pass
            else:
                orig_rowid = rowid
                if not rowid:
                    rowid = 1
                startrow = rowid if singleitemupdate else 1
                endrow = rowid if singleitemupdate else len(self.value)
                tcmd = []

                duplicateelem = False
                usedorigrow = False

                # for each value in our set, create an update command
                for rowid in range(startrow,endrow+1):
                    tcmdlocal = Command()
                    tcmdlocal.setcommand('targetid', updateid)

                    if not singleitemupdate or orig_rowid:
                        #earlier before changes of AWD-2021 mvndx was set to rowid (here orig_rowid)
                        #current implementation is defaulting it to "1", causing prompt not to be found in the dom so in such case set mvndx to orig row id pylint:disable=line-too-long
                        if rowid == 1 and not singleitemupdate and not orig_rowid and self.prompttype.strip() == "M":
                            # if all subsequent elems value is null then ignore it for modal
                            duplicateelem = not any(val for val in self.value[1:] if val)

                        tcmdlocal.setcommand('mvndx', orig_rowid if duplicateelem else rowid)
                    tcmdlocal.setcommand('type', "DISPLAY")
                    tcmdlocal.setcommand('value', self.value[rowid - 1])
                    tcmdlocal.setcommand('bgcolour', self.bgcolour[rowid - 1])
                    tcmdlocal.setcommand('textcolour', self.textcolour[rowid - 1])
                    tcmdlocal.setcommand("required", self.required)

                    if duplicateelem and not usedorigrow:
                        tcmdlocal.setcommand("focus", (packet.extract(1) == "WPD"))
                        usedorigrow = True
                        duplicateelem = False

                    if (singleitemupdate or rowid == endrow) and not usedorigrow:
                        # set focus to last item if WPD & multivalued
                        tcmdlocal.setcommand("focus", (packet.extract(1) == "WPD"))
                    tcmd.append(tcmdlocal)
            return True, tcmd
        return False, None

    def getid(self):
        ''' override getid '''
        return self.promptid()

    def cleardata(self):
        ''' clear data from prompt '''
        self.value.clear()
        self.bgcolour.clear()
        self.textcolour.clear()

    def promptid(self, row=None):
        '''
        returns the prompt id
        separate function to handle row requests in grid
        '''
        promptid = str(self.screenid) + "_" + str(self.promptnum)
        if row:
            promptid += "_" + str(row)
        return promptid

    def _parsewp(self, packet: WinGemPacket, screenendrow=0):
        ''' Parse a WP WinGem Packet '''
        self.stringrepresentation = packet.stringify()
        try:
            self.promptnum = int(packet.extract(2))
            self.tagrow = float(packet.extract(3))
            self.tagcol = float(packet.extract(4))
            self.tag = packet.extract(5)
            self.datarow = float(packet.extract(6))
            self.datacol = float(packet.extract(7))
        except ValueError:
            # may not be set on some packets
            pass
        just = packet.extract(8, 1)
        maxlen = packet.extract(8, 2)
        displen = packet.extract(8, 3)
        try:
            if just:
                self.justification = just
            if maxlen:
                self.maxlength = int(round(float(maxlen)))
            if displen:
                self.displaywidth = float(displen)
        except ValueError:
            # ignore bad data for now
            pass
        self.prompttype = packet.extract(9)
        # keep copy of original for grid to track
        # but simplify down to single type for all show prompts
        self.origprompttype = self.prompttype
        if self.prompttype in ("SS", "DS"):
            # treat show select identifier like show prompt
            self.prompttype = "S"
        edittype = packet.extract(10)
        if edittype:
            self.edittype = edittype
            if edittype == "CHECKBOX":
                self.tagcol = self.datacol + 3
                self.tagrow = self.datarow
                self.checkedvalue = "*"
                self.uncheckedvalue = " "
        self.promptliteral = packet.extract(11)
        self._parseoptionlist(WinGemPacket(packet.extract(12)))
        if self.prompttype == "X" or \
                (self.prompttype != "M" and
                 self.datarow >= 0 and self.datarow <= screenendrow and
                 self.datacol >= 0):
            # defaults as above
            pass
        else:
            if self.edittype == "YORN" or self.edittype == "NORY" or \
                    self.edittype == "YORN.NODEF":
                defaultcaption = resource.loadstring("IDS_CAP0035")  # Question
            elif self.edittype == "CONFIRM" or self.edittype == "CONFIRM.Y" \
                    or self.edittype == "CONFIRM.N":
                defaultcaption = resource.loadstring("IDS_ERROR0079")  # Warning
            else:
                defaultcaption = resource.loadstring("IDS_CAP0028")  # Entry
            if self.tag == "":
                self.tag = defaultcaption
            self.title = self.tag
            if self.promptliteral == "":
                self.promptliteral = self.tag
                self.title = defaultcaption

        self.required = (packet.extract(12) or '') == "MANDATORY"

    def _parseoptionlist(self, optionlist: WinGemPacket):
        ''' Parse the options list to set properties for the prompt '''
        # Reset these options to the defaults, re-apply if the options are still there
        self.tlb = False
        self.tlbleft = False
        self.tlbicon = ""
        pos = 1
        while True:
            option = optionlist.extract(1, pos, 1)
            if option:
                if option == "RADIO.BUTTONS" or option == "RADIO-BUTTONS":
                    self.radiobuttonitems = []
                    rbpos = 2
                    while True:
                        rbdata = optionlist.extract(1, pos, rbpos).split("=")
                        if len(rbdata) > 1:
                            rbkey = rbdata[0]
                            rbitem = rbdata[1]
                            if rbitem:
                                if rbkey == "ARRANGE":
                                    self.radiobuttonposition = rbitem
                                elif rbkey == "ITEM":
                                    self.radiobuttonitems.append(rbitem.split(","))
                        else:
                            break
                        rbpos += 1
                elif option == "BROWSER":
                    smpos = 2
                    while True:
                        smitem = optionlist.extract(1, pos, smpos)
                        if smitem:
                            if "=" in smitem:
                                smdata = smitem.split("=")
                                if smdata[0] == "HT":
                                    self.displayheight = float(smdata[1])
                        else:
                            break
                        smpos += 1
                elif option == "DDD":
                    self.tlb = True
                elif option == "DDL":
                    self.tlb = True
                    self.tlbleft = True
                elif option == "DDI":
                    self.tlbicon = resource.loadimage(optionlist.extract(1, pos, 2))
                elif option == "EDIT.PARMS":
                    parmpos = 2
                    while True:
                        parm = optionlist.extract(1, pos, parmpos)
                        if parm:
                            if parm == "CHECKED.VALUE" and self.edittype == "CHECKBOX":
                                parmpos += 1
                                self.checkedvalue = optionlist.extract(1, pos, parmpos)
                            elif parm == "UNCHECKED.VALUE" and self.edittype == "CHECKBOX":
                                parmpos += 1
                                self.uncheckedvalue = optionlist.extract(1, pos, parmpos)
                            elif len(parm) < 5:
                                pass
                            elif parm[-5:] == ".EDIT" and self.edittype in ("WP", "WORDWRAP"):
                                self.edittype = parm[0: -5]
                        else:
                            break
                        parmpos += 1
                elif option == "AC.LIST":
                    self.aclist = optionlist.extractfrom(1, pos, 2).split(WinGemPacket.SM)
                elif option == "SELECT":
                    # Is this used??
                    pass
            else:
                break
            pos += 1
        if self.prompttype == "S":
            self.tlb = False

    def deleterow(self, rowtodelete):
        ''' Remove Row '''
        if rowtodelete <= len(self.value):
            del self.value[rowtodelete - 1]
            del self.bgcolour[rowtodelete - 1]
            del self.textcolour[rowtodelete - 1]

    def insertrow(self, rowtoinsert):
        ''' Remove Row '''
        self.value.insert(rowtoinsert - 1, "")
        self.bgcolour.insert(rowtoinsert - 1, "")
        self.textcolour.insert(rowtoinsert - 1, "")

    def visible(self):
        ''' return true if visible '''
        if self.displaywidth > 0 and self.prompttype != "X" and \
                self.datarow != -1.0 and self.datacol != -1.0:
            return True
        else:
            return False

    def applyfilemap(self, filemap: dict):
        ''' Check to see if our value is in the file map '''
        self.value = [filemap[value] if value in filemap else value for value in self.value]

    def numrows(self, row: int):
        ''' Count # of newlines '''
        value = ""
        if row < len(self.value):
            value = self.value[row]

        rows = value.count("\r") + value.count("\n") - value.count("\r\n") + 1
        if rows == 1:
            thin_chars = "Iil1jTt"
            thick_chars = "MmWw"
            # check to see if we have more data than we can show
            punc = charcount(value, string.punctuation + thin_chars)
            thick = charcount(value, thick_chars)
            fieldlen = len(value) - (punc * 0.5) + (thick * 0.5) + 1
            if fieldlen > self.displaywidth and self.displaywidth:
                rows = math.ceil(fieldlen / self.displaywidth)

        return rows

    def __str__(self) -> str:
        """ String represtation for prompt """
        return f"Prompt : id = {self.screenid or ''}, title = {self.title or ''}, promptliteral = {self.promptliteral or ''}, edittype = {self.edittype or ''}" # pylint:disable=line-too-long


    def __repr__(self) -> str:
        """ Show Representation by __str__()   """
        return self.__str__()
    