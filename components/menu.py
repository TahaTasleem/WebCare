'''
Created on Nov 15, 2016

@author: rosenada
'''
import logging
from _collections import OrderedDict
from components.wdobject import BaseWDObject
from connector.wingempacket import WinGemPacket
from connector import resource

class MenuItem():
    '''
        This represents a single menu item/link
        from axis or goldcare
    '''
    def __init__(self, menutext, menuicon, menuindex):
        self.menutext = menutext
        self.menuindex = menuindex
        self.menuicon = menuicon

class MenuSection():
    '''
        Represents a collection of menu items
    '''
    def __init__(self, sectiontitle):
        self.title = sectiontitle
        self.menuitems = []



class MenuObject(BaseWDObject):
    '''
    Object representing a WinGem menu
    '''
    _MENUPACKETS = ["WN"]
    ICONLIST = {
        "-1":{"icon":"folder.svg"},
        "-2":{"icon":"program.svg"},
        "-3":{"icon":"table.svg"},
        "-4":{"icon":"report.svg"}
    }
    #===========================================================================
    # JHO: Not sure if -3 or -4 are ever sent
    # Haven't found a case, yet, and interestingly all report items
    #   seem to send a reference to custom "REPORTMENUITEM.ICO" rather than -4
    #===========================================================================



    def __init__(self):
        ''' Create the empty list of sections '''
        super(MenuObject, self).__init__("MENU")
        self.executelevel = 0
        self.calllevel = 0
        self.mainmenutitle = ""
        self.menuitemtitles = []
        self.menuitemsections = []
        self.iconindex = []
        self.customicons = []
        self.sections = OrderedDict()
        self.menuoptionnum = []
        self.haschildmenu = []

    def getid(self):
        ''' return calculated menu id as per GUI Command doc'''
        return (self.executelevel * 1000) + self.calllevel


    def parsewn(self, packet: WinGemPacket):
        ''' Parse WN Packet into properties '''
        try:
            self.executelevel = int(packet.extract(2))
            self.calllevel = int(packet.extract(3))
            self.mainmenutitle = packet.extract(4)
            self.menuitemtitles = packet.extractaslist(5)
            self.menuitemsections = packet.extractaslist(8)
            self.iconindex = packet.extractaslist(11)
            self.customicons = packet.extractaslist(12)
            self.menuoptionnum = packet.extractaslist(13)
            self.haschildmenu = packet.extractaslist(16)

            # additional stuff going on here in case there was no info returned; we still want
            # values for these things
            if len(self.menuitemsections) != len(self.menuitemtitles):
                # if there are no extra sections, as is the case with some/most/all SX style menus
                # fill in their MenuSection text, so it can sort them into the same single one
                # probably a better way to do this, but it works in both cases where sections
                # are and arent a thing.
                # create the section list as the same section as the main title text
                self.menuitemsections = [self.mainmenutitle] * len(self.menuitemtitles)

            if not self.menuoptionnum:
                # no menu option text received, as is the case with some/most/all sx style menus
                # fill in their menu option
                # range returns a range() object, pass it into list() to have it be a true
                # [1,2,3,4,...] form. Start the list at 1 because host is 1 based as per usual
                self.menuoptionnum = list(range(1, len(self.menuitemtitles) + 1))

            if self.haschildmenu == []:
                # if they(goldcare) dont send the new field whether or not it contains child
                # menus or not then create list assuming they menus
                self.haschildmenu = ["1"] * len(self.menuitemtitles)

            # if we dont have menu items, dont even bother
            # cant do just a if not self.menuitemtitles because
            # the list here isnt actually empty/not exist (grr), so i
            # have to actually check that it just same a single empty element.
            # [] would be empty vs [''] is filled, just with an empty string.
            if self.menuitemtitles == ['']:
                self._complete = True
                return

            # add the first element no matter what
            # .pop()'s are bad according to some page JHOe read
            tsectiontitle = self.menuitemsections.pop(0)
            self.sections[tsectiontitle] = MenuSection(tsectiontitle)
            self.sections.get(tsectiontitle).menuitems.append(
                MenuItem(self.menuitemtitles.pop(0).replace("^", ""),
                         self.geticon(self.iconindex.pop(0), self.haschildmenu.pop(0)),
                         self.menuoptionnum.pop(0)))
            # loop through the remainder of the lists
            for sectionndx, sectiontext in enumerate(self.menuitemsections):
                menuiconindex = self.iconindex[sectionndx]
                menutext = self.menuitemtitles[sectionndx].replace("^", "")
                menuoption = self.menuoptionnum[sectionndx]
#                 logging.debug("Current Menu Item: " + menutext + "/" + sectiontext)
                # lookup the current MenuSection in our dict
                if not self.sections.get(sectiontext):
                    # if it's not there, add it to the list with its item.
#                     logging.debug("Creating MenuSection " + sectiontext +
#                                   " with menu item " + menutext)
                    self.sections[sectiontext] = MenuSection(sectiontext)
                    self.sections.get(sectiontext).menuitems.append(
                        MenuItem(menutext,
                                 self.geticon(menuiconindex, self.haschildmenu[sectionndx]),
                                 menuoption))
                else:
                    # otherwise, it's there, so add the menu item to its list.
#                     logging.debug(sectiontext + " already exists, adding " + \
#                                   menutext + " to " + sectiontext)
                    self.sections.get(sectiontext).menuitems.append(
                        MenuItem(menutext,
                                 self.geticon(menuiconindex, self.haschildmenu[sectionndx]),
                                 menuoption))



            self._complete = True
        except (ValueError, IndexError):
            logging.error("Error creating menu from packet - " + packet.stringify())
            self._complete = False

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Handles a single menu packet'''
        handlepacket = False
        if packet.packettype() in MenuObject._MENUPACKETS:
            self.parsewn(packet)
            handlepacket = True

        return handlepacket, None, self

    def geticon(self, iconvalue, haschildmenu):
        '''
            Returns the icon full file name
            If the icon is a default value (val < 0 it seems), it will look it up in the
            list ICONLIST
            If the icon is not a default value (val > 0), it will return the corresponding indexes
            text that is in the packet
        '''
        iconobj = self.ICONLIST.get(iconvalue)
        if not iconobj:
            iconstr = resource.loadimage(self.customicons[int(iconvalue) - 1])
        else:
            iconstr = resource.loadimage(iconobj.get("icon"))
        if iconstr == "":
            if haschildmenu == "1":
                iconstr = resource.loadimage(self.ICONLIST.get("-1").get("icon"))
            else:
                iconstr = resource.loadimage(self.ICONLIST.get("-2").get("icon"))
        return iconstr
