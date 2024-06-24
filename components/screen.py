'''
Created on Oct 13, 2016

@author: bouchcla
'''
import html
import re
from connector import resource
from connector.configuration import CONFIG
from connector.wingempacket import WinGemPacket

import components
from components.button import Button
from components.command import Command
from components.grid import Grid
from components.groupbox import GroupBox
from components.prompt import Prompt
from components.text import Text
from components.wdobject import BaseWDObject


class Screen(BaseWDObject):
    ''' Object representing a WinGem Screen '''
    _SCREENPACKETS = ["WS", "WP", "WSC", "WD", "WT", "WPD", "WDB",
                      "WCB", "WW", "WWB", "WGB", "WDD", "WC",
                      "WMG", "WDV", "WIV", "WAC", "WH"]

    # Button constants
    _BUTTONOPTIONS_DIRECTIONNDX = 0
    _BUTTONOPTIONS_OKNDX = 1
    _BUTTONOPTIONS_CANCELNDX = 2
    _BUTTONOPTIONS_VERTICAL = "V"
    _BUTTONOPTIONS_CLOSE = "C"
    _BUTTONBARWIDTH = 17
    _BUTTONGAPSIZE = 0.25

    # Screen constants
    _BASESTARTROW = 2  # from frmWGMain:m_intStartRow in WinGem
    _CAPTIONHEIGHT = 0.5
    _NOCAPTIONHEIGHT = 0.3
    _BUFFERSCREEN = 1

    def __init__(self):
        ''' Constructor '''
        super().__init__("SCREEN")
        self._cacheable = True

        # default values
        self.executelevel = 0
        self.calllevel = 0
        self.startrow = 0
        self.startrowdraw = 0
        self.startcol = 0
        self.endrow = 0
        self.endcol = 0
        if not hasattr(self, 'rowoffset'):
            self.rowoffset = 0.0
        if not hasattr(self, 'coloffset'):
            self.coloffset = 0.0
        self.boxtype = ""
        self.buttonoptions = "VYY"
        self.buttonheight = Button.DEFAULTBUTTONHEIGHT
        self.buttonwidth = Button.DEFAULTBUTTONWIDTH
        self.stringrepresentation = ""
        self.height = 0
        self.width = 0
        self.guiwidth = 0
        self.prompts = []
        self.texts = []
        self.buttons = []
        self.grids = []
        self.groupboxes = []
        self._screenbuttondepth = 0
        self.screenid = "500"
        self.focuspromptnum = 0
        self._buttoninsertpos = 0
        self._buttonlasttype = ""
        self.position = None
        self.fillcontainer = False
        self.draw = False
        self.aclists = dict()
        self.title = ""
        self.titleappended = False
        self.ischild = False
        self.hasheading = False
        self.defaultbutton = None

    def getid(self):
        ''' override getid '''
        return str(self.screenid)

    def addpacket(self, packet: WinGemPacket, **extras):
        '''
        Add packet to screen object
        return true if processed
        return false otherwise
        '''
        retobj = None
        handlepacket = False
        hostdata = None
        newscreen = False
        if packet.packettype() in Screen._SCREENPACKETS:
            handlepacket = True
            if packet.packettype() == "WS" and self.iscomplete():
                # a new screen
                handlepacket = False
            elif packet.packettype() == "WS" and not self.iscomplete() and \
                ((self.calllevel != 0 and self.calllevel != packet.extract(3)) or
                 (self.executelevel != 0 and self.executelevel != packet.extract(2))):
                # a new screen
                self.finishscreen()
                self.draw = True
                retobj = self
                handlepacket = False
                newscreen = True
            elif packet.packettype() == "WS":
                self._parsews(packet)
            elif packet.packettype() == "WGB":
                self._parsewgb(packet)
            elif packet.packettype() == "WSC":
                draw = self._parsewsc(packet)
                if draw:
                    retobj = self
            elif packet.packettype() == "WP":
                prompttype = packet.extract(9)
                if prompttype == "P" or prompttype == "PL":
                    # define a menubar, handle elsewhere
                    handlepacket = False
                else:
                    # create prompt object
                    retobj = self._addprompt(packet)
            elif packet.packettype() == "WW":
                # create grid
                retobj = self._addgrid(packet)
            elif packet.packettype() == "WMG":
                # modify grid
                for grid in self.grids:
                    handlepacket, _, retobj = grid.addpacket(packet)
            elif packet.packettype() in ["WD", "WPD"]:
                # try all prompts (for now)
                handlepacket = False
                for prompt in self.prompts:
                    origrows = 0
                    if self.grids:
                        ingrid = [grid for grid in self.grids if prompt in grid.prompts]
                        if ingrid:
                            ingrid = ingrid[0]
                            origrows = ingrid.getnumrows()
                    handlepacket, _, retobj = prompt.addpacket(packet)
                    if handlepacket:
                        if self.grids:
                            if ingrid:
                                # did our grid change size? Have row added/delete?
                                # if so, re-send grid
                                if not packet.extract(2, 2) or (origrows != ingrid.getnumrows()):
                                    # need to do something to reset focus
                                    if isinstance(retobj, list):
                                        retobj.insert(0, ingrid)
                                    else:
                                        retobj = [ingrid, retobj]
                                if packet.packettype() == "WPD":
                                    ingrid.setrow(packet.extract(2, 2))
                        break
                if handlepacket:
                    if not self.iscomplete() or not self.draw:
                        if packet.packettype() == "WPD":
                            # GoldCare doesn't send a WSC SHOW
                            # but a prompting packet means to show the screen
                            retobj = self
                        else:
                            retobj = None
                if packet.packettype() == "WPD":
                    # if we see a WPD, flip us to draw
                    # since it will either be for us, or our menubar
                    if not self.draw:
                        retobj = self
                    # Always mark focus guy for screen on WPD
                    self.focuspromptnum = packet.extract(2, 1)
                    mvndx = packet.extract(2, 2)
                    if mvndx:
                        self.focuspromptnum += "_" + mvndx
                    self.draw = True
                    self.finishscreen()
            elif packet.packettype() == "WT":
                retobj = self._addtext(packet)
            elif packet.packettype() in ("WDB", "WCB"):
                retobj = self._addbutton(packet)
            elif packet.packettype() == "WWB":
                buttonid = packet.extract(2)
                isbutton = [btn for btn in self.buttons if btn.name == buttonid]
                if not isbutton:
                    # convert it to the default button
                    packet.replace(self.defaultbutton, 2)
                if not self.iscomplete() or not self.draw:
                    # WWB can also mean show the screen in GoldCare
                    # TODO: Should also place focus on the button.
                    self.focuspromptnum = packet.extract(2)
                    self.finishscreen()
                    retobj = self
                else:
                    # if screen is complete, let app handle it
                    handlepacket = False
                    retobj = None
                self.draw = True
            elif packet.packettype() in ["WDD", "WC", "WDV", "WIV"]:
                # Assume we aren't handling it
                handlepacket = False
                # may be data for the screen's grid
                for grid in self.grids:
                    handlepacket, hostdata, retobj = grid.addpacket(packet)
                    if handlepacket:
                        break
                if not handlepacket and packet.packettype() == "WC":
                    for prompt in self.prompts:
                        handlepacket, hostdata, retobj = prompt.addpacket(packet)
                        if handlepacket:
                            break
                if packet.packettype() in ("WDV", "WIV"):
                    handlepacket = False
            elif packet.packettype() == "WAC":
                retobj = self._parsewac(packet)
            elif packet.packettype() == "WH":
                retobj = self._addtitle(packet)
        if handlepacket and retobj and not self.iscomplete() and not isinstance(retobj, Command):
            # don't return anything if screen has not been drawn yet
            # Let commands through, specifically allowing WMB, may need to check for that
            # specifically?
            retobj = None
        elif not handlepacket and not newscreen:
            retobj = None

        return handlepacket, hostdata, retobj

    def _parsews(self, packet: WinGemPacket):
        ''' Parse WS Packet into properties '''
        if self.stringrepresentation:
            # We were already defined, so let's reset EVERYTHING
            # Except offset, because we lose it if we reset it
            self.__init__() #pylint:disable=unnecessary-dunder-call

        # now parse packet
        self.stringrepresentation = packet.stringify()
        self.executelevel = packet.extract(2)
        self.calllevel = packet.extract(3)
        self.startrow = float(packet.extract(5))
        self.startcol = float(packet.extract(6))
        self.endrow = float(packet.extract(7))
        self.endcol = float(packet.extract(8))
        self.boxtype = packet.extract(9)
        if packet.extract(12):
            self.buttonoptions = packet.extract(12)
        if packet.extract(13, 1):
            self.buttonheight = float(packet.extract(13, 1))
        if packet.extract(13, 2):
            self.buttonwidth = float(packet.extract(13, 2))
        if packet.extract(14) and self.startrow >= 0 and self.startcol >= 0:
            # only allow positional override if the screen is not defined
            # to be off-screen
            self.position = packet.extract(14)
        # WinGem treats screens starting @ 3 different than other start points
        heightmodifier = 0
        if self.startrow == (Screen._BASESTARTROW + 1) and (self.endcol - self.startcol + 1) > 79:
            heightmodifier = 1
        else:
            self.startrowdraw = self.startrow - Screen._BASESTARTROW
        self.height = self.endrow - self.startrow + Screen._BASESTARTROW + heightmodifier
        self.height = components.applyscaling(self.height, True)
        self.width = (self.endcol - self.startcol) + Screen._BUTTONBARWIDTH
        self.width = components.applyscaling(self.width, False) + Screen._BUFFERSCREEN
        self.guiwidth = self.width + 1.4
        self.screenid = int(self.executelevel) * 1000 + int(self.calllevel) + 500

        if len(self.buttonoptions) > self._BUTTONOPTIONS_CANCELNDX:
            if self.buttonoptions[self._BUTTONOPTIONS_CANCELNDX] != "N":
                self._addcancelbutton(self.buttonoptions[self._BUTTONOPTIONS_CANCELNDX])
        else:
            self._addcancelbutton("Y")

        if len(self.buttonoptions) > self._BUTTONOPTIONS_OKNDX:
            if self.buttonoptions[self._BUTTONOPTIONS_OKNDX] != "N":
                self._addokbutton()
        else:
            self._addokbutton()

    def _parsewgb(self, packet: WinGemPacket):
        ''' Parse Groupbox Packet '''
        gbox = GroupBox()
        gbox.addpacket(packet)
        self.groupboxes.append(gbox)

    def _parsewac(self, packet: WinGemPacket):
        ''' Parse Auto Complete List '''
        listname = packet.extract(2)
        retobj = None
        if listname and listname != chr(21):
            aclist = []
            if listname in self.aclists:
                aclist = self.aclists[listname]
            actions = packet.extractaslist()
            for action in actions[2:]:
                item = WinGemPacket(action)
                entry = item.extract(1, 1)
                if entry == "ADD":
                    itemlist = item.extractaslist(1, 2)
                    for x in itemlist:
                        if x not in aclist:
                            aclist.append(x)
                elif entry == "CLEAR":
                    aclist = []
            self.aclists[listname] = aclist
            if aclist and self.draw:
                # if we've already sent the screen, update the list
                cmd = Command()
                cmd.updateaclist(listname, aclist)
                retobj = cmd
        return retobj

    def _parsewsc(self, packet: WinGemPacket):
        ''' Parse WSC Packet '''
        subpacket = packet.extract(2)
        if subpacket == "SHOW":
            self.finishscreen()
            if not self.draw:
                self.draw = True
                return True
            return False
        return False

    def _addprompt(self, packet: WinGemPacket):
        '''
        Add a prompt to the Screen
        Check if it already exists, if so, replace the current definition
        '''
        promptnum = int(packet.extract(2))
        processed = False
        prompt = None
        origprompt = None
        for testprompt in self.prompts:
            if testprompt.promptnum == promptnum:
                # redefine the prompt
                origprompt = testprompt.stringrepresentation
                _, _, prompt = testprompt.addpacket(packet, screenendrow=self.endrow)
                processed = True
                break
        if not processed:
            prompt = Prompt()
            prompt.addpacket(packet, screenendrow=self.endrow)
            prompt.screenid = self.screenid
            self.prompts.append(prompt)
            if self.grids:
                for grid in self.grids:
                    if grid.addprompt(prompt):
                        break
        ingrid = [grid for grid in self.grids if prompt in grid.prompts]
        if ingrid and prompt.edittype == "CHECKBOX":
            # There are some grids that redefine the checkbox after display, wtf.
            prompt.checkedvalue = "*"
            prompt.uncheckedvalue = ""
        if self.iscomplete() and not ingrid:
            return prompt
        elif ingrid and self.iscomplete():
            # added prompt to grid, may need to re-calc
            # but this can't really do anything. :|
            ingrid[0].finishgrid()
            # returning the grid can cause HUGE problems

            origedittype = WinGemPacket(origprompt).extract(10)
            if origedittype in ("WP", "WORDWRAP") and prompt.edittype not in ("WP","WORDWRAP") or \
                (origedittype not in ("WP","WORDWRAP") and prompt.edittype in ("WP", "WORDWRAP")):
                # if changing a prompt from Wordwrap to text (or vice versa) send the whole grid
                # Most of the time this is used it's a single column grid
                return ingrid
            elif prompt.stringrepresentation != origprompt:
                # this handles other potential changes
                # currently only prompt literaly
                cmd = Command()
                cmd.addpacket(packet)
                return cmd

        return None

    def _addgrid(self, packet: WinGemPacket):
        ''' Add a grid '''
        grid = Grid()
        grid.addpacket(packet)
        self.grids.append(grid)
        grid.screenid = self.screenid
        # setup a grid id
        grid.gridid = str(self.screenid) + "_" + str(len(self.grids) - 1) + "_grid"
        return grid

    def _addtext(self, packet: WinGemPacket):
        ''' Add a prompt to the Screen '''
        text = Text()
        success = text.addpacket(packet)[0]

        if success and text.row == self.startrow and self._haswindowcaption():
            self._removeheading()
            text.makeheading()

        if success:
            text.screenid = self.screenid
            self.texts.append(text)
            return text
        else:
            # Do nothing, Text() logs issue
            pass

    def _addtitle(self, packet: WinGemPacket):
        ''' Add a title to the screen '''
        title = packet.extract(2)
        prev_title = (self.title or '').strip()
        if title:
            self.title = (title or '').strip()

        if self.iscomplete() and not self.ischild and self.title != prev_title:
            # We are the parent screen, and the main title has changed, update it
            cmd = Command()
            current_title = self.title
            if self.titleappended:
                # We had a merged heading/subheading,
                # try to remove the old title and prepend the new one
                tempheading = [text for text in self.texts if text.heading][0]
                current_title = (tempheading.tag or '').strip()

                same_index = 0
                for current_index in range(min(len(current_title), len(prev_title))):
                    if current_title[current_index] != prev_title[current_index]:
                        same_index = current_index
                        break

                if same_index > 0:
                    current_title = current_title[same_index:].strip()
                    current_title = re.sub(r"^[-\s+]+", "", current_title) #remove any kind of "-" or white space at the beginning of the string pylint: disable=line-too-long

                current_title = tempheading.tag = self.title + " - " + current_title

            cmd.updatetext(current_title, f"#{self.screenid}_heading")
            return cmd

    def _removeheading(self):
        ''' remove any screen heading '''
        for text in self.texts:
            if text.heading:
                self.texts.remove(text)

    def _addbutton(self, packet: WinGemPacket):
        ''' Add a button to the Screen '''
        retbuttons = []
        packettype = packet.packettype()

        for onebuttondef in Button.enumpackets(packet):
            matchlist = []
            button = Button()

            if packettype == "WDB":
                wdb = True
            else:
                wdb = False

            if wdb:
                # Initialize button size to current screen default
                button.setwidth(self.buttonwidth)
                button.setheight(self.buttonheight)

            success = button.addpacket(onebuttondef)[0]

            if not wdb:
                # Changing: Check for existence of button
                # Find in self.buttons
                matchlist = [pos for pos, btn in enumerate(self.buttons) if btn.name == button.name]
                if matchlist:
                    # Modify existing button
                    button = self.buttons[matchlist[0]]
                    success = button.addpacket(onebuttondef)[0]
                else:
                    # Couldn't find button to change
                    success = False

            # If fails, Button() logs issue, only continue if succeeded
            if success:
                button.screenid = self.screenid

                if button.deleted:
                    # Button is deleted; remove from collection and move on
                    try:
                        self.buttons.remove(button)
                    except ValueError:
                        # Ignore if not there
                        pass
                    # Return button so deletion command can be sent
                    retbuttons.append(button)
                    continue

                # Auto-position button
                if button.row == 0.0 and button.col == 0.0:
                    self._updatebuttontype(button, "AUTO")
                    self._screenbuttondepth += 1
                    if self.position == "FULLSCREEN":
                        button.autoposition = True
                        col = 1
                        coladjust = components.applyscaling(self._BUTTONGAPSIZE, True)
                        coladjust = coladjust / components.applyscaling(1, False)
                        coladjust = coladjust * (self._screenbuttondepth - 1)
                        col += coladjust
                        col += (self._screenbuttondepth - 1) * self.buttonwidth
                        button.col = col
                    else:
                        screenwidth = self.endcol - self.startcol + 1

                        # Base row (at bottom of screen)
                        row = self.endrow + self._BASESTARTROW
                        if self.startrow == self._BASESTARTROW + 1 and screenwidth > 79:
                            row += 1
                        if self._haswindowcaption():
                            row -= self._CAPTIONHEIGHT
                        else:
                            row -= self._NOCAPTIONHEIGHT

                        # Base column (to the right of traditional screen area)
                        col = self.endcol + 1 + self._BUTTONBARWIDTH

                        if self.buttonoptions[self._BUTTONOPTIONS_DIRECTIONNDX] == \
                                self._BUTTONOPTIONS_VERTICAL:
                            # Vertical positioning adjustment
                            row -= self._screenbuttondepth * self.buttonheight
                            row -= (self._screenbuttondepth - 1) * self._BUTTONGAPSIZE
                            button.row = row

                            col -= self.buttonwidth
                            button.col = col
                        else:
                            # Horizontal positioning adjustment
                            row -= self.buttonheight
                            button.row = row
                            coladjust = components.applyscaling(self._BUTTONGAPSIZE, True)
                            coladjust = coladjust / components.applyscaling(1, False)
                            coladjust = coladjust * (self._screenbuttondepth - 1)
                            col -= coladjust
                            col -= self._screenbuttondepth * self.buttonwidth
                            button.col = col
                else:
                    self._updatebuttontype(button, "MANUAL")

                if matchlist:
                    # Replace button
                    self.buttons[matchlist[0]] = button
                else:
                    # Attach button
                    self._attachbutton(button)

                retbuttons.append(button)

                # WinGem defaults to the first button added if it's not set
                # or set to CANCEL
                if self.defaultbutton == "CANCEL" or self.defaultbutton is None:
                    self.defaultbutton = button.name

        return retbuttons

    def _updatebuttontype(self, button, buttontype):
        ''' Perform logic when switch between types of buttons '''
        # if self._buttonlasttype != buttontype and button.name not in ("OK", "CANCEL"):
        if self._buttonlasttype != buttontype:
            self._buttonlasttype = buttontype
            self._buttoninsertpos = len(self.buttons)
        if button.name in ("OK", "CANCEL"):
            self._buttoninsertpos += 1

    def _attachbutton(self, button):
        '''
            Attach button in appropriate location in the list.
            Order added:
                1 - Manual positioned buttons before OK/CANCEL, in order received
                2 - OK/CANCEL, at beginning of stack
                3 - Manual/auto positioned buttons, in reverse of order received
        '''
        # print([button.name, self._buttoninsertpos, len(self.buttons)])
        if button.name == "OK":
            self.buttons.insert(0, button)
        elif button.name == "CANCEL":
            if self.buttons:
                if self.buttons[0].name == "OK":
                    self.buttons.insert(1, button)
                else:
                    self.buttons.insert(0, button)
            else:
                self.buttons.append(button)
        elif self._buttoninsertpos == 0:
            self.buttons.append(button)
        else:
            self.buttons.insert(self._buttoninsertpos, button)

    def _haswindowcaption(self):
        ''' Determine if window has a caption '''
        return self.boxtype != ""

    def _addokbutton(self):
        ''' Build packet for OK button and add to screen '''
        # See frmWGMain.ScreenAdd
        optionslist = list("C")
        optionslist.append(resource.loadstring("IDS_CAP0001"))  # "OK"
        optionslist.append("E")
        optionslist.append("F2")
        optionslist.append("")
        optionslist.append("Y")
        optionslist.append("")
        optionslist.append("")
        optionslist.append("OK")
        optionslist.append("")
        optionslist.append("")
        optionslist.append("")
        optionslist.append("")
        optionslist.append(str(self.buttonheight))
        optionslist.append(str(self.buttonwidth))
        optionsstring = (WinGemPacket.VM).join(optionslist)
        buttonpacket = (WinGemPacket.AM).join(("WDB", "", optionsstring))
        self._addbutton(WinGemPacket(buttonpacket))
        self.defaultbutton = "OK"

    def _addcancelbutton(self, canceltype):
        ''' Build packet for Cancel button and add to screen '''
        # frmWGMain.ScreenAdd, watch Cancel vs Close

        if canceltype == self._BUTTONOPTIONS_CLOSE:
            buttontext = resource.loadstring("IDS_CAP0067")  # "Close"
        else:
            buttontext = resource.loadstring("IDS_CAP0006")  # "Cancel"

        buttontext = html.unescape(buttontext)

        optionslist = list("C")
        optionslist.append(buttontext)
        optionslist.append("E")
        optionslist.append("F4")
        optionslist.append("")
        optionslist.append("Y")
        optionslist.append("")
        optionslist.append("")
        optionslist.append("CANCEL")  # Named "CANCEL" regardless of text
        optionslist.append("")
        optionslist.append("")
        optionslist.append("")
        optionslist.append("")
        optionslist.append(str(self.buttonheight))
        optionslist.append(str(self.buttonwidth))
        optionsstring = (WinGemPacket.VM).join(optionslist)
        buttonpacket = (WinGemPacket.AM).join(("WDB", "", optionsstring))
        self._addbutton(WinGemPacket(buttonpacket))
        self.defaultbutton = "CANCEL"

    def getprompt(self, promptnum: int):
        ''' return prompt that matches prompt num '''
        promptmatches = [prompt for prompt in self.prompts if prompt.promptnum == promptnum]
        if promptmatches:
            return promptmatches[0]
        else:
            return None

    def finishscreen(self):
        ''' Do some cleanup on screen '''
        self._complete = True

        hasheading = [text for text in self.texts if text.heading]
        # update heading, as it sometimes is not set correctly
        if CONFIG["PRODUCT"] == "AXIS":
            # just want to know if it has a heading
            self.hasheading = (hasheading and hasheading[0].tag)
        hassinglebrowser = (sum([1 if prompt.edittype == "BROWSER" else 0
                                 for prompt in self.prompts]) == 1)

        if not self.ischild and \
           (self.title or self.position != "FULLSCREEN" or CONFIG["PRODUCT"] == "GoldCare"):
            # don't automatically add a heading to FULLSCREEN screens
            if not hasheading:
                if not self.boxtype:
                    # Make a box
                    if self.startrow > 0:
                        self.startrow -= 1

                    # WinGem treats screens starting @ 3 different than other start points
                    heightmodifier = 0
                    if self.startrow == Screen._BASESTARTROW and \
                            (self.endcol - self.startcol + 1) > 79:
                        heightmodifier = 1
                    else:
                        self.startrowdraw = max(self.startrow - Screen._BASESTARTROW, 0)

                    self.height = (self.endrow - self.startrow +
                                   Screen._BASESTARTROW + heightmodifier)
                    self.height = components.applyscaling(self.height, True)

                temptext = Text()
                if self.title:
                    temptext.tag = self.title
                    self.titleappended = True
                else:
                    temptext.tag = CONFIG['PRODUCT']
                temptext.screenid = self.screenid
                temptext.makeheading()
                temptext.row = self.startrow
                temptext.col = self.startcol
                self.texts.append(temptext)
            elif self.title and not self.titleappended:
                tempheading = hasheading[0]
                searchvalue = tempheading.tag[:30]
                searchvalue = searchvalue[:searchvalue.find(" (")].strip()

                if self.title.find(searchvalue) == -1:
                    tempheading.tag = self.title + " - " + tempheading.tag
                else:
                    tempheading.tag = self.title
                self.titleappended = True
        elif self.boxtype and not hasheading:
            temptext = Text()
            temptext.screenid = self.screenid
            temptext.makeheading()
            temptext.row = self.startrow
            temptext.col = self.startcol
            self.texts.append(temptext)

        # determine number of prompts that are not displayed
        undisplayed = sum([1 if (prompt.prompttype == "M" or
                                 prompt.prompttype == "X" or
                                 prompt.displaywidth <= 0 or
                                 not (prompt.datarow >= 0 and
                                      prompt.datarow <= self.endrow and
                                      prompt.datacol >= 0)
                                 )
                           else 0 for prompt in self.prompts])
        offset = self.startcol > 0 or self.startrow > 3

        # check to see if we have a single (displayed) browser prompt
        if hassinglebrowser and not (offset
                                     or self.buttons
                                     or (len(self.prompts) != 1
                                         and undisplayed != (len(self.prompts) - 1))):
            # fix screen to be maximal size and prompt to fill all
            self.prompts[0].fullscreen = True
            self.fillcontainer = True

            if not hasheading and self.startrow <= 3:
                self.startrowdraw = 0
                self.prompts[0].datarow = self.startrow
        elif self.position == "FULLSCREEN":
            # Single browser, flagged fullscreen,
            # likely a screen with just a browser and buttons, fullscreen it
            if hassinglebrowser and (
                    len(self.prompts) == 1 or undisplayed == (len(self.prompts) - 1)):
                self.prompts[0].fullscreen = True
                if not hasheading and self.startrow <= 3:
                    self.startrowdraw = 0
                    self.prompts[0].datarow = self.startrow
            else:
                # Recalc hasheading
                hasheading = [text for text in self.texts if text.heading]
                if hasheading and not self.hasheading:
                    self.startrow += 1
                    self.hasheading = True
