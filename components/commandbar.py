'''
Created on Nov 24, 2016

@author: holthjef
'''
import logging
import html
import posixpath
from components.button import Button
from components.wdobject import BaseWDObject
from connector import resource
from connector.wingempacket import WinGemPacket
from connector.configuration import CONFIG


class CommandBarTool(Button):
    ''' A Command Bar Tool '''

# Tools belong to their own list AND to whatever band(s) they are attached to

    def __init__(self):
        ''' Constructor '''
        super().__init__("COMMANDBARTOOL")
        self._cacheable = True

        self.image = ""
        self.menupath = ""
        self.toolbar = ""
        self._menubar = "bndMenuStandard"
        self._accelerator = ""  # Application global key, eg. F1, CTRL+G, ...
        # Underlined character in menu option, button tag, prompt label, etc.
        self._shortcut = ""
        self.toolpos = ""
        self.menupos = ""
        self.begingroup = False
        self.subband = ""
        self.specialcmd = ""
        self.visible = True
        self.parents = {}
        self._complete = True

        # Inherited:
#         self.type = ""
#         self.tag = ""
#         self.sendtype = ""
#         self.sendtext = ""
#         self.help = ""
#         self.enabled = True
#         self.checked = False
#         self.row = 0.0
#         self.col = 0.0
#         self.name = ""
#         self.height = self.DEFAULTBUTTONHEIGHT
#         self.width = self.DEFAULTBUTTONWIDTH
#         self.filename = ""
#         self.screenid = "500"
#         self.stringrepresentation = ""
#         self.options = {}

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Configure Command Bar Tool object from WinGem WDT or WCT packet '''

        success = False
        packettype = packet.packettype()

        if packettype in ("WDT", "WCT"):
            if packettype == "WDT":
                wdt = True
                defpos = 3
            else:
                wdt = False
                defpos = 2

            try:
                self.stringrepresentation = packet.stringify()

                newtype = packet.extract(defpos, 1)
                if newtype or wdt:
                    self.type = newtype

                newimage = packet.extract(defpos, 2)
                if newimage or wdt:
                    if newimage and newimage[0] != chr(27):
                        self.origfilename = newimage
                    else:
                        _, newoptions = packet.parseoptions(defpos, 2)
                        self.options = newoptions
                        # Extract filename
                        self.origfilename = self.options.get("img", "")
                    self.filename = resource.loadimage(self.origfilename)

                newsendtype = packet.extract(defpos, 3)
                if newsendtype or wdt:
                    self.sendtype = newsendtype

                newsendtext = packet.extract(defpos, 4)
                if newsendtext or wdt:
                    self.sendtext = newsendtext

                newhelp = packet.extract(defpos, 5)
                if newhelp or wdt:
                    self.help = newhelp

                newenabled = packet.extract(defpos, 6)
                if newenabled or wdt:
                    if newenabled == "Y":
                        self.enabled = True
                    elif newenabled == "N":
                        self.enabled = False
                    elif newenabled == "H":
                        self.visible = False
                    elif newenabled == "U":  # Unhide
                        self.visible = True
                    elif newenabled == "X":
                        self.deleted = True

                newname = packet.extract(defpos, 9)
                if newname or wdt:
                    self.name = newname

                newmenupath = packet.extract(defpos, 10)
                if newmenupath or wdt:
                    self.menupath = newmenupath
                    self.tag, self._shortcut = resource.removehotkey(
                        self.menupath.split("/")[-1])

                newtoolbar = packet.extract(defpos, 11)
                if newtoolbar or wdt:
                    self.toolbar = newtoolbar
                    if self.toolbar and self.toolbar[:3] != "bnd":
                        self.toolbar = "".join(["bnd", self.toolbar])

                # CommandBar: Handle accelerator
                newaccelerator = packet.extract(defpos, 12)
                if newaccelerator or wdt:
                    self._accelerator = newaccelerator

                newtoolpos = packet.extract(defpos, 16)
                if newtoolpos or wdt:
                    self.toolpos = newtoolpos

                newmenupos = packet.extract(defpos, 17)
                if newmenupos or wdt:
                    self.menupos = newmenupos

                # Show a separator before this item (above or to the left)
                newbegingroup = packet.extract(defpos, 18)
                if newbegingroup or wdt:
                    self.begingroup = newbegingroup == "Y"

                # Calculate name and tag overrides on WDT only
                if wdt:
                    # Use filename or menu item name if name not specified
                    if self.name == "":
                        #=======================================================================
                        # Filenames from resource module use POSIX/URI-style separators
                        # Naming may cause issues when filename used as name
                        #   and is an ico translated to an svg
                        #=======================================================================
                        # self.name = self.origfilename.split(posixpath.sep)[-1]
                        self.name = self.filename.split(posixpath.sep)[-1]
                    if self.name == "":
                        self.name = self.tag
                    if self.tag == "":
                        self.tag = self.name

                # Prefix name with "att" for both WDT and WCT
                self.name = "".join(["att", self.name])
                if self.name == "attCommandLine":
                    self.specialcmd = "WD.toggletcl();"
                if self.name == "attEnable Log":
                    self.specialcmd = "WD.toggleLogs();"
                if self.name == "attDownload Log":
                    self.specialcmd = "WD.viewLogs();"

                if not (self.tag == "" and self.filename == "" and packettype == "WDT"):
                    # Don't error if "WCT"
                    success = True
            except Exception:  # pylint:disable = broad-except
                logging.error(" ".join(["CommandBarTool failed to parse", packettype,
                                        "packet:", self.stringrepresentation]))

        return success, None, self

    def getid(self):
        ''' override getid '''
        return "COMMANDBAR_TOOL_" + self.name.replace(" ", "_").replace("&", "")


class CommandBarBand(object):
    ''' A Command Bar '''

    # May need to change these constants to something else
    BANDTYPEMENU = "MENU"
    BANDTYPETOOLBAR = "TOOLBAR"
    BANDTYPEPOPUP = "POPUP"

    def __init__(self):
        ''' Constructor '''
        self._type = "COMMANDBARBAND"
        self._cacheable = True
        self._complete = True
        self.tools = []
        self.tag = ""
        self.bandtype = self.BANDTYPEPOPUP
        self.name = ""
        self.offsethead = 0
        self.offsettail = 0

    def inserttool(self, tool: CommandBarTool, position: str = None):
        ''' Insert Tool into Band '''
        # success = False

        tool.parents[self.getid()] = self

        # Search for the tool in this band
        if self.tools:
            matchlist = [pos for pos, node in enumerate(
                self.tools) if node.name == tool.name]
        else:
            matchlist = []
        # Does the tool already exist?
        if matchlist:
            # Replace tool
            self.tools[matchlist[0]] = tool
        else:
            if position is None:
                if self.bandtype == self.BANDTYPETOOLBAR:
                    position = tool.toolpos
                else:
                    # If a positional path is given, WinGem seems to treat it as "add to the tail"
                    position = tool.menupos
                    if "/" in position:
                        position = ""

            tailindex = len(self.tools) - self.offsettail
            if position == "":
                toolindex = tailindex
            elif position[0] == "A":
                toolindex = int(position[1:])
                toolindex -= 1  # Convert from 1- to 0-base
                tailindex = len(self.tools)
            else:
                toolindex = self.offsethead + int(position)
                toolindex -= 1  # Convert from 1- to 0-base

            if toolindex > tailindex:
                toolindex = tailindex

            if toolindex < 0:
                toolindex = 0

            #===================================================================
            # if self.tag == "Standard":
            #     print("")
            #     print("position  : " + position)
            #     print("tailindex : " + str(tailindex))
            #     print("toolindex : " + str(toolindex))
            #     print("offsethead: " + str(self.offsethead))
            #     print("offsettail: " + str(self.offsettail))
            #===================================================================

            # Update offsets (inserting shifts right)
            if toolindex < self.offsethead:
                self.offsethead += 1
            if toolindex > len(self.tools) - self.offsettail:
                self.offsettail += 1

            self.tools.insert(toolindex, tool)

        success = True

        return success, None

    def gettoolclientpos(self, targettool: CommandBarTool):
        ''' Find position of tool in tools list '''

        #=======================================================================
        # # This should work EXCEPT that separators take up slots in the DOM
        # try:
        #     ndx = [tool.name for tool in self.tools].index(targettool.name)
        # except ValueError:
        #     ndx = -1
        # return ndx
        #=======================================================================
        try:
            ndx = [tool.name for tool in self.tools].index(targettool.name)
            head = self.tools[:ndx]
            sepcnt = len([tool.name for tool in head if tool.begingroup])
            ndx = ndx + sepcnt
            if self.bandtype == self.BANDTYPEMENU and CONFIG['PRODUCT'] == "AXIS":
                # Add one to account for application icon in top left of WebDirect window
                ndx += 1
        except ValueError:
            ndx = -1
        return ndx

    def getid(self):
        ''' override getid '''
        return "COMMANDBAR_BAND_" + self.name.replace(" ", "_").replace("&", "")


class CommandBar(BaseWDObject):
    ''' A Command Bar '''

#    DEFAULTBUTTONHEIGHT = 1.35
#    DEFAULTBUTTONWIDTH = 1.35

    _MENUSTANDARD = "bndMenuStandard"
    _TOOLBARSTANDARD = "bndToolbarStandard"
    _TOOLBARDEBUG = "bndToolbarDebug"
    _POPUPHELP = "bndPopupHelp"
    _POPUPWINDOW = "bndPopupWindow"
    _POPUPVIEW = "bndPopupView"
    _POPUPSESSION = "bndPopupSession"
    _POPUPCOMMAND = "bndPopupCommands"
    _TYPEMENUITEM = "M"
    _TYPETOOL = "T"

    def __init__(self, enable_logging = False):
        ''' Constructor '''
        super(CommandBar, self).__init__("COMMANDBAR")
        self._cacheable = True
        self.enable_logging = enable_logging

#         self.type = ""
#         self.tag = ""
#         self.sendtype = ""
#         self.sendtext = ""
#         self.help = ""
#         self.enable = ""
#         self.row = 0.0
#         self.col = 0.0
#        self.name = ""
#        self.height = self.DEFAULTBUTTONHEIGHT
#        self.width = self.DEFAULTBUTTONWIDTH
#         self.filename = ""
#         self.screenid = "500"
#         self.stringrepresentation = ""
#         self.options = {}
        self._reset()
        self._complete = True

    def _reset(self):
        ''' Clear items from commandbar and re-apply defaults '''
        self.bands = {}
        self._tools = {}
        self._builddefault()

    def _builddefault(self):
        ''' Create default components '''

        # CommandBar: Accelerator keys
        # should eventually be changed to use numeric sequences as defined in GUICommandSet

        # Create Menu Bar
        self._addband(self._MENUSTANDARD, CommandBarBand.BANDTYPEMENU)

        # Create Standard Toolbar
        self._addband(self._TOOLBARSTANDARD, CommandBarBand.BANDTYPETOOLBAR, None,
                      resource.loadstring("IDS_CAP0054"))

        if CONFIG['PRODUCT'] == "AXIS":
            # Create Debug Toolbar
            self._addband(self._TOOLBARDEBUG, CommandBarBand.BANDTYPETOOLBAR, None,
                          resource.loadstring("IDS_CAP0060"))
            # Create and Link Session Popup
            self._addband(self._POPUPSESSION, CommandBarBand.BANDTYPEPOPUP,
                          "attSession", resource.loadstring("IDS_CAP0051"),
                          self.bands[self._MENUSTANDARD])
        else:
            # Build CancelUp button on main toolbar
            buttonpacket = self._createbuttonpacket(tooltype=self._TYPETOOL,
                                                    toolimg="".join(
                                                        (chr(27), "<img=gcuptool.svg >")),
                                                    toolsendtype="E",
                                                    toolsendtext="F4",
                                                    toolhelp=resource.removehotkey(
                                                        resource.loadstring("IDS_CAP0055"))[0],
                                                    toolenabled="Y",
                                                    toolname="CancelUp",
                                                    tooltoolbar=self._MENUSTANDARD,
                                                    toolaccelerator="F4")
            self.addpacket(WinGemPacket(buttonpacket))


        window_string = html.unescape( resource.loadstring("IDS_CAP0052") )
        help_string = resource.loadstring("IDS_CAP0053")
        view_string = resource.loadstring("IDS_CAP0058")

        if CONFIG['PRODUCT'] == "AXIS":
            # Create and Link Window Popup
            self._addband(self._POPUPWINDOW, CommandBarBand.BANDTYPEPOPUP,
                          "attWindow", window_string,
                          self.bands[self._MENUSTANDARD])

            # CommandBar: Replace CancelUp with Cancel and Up tools
            # Build CancelUp button
            buttonpacket = self._createbuttonpacket(tooltype=self._TYPETOOL,
                                                    toolimg="".join(
                                                        (chr(27), "<img=uptool.ico >")),
                                                    toolsendtype="E",
                                                    toolsendtext="F4",
                                                    toolhelp=resource.removehotkey(
                                                        resource.loadstring("IDS_CAP0055"))[0],
                                                    toolenabled="Y",
                                                    toolname="CancelUp",
                                                    toolmenupath="".join(
                                                        (f"{window_string}/",
                                                         resource.loadstring("IDS_CAP0055"))),
                                                    toolaccelerator="F4")
            self.addpacket(WinGemPacket(buttonpacket))

            # Create View Popup _POPUPVIEW
            self._addband(self._POPUPVIEW, CommandBarBand.BANDTYPEPOPUP,
                          "attView", view_string,
                          self.bands[self._POPUPWINDOW], True)

            # Create Help Popup _POPUPHELP
            self._addband(self._POPUPHELP, CommandBarBand.BANDTYPEPOPUP,
                          "attHelp", help_string,
                          self.bands[self._MENUSTANDARD])
        else:
            # Create Help Popup _POPUPHELP
            self._addband(self._POPUPHELP, CommandBarBand.BANDTYPEPOPUP,
                          "attHelp", help_string,
                          self.bands[self._MENUSTANDARD], False, resource.loadimage("gchelp.ico"))

        # Build Context Sensitive Help (AXIS Help / GoldCare Help) button
        # sends <esc>F1 if in screen, or ?<option#> if a menu item is highlighted
        # (current menu option #, not full path)
        if CONFIG['PRODUCT'] == "AXIS":
            caption = resource.loadstring("IDS_CAP0074")
        else:
            caption = resource.loadstring("IDS_CAP0075")
        buttonpacket = self._createbuttonpacket(tooltype=self._TYPETOOL,
                                                toolimg="".join(
                                                    (chr(27), "<img=HELP.ICO >")),
                                                toolhelp=resource.removehotkey(help_string)[0],
                                                toolenabled="Y",
                                                toolname="ContextSensitive",
                                                toolmenupath="".join(
                                                    (f"{help_string}/", caption)),
                                                toolaccelerator="F1")
        self.addpacket(WinGemPacket(buttonpacket))
        self._tools["attContextSensitive"].specialcmd = "WD.sendContextHelp();"

        # Build Log buttons
        if CONFIG['PRODUCT'] == "AXIS":
            menupath = ""
            toolbar = self._TOOLBARDEBUG
            buttonpacket = self._createbuttonpacket(tooltype=self._TYPETOOL,
                                                    toolimg="".join(
                                                        (chr(27), "<img=log_start.svg >")),
                                                    toolhelp=resource.removehotkey(
                                                        resource.loadstring("IDS_CAP0142"))[0],
                                                    toolenabled="Y",
                                                    toolname="Enable Log",
                                                    toolmenupath=menupath,
                                                    tooltoolbar=toolbar,
                                                    toolbegingroup="Y")
            self.addpacket(WinGemPacket(buttonpacket))
            self._tools["attEnable Log"].specialcmd = "WD.toggleLogs();"

            buttonpacket = self._createbuttonpacket(tooltype=self._TYPETOOL,
                                                    toolimg="".join(
                                                        (chr(27), "<img=download_file.svg >")),
                                                    toolhelp=resource.removehotkey(
                                                        resource.loadstring("IDS_CAP0143"))[0],
                                                    toolenabled="Y",
                                                    toolname="Download Log",
                                                    toolmenupath=menupath,
                                                    tooltoolbar=toolbar)
            self.addpacket(WinGemPacket(buttonpacket))
            self._tools["attDownload Log"].specialcmd = "WD.viewLogs();"

        # Build About WinGem button
        toolhelp = " ".join((resource.removehotkey(
            resource.loadstring("IDS_CAP002"))[0], "WinGem"))
        buttonpacket = self._createbuttonpacket(tooltype=self._TYPEMENUITEM,
                                                toolhelp=toolhelp,
                                                toolenabled="Y",
                                                toolname="AboutWinGem",
                                                toolmenupath="".join((
                                                    f"{help_string}/",
                                                    resource.loadstring("IDS_CAP0002"),
                                                    " ",
                                                    CONFIG['PRODUCT'])),
                                                toolaccelerator="F1",
                                                toolbegingroup="Y")
        self.addpacket(WinGemPacket(buttonpacket))
        self._tools["attAboutWinGem"].specialcmd = "WD.about();"

        # Build Command Line... button
        if CONFIG['PRODUCT'] == "AXIS":
            menupath = "".join(
                (f"{window_string}/{view_string}/", resource.loadstring("IDS_CAP0059")))
            buttonpacket = self._createbuttonpacket(tooltype=self._TYPEMENUITEM,
                                                    toolhelp=resource.removehotkey(
                                                        resource.loadstring("IDS_CAP0059"))[0],
                                                    toolenabled="Y",
                                                    toolname="CommandLine",
                                                    toolmenupath=menupath,
                                                    toolaccelerator="CTRL+F4")
            self.addpacket(WinGemPacket(buttonpacket))
            self._tools["attCommandLine"].specialcmd = "WD.toggletcl();"

        # Add logout button
        if CONFIG['PRODUCT'] == "GoldCare":
            buttonpacket = self._createbuttonpacket(tooltype=self._TYPETOOL,
                                                    toolimg="".join(
                                                        (chr(27), "<img=logout.ico >")),
                                                    toolhelp="Logout",
                                                    toolname="Logout",
                                                    tooltoolbar=self._MENUSTANDARD)
            self.addpacket(WinGemPacket(buttonpacket))
            self._tools["attLogout"].specialcmd = "WD.requestlogout();"

        #=======================================================================
        # # Build Disable Disconnect button
        # optionslist = list(self._TYPEMENUITEM)  # 1, Type
        # optionslist.append("")  # 2, Image
        # optionslist.append("")  # 3, Send Type
        # optionslist.append("")  # 4, Send Text
        # optionslist.append(resource.removehotkey(resource.loadstring("IDS_CAP0063"))[0]) # 5, Help
        # optionslist.append("Y")  # 6, Enabled (Y/N)
        # optionslist.append("")  # 7, Unused
        # optionslist.append("")  # 8, Unused
        # optionslist.append("DisableDisconnect")  # 9, Name
        # # 10, Menupath
        # optionslist.append("".join(("&Session/", resource.loadstring("IDS_CAP0063"))))
        # optionslist.append("")  # 11, Toolbar
        # optionslist.append("")  # 12, accelerator key
        # optionslist.append("")  # 13, Unused
        # optionslist.append("")  # 14, Unused
        # optionslist.append("")  # 15, Unused
        # optionslist.append("")  # 16, toolpos
        # optionslist.append("")  # 17, menupos
        # optionslist.append("")  # 18, begin group
        # optionsstring = (WinGemPacket.VM).join(optionslist)
        # buttonpacket = (WinGemPacket.AM).join(("WDT", "", optionsstring))
        # self.addpacket(WinGemPacket(buttonpacket))
        #=======================================================================

        # Set insertion points for host added elements
        if CONFIG['PRODUCT'] == "AXIS":
            self.bands[self._MENUSTANDARD].offsethead = 1
            self.bands[self._MENUSTANDARD].offsettail = 2
        else:
            self.bands[self._MENUSTANDARD].offsethead = 1
            self.bands[self._MENUSTANDARD].offsettail = 2
        self.bands[self._TOOLBARSTANDARD].offsethead = 1
        self.bands[self._TOOLBARSTANDARD].offsettail = 1
        if CONFIG['PRODUCT'] == "AXIS":
            # Was 1 w/Disable Disconnect
            self.bands[self._POPUPSESSION].offsethead = 0
            self.bands[self._POPUPSESSION].offsettail = 0
            self.bands[self._TOOLBARDEBUG].offsethead = 0
            self.bands[self._TOOLBARDEBUG].offsettail = 1
            self.bands[self._POPUPVIEW].offsethead = 1
            self.bands[self._POPUPVIEW].offsettail = 0
            self.bands[self._POPUPWINDOW].offsethead = 1
            self.bands[self._POPUPWINDOW].offsettail = 1
        self.bands[self._POPUPHELP].offsethead = 1
        self.bands[self._POPUPHELP].offsettail = 1

    def _addband(self,
                 bandname: str,
                 bandtype: str,
                 toolname: str = None,
                 tooltag: str = None,
                 parent: CommandBarBand = None,
                 begingroup: bool = False,
                 toolimg: str = None):
        ''' Add band and link it to parent '''
        # Create Band
        band = CommandBarBand()
        band.name = bandname
        band.bandtype = bandtype
        if tooltag:
            band.tag = resource.removehotkey(tooltag)[0]
        self.bands[bandname] = band

        # Link Band to Parent if all necessary parameters passed (Yay De Morgan's!)
        if not(toolname is None or (tooltag is None and toolimg is None) or parent is None):
            tool = CommandBarTool()
            tool.name = toolname
            tool.tag = tooltag
            tool.filename = toolimg
            tool.subband = band.name
            tool.begingroup = begingroup
            self._tools[toolname] = tool
            parent.inserttool(tool)

    def _createbuttonpacket(self,
                            tooltype: str,
                            toolimg: str = "",
                            toolsendtype: str = "",
                            toolsendtext: str = "",
                            toolhelp: str = "",
                            toolenabled: str = "",
                            toolname: str = "",
                            toolmenupath: str = "",
                            tooltoolbar: str = "",
                            toolaccelerator: str = "",
                            toolpos: str = "",
                            toolmenupos: str = "",
                            toolbegingroup: str = ""):

        # Create a button packet for a tool
        optionslist = list(tooltype)
        optionslist.append(toolimg)
        optionslist.append(toolsendtype)
        optionslist.append(toolsendtext)
        optionslist.append(toolhelp)
        optionslist.append(toolenabled)
        optionslist.append("")  # 7, Unused
        optionslist.append("")  # 8, Unused
        optionslist.append(toolname)
        optionslist.append(toolmenupath)
        optionslist.append(tooltoolbar)
        optionslist.append(toolaccelerator)
        optionslist.append("")  # 13, Unused
        optionslist.append("")  # 14, Unused
        optionslist.append("")  # 15, Unused
        optionslist.append(toolpos)
        optionslist.append(toolmenupos)
        optionslist.append(toolbegingroup)
        optionsstring = (WinGemPacket.VM).join(optionslist)
        return (WinGemPacket.AM).join(("WDT", "", optionsstring))

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Configure CommandBar object from WinGem WDT/WCT or WTB packet '''

        success = False
        packettype = packet.packettype()
        retobj = None

        if packettype == "WTB":
            success, retobj = self._processtoolbarpacket(packet)
        elif packettype in ("WDT", "WCT"):
            success, retobj = self._processbuttonpacket(packet)

        return success, None, retobj

    def _processtoolbarpacket(self, packet: WinGemPacket):
        ''' Configure CommandBar object from WinGem WTB packet '''

        success = True

        if packet.extract(2).upper() == "RESET":
            self._reset()

        return success, self

    def _processbuttonpacket(self, packet: WinGemPacket):
        ''' Configure CommandBar object from WinGem WDT or WCT packet '''

        success = True  # Setting to false results in catastrophic loss of other buttons
        packetlist = []
        packettype = packet.packettype()
        tools = []

        # Could probably us a map (and maybe lambda) here
        if packettype == "WDT":
            for buttondef in WinGemPacket(packet.extractfrom(3)).extractaslist():
                packetlist.append(WinGemPacket(
                    (WinGemPacket.AM).join([packettype, "", buttondef])))
        else:
            for buttondef in WinGemPacket(packet.extractfrom(2)).extractaslist():
                packetlist.append(WinGemPacket(
                    (WinGemPacket.AM).join([packettype, buttondef])))

        for packet in packetlist:
            try:
                tool = CommandBarTool()

                if tool.addpacket(packet)[0]:
                    if tool.deleted:
                        self._removetool(tool)
                    else:
                        if tool.name in self._tools:
                            if packettype == "WDT":
                                # Replace tool
                                self._tools[tool.name] = tool
                            else:
                                # Update tool
                                tool = self._tools[tool.name]
                                tool.addpacket(packet)
                        else:
                            if packet.packettype() == "WCT":
                                # Ignore failure on default items no longer included
                                if tool.name != "attExit":
                                    # Fail if can't find tool to change
                                    raise IndexError
                                tool = None
                            else:
                                self._tools[tool.name] = tool
                else:
                    raise Exception # pylint: disable=W0719

                if tool:
                    if tool.deleted:
                        tools.append(tool)
                    else:
                        tools.append(self._attachtool(tool))

                    if tool.name == "attEnable Log" and self.enable_logging:
                        # if log is enabled icon and text should be shown for disable log
                        tool.help = tool.tag = resource.loadstring("IDS_WEB0003") or "Disable Log"
                        tool.filename = tool.filename.replace("log_start.svg", "log_stop.svg")

            except IndexError:
                tool = None
                logging.error(" ".join(["CommandBar failed to find tool", packettype,
                                        "packet:", packet.stringify()]))

            except Exception:  # pylint:disable = broad-except
                tool = None
                logging.error(" ".join(["CommandBar failed to parse", packettype,
                                        "packet:", packet.stringify()]))

        return success, tools

    def _attachtool(self, tool: CommandBarTool):
        ''' Attach tool to band and collection '''
        newbandtool = None
        window_string = html.unescape(resource.loadstring("IDS_CAP0052"))

        if tool.menupath:
            band = self.bands[self._MENUSTANDARD]
            levels = tool.menupath.split("/")
            for levelndx, leveltag in enumerate(levels[:-1]):
                # Search for the current part of the path in this band
                if band.tools:
                    matchlist = [node for node in band.tools
                                 if resource.removehotkey(node.tag)[0] ==
                                 resource.removehotkey(leveltag)[0]]
                else:
                    matchlist = []

                # Is the current part of the path missing from this band?
                if not matchlist:
                    # Create new tool to hold the missing Popup
                    if CONFIG['PRODUCT'] == "GoldCare" and leveltag == "&Commands":
                        # Create and Link Command Popup
                        self._addband(self._POPUPCOMMAND, CommandBarBand.BANDTYPEPOPUP,
                                      "attCommands", resource.loadstring("IDS_CAP0146"),
                                      self.bands[self._MENUSTANDARD], False,
                                      resource.loadimage("commands.ico"))
                        newtool = self._tools["attCommands"]
                    elif CONFIG['PRODUCT'] == "GoldCare" and leveltag in ("&Window", window_string):
                        # Create and Link Window Popup
                        self._addband(self._POPUPWINDOW, CommandBarBand.BANDTYPEPOPUP,
                                      "attWindow", window_string,
                                      self.bands[self._MENUSTANDARD], False,
                                      resource.loadimage("settings.ico"))
                        newtool = self._tools["attWindow"]
                    elif CONFIG['PRODUCT'] == "GoldCare" and leveltag == "Support Tools":
                        # Create and Link Support Popup, one from bottom
                        saveoffsettail = self.bands[self._MENUSTANDARD].offsettail
                        self.bands[self._MENUSTANDARD].offsettail = 1
                        self._addband(self._TOOLBARDEBUG, CommandBarBand.BANDTYPEPOPUP,
                                      "attDebug", resource.loadstring("IDS_CAP0060"),
                                      self.bands[self._MENUSTANDARD], False,
                                      resource.loadimage("gc_log.ico"))
                        self.bands[self._MENUSTANDARD].offsettail = saveoffsettail
                        newtool = self._tools["attDebug"]
                    else:
                        newtool = CommandBarTool()
                        # build unique name based on path
                        toolname = "/".join(levels[:levelndx + 1])
                        toolname = toolname.replace("/", "_")
                        newtool.name = "".join(["att", toolname])
                        newtool.tag = leveltag
                        self._tools[newtool.name] = newtool

                        # Create new popup
                        newband = CommandBarBand()
                        newband.name = "".join(["bndPopup", toolname])
                        newband.bandtype = CommandBarBand.BANDTYPEPOPUP
                        self.bands[newband.name] = newband

                        # Attach new popup to new tool
                        newtool.subband = newband.name

                        # Attach new tool to current band
                        band.inserttool(newtool)

                    # Remember newband for updating
                    if newbandtool is None:
                        newbandtool = newtool
                else:
                    newtool = matchlist[0]

                band = self.bands[newtool.subband]

            band.inserttool(tool)

        # Add to appropriate toolbar band
        if tool.type == self._TYPETOOL:
            if tool.toolbar in self.bands:
                self.bands[tool.toolbar].inserttool(tool)
            else:
                self.bands[self._TOOLBARSTANDARD].inserttool(tool)

        if newbandtool:
            return newbandtool
        else:
            return tool

    def _removetool(self, targettool: CommandBarTool):
        ''' Remove tool from bands and collection '''
        # Remove from any band which has it
        for name in self.bands:  # pylint: disable=C0206
            band = self.bands[name]
            # band.tools = [tool for tool in band.tools if tool.name != targettool.name]
            for ndx, tool in enumerate(band.tools):
                if tool.name == targettool.name:
                    # Adjust insertion points, if necessary
                    if ndx < band.offsethead:
                        band.offsethead -= 1
                    if ndx >= len(band.tools) - band.offsettail:
                        band.offsettail -= 1

                    # Add as parent
                    targettool.parents[band.name] = band

                    # Remove
                    band.tools.remove(tool)

                    # Exit inner for loop
                    break
        # Remove from main collection
        self._tools.pop(targettool.name, None)

    def getid(self):
        ''' override getid '''
        return "COMMANDBAR"

    def update_for_alt_languages(self):
        """
        Some parts of bands are being returned from telnet
        rename parts of it for avoiding duplicate menus
        """

        if resource.getlanguage() == resource.LANG_FR:
            # if help menu is returned by server append it to language's own menu
            help_menu_name = 'bndPopup&Help'
            help_telnet_menu = (self.bands or {}).pop(help_menu_name, None)


            if help_telnet_menu:
                help_string = resource.loadstring("IDS_CAP0053")
                self.bands[f'bndPopup{help_string}'] = help_telnet_menu

        return True

#     def setheight(self, height: float):
#         ''' Set the button height '''
#         self.height = height
#
#     def setwidth(self, width: float):
#         ''' Set the button width '''
#         self.width = width
