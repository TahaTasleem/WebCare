'''
Created on Oct 12, 2016

@author: bouchcla
'''
from copy import copy
import hashlib
import logging
import random
from components.application import Application
from components.command import Command
from components.filetransfer import FileTransfer
from components.enhancedfiletransfer import EnhancedFileTransfer
from components.bgbrowser import BGBrowser
from components.editor import Editor
from components.info import Info
from components.screen import Screen
from components.menubar import MenuBar
from components.commandbar import CommandBar, CommandBarTool  # pylint: disable=unused-import
from components.tcldata import TCLData
from components.menu import MenuObject
from connector.wingempacket import WinGemPacket
# this import is used, but pylint can't pick it up
import connector.logging  # pylint: disable=unused-import


def ispromptingpacket(packet: WinGemPacket):
    ''' determine if we are a prompting packet '''
    promptpacket = False
    if packet.packettype() in ['WPD', 'WPN', 'WPP', 'WWB', 'WPM', 'WM']:
        promptpacket = True
    if packet.packettype() == "WA":
        if packet.extract(2) == "DUMMY.PACKET":
            promptpacket = True
        if packet.extract(2) == "MOUSE" and packet.extract(3) == "RESET":
            promptpacket = True
    return promptpacket


class PacketProcessor(object):
    ''' Class to handle the processing of WinGem packets '''
    LOCALOBJECTS = ['FILETRANSFER', 'APP', 'INFO']
    MODIFYIDCOMMAND = ['DISPLAY', 'FIREEVENT', 'UPDATEBROWSER',
                       'WAITONBUTTON', 'MSG', 'UPDATEPROMPT']
    NOTIMPLEMENTED = ["DIT", "DE", "DP", "DR", "DX"]

    def __init__(self, sessionid, screenstack: list, externalfiles: dict,
                 commandbar: CommandBar, startdata: str = None):
        ''' Constructor '''
        self._currentdata = ""
        self._currentobjects = []
        self._completedobjects = []
        self._hostdata = []
        self._sessionid = sessionid
        self._pathmap = {}
        self._screenstack = screenstack
        self._commandbar = commandbar
        self._menubar = MenuBar()
        self._bgbrowserlist = []
        self._rptbrowserlist = dict()
        self._externalfiles = externalfiles
        self.canexit = True
        self._exitmsg = ""
        self.rowoffset = 0.0
        self.coloffset = 0.0
        self.disconnect = False
        self.lockscreen = False
        self._startdata = startdata

    def _intialize(self):
        ''' set packet processor to defaults for non-processing objects '''
        self._pathmap.clear()
        self._screenstack.clear()
        self._bgbrowserlist.clear()
        self._commandbar.addpacket(WinGemPacket("WTB" + WinGemPacket.AM + "RESET"))

    def processinput(self, rawdata: str):
        ''' Determine what to do with the packet '''
        returndata = []

        # split data into packets and tcl data
        wingempackets = self._splitrawdata(rawdata)

        # log packets + raw data
        for wgp in wingempackets:
            if isinstance(wgp, TCLData):
                logging.getLogger("packetlogger").packet("   |" + wgp.getdata())
                returndata.append(wgp)
            else:
                logging.getLogger("packetlogger").packet("IN |" + wgp)
                self._processwgpacket(wgp)
                if self._completedobjects:
                    # append completed objects to the return list
                    returndata += self._completedobjects
                    self._completedobjects = []
                if self.disconnect:
                    break

        # setup return host data,
        #     clear out instance data
        returnhostdata = self._hostdata
        self._hostdata = []

        return returndata, returnhostdata

    def _splitrawdata(self, rawdata: str):
        ''' Splits raw data into TCL and WinGem packets '''
        wgpackets = []
        while rawdata:
            chr2loc = rawdata.find(chr(2))
            chr3loc = rawdata.find(chr(3))
            if chr(2) in self._currentdata and chr3loc >= 0:
                # the end of a previous packet is here
                wgpackets.append(self._currentdata[1:] + rawdata[:chr3loc])
                rawdata = rawdata[chr3loc + 1:]
                self._currentdata = ""
            elif chr2loc > 0:
                # convert everything before the STX symbol to a tcl packet
                tstr = rawdata[0:chr2loc]
                rawdata = rawdata[chr2loc:]
                if tstr:
                    wgpackets.append(TCLData(tstr))
            elif chr2loc == 0:
                # Start WinGem packet
                if chr3loc >= 0:
                    # true packet, process it
                    wgpackets.append(rawdata[1:chr3loc])
                    rawdata = rawdata[chr3loc + 1:]
                else:
                    # don't have full packet yet, cache it for next cycle
                    self._currentdata = rawdata
                    rawdata = ""
            elif chr3loc >= 0:
                # End of packet present, do we have cached data?
                if not self._currentdata:
                    # error case?
                    # check what wingem does
                    logging.error("Bad packet definition")
                else:
                    # pass packet off to WinGem handler
                    wgpackets.append(
                        self._currentdata[1:] + rawdata[:chr3loc])
                    self._currentdata = ""
                rawdata = rawdata[chr3loc + 1:]
            else:
                # tcl packet
                # should check to see if we have buffered data first
                if self._currentdata:
                    self._currentdata += rawdata
                else:
                    if rawdata:
                        wgpackets.append(TCLData(rawdata))
                rawdata = ""
        return wgpackets

    def _processwgpacket(self, packet: str):
        ''' Process a WinGem packet '''
        # Check to see if already created object needs to use it
        wgpacket = WinGemPacket(packet)
        # pre-process some packets (WD, WPD)
        wgpacket = self._preprocesspacket(wgpacket)
        # print(packet)
        if not self._checkstack(wgpacket):
            # we haven't, so continue
            retobject = None
            if wgpacket.isignorepacket():
                # do nothing with it
                pass
            else:
                retobject = self._handlepacket(wgpacket)
                if retobject:
                    # Add packet to list
                    if retobject.gettype() == "EDITOR":
                        processed, hostdata, newobj = retobject.addpacket(wgpacket)
                        retobject = newobj
                    else:
                        processed, hostdata, _ = retobject.addpacket(wgpacket)
                    self._processhostdata(hostdata)
                    if not processed:
                        retobject = None
                        logging.error("Packet not handled: " + packet)
                elif wgpacket.packettype() == "WGI" and wgpacket.extract(2) == "BROWSERS":
                    #info = Info()
                    #self._processhostdata(info.getbrowsers(
                    #    self._bgbrowserlist, self._rptbrowserlist))
                    retobject = Command()
                    retobject.setcommand("type", "INFO")
                    retobject.setcommand("query", "browsers")

            # now, determine what we do with the response
            if retobject:
                if retobject.iscomplete():
                    self._processcomplete(retobject)
                    if wgpacket.packettype() == "WI":
                        # resend command bar
                        self._completedobjects.append(self._commandbar)
                        if wgpacket.extract(4) != "WDE":
                            # account is not WebDirect Enabled
                            cmd = Command()
                            cmd.logout("Account is not WebDirect enabled, aborting.", True)
                            self._completedobjects.clear()
                            self._completedobjects.append(cmd)
                            # let the telnet thread know we need to disconnect
                            self.disconnect = True
                elif retobject.gettype() == "SCREEN":
                    self._closescreens(retobject.getid(), True)
                    retobject.rowoffset = self.rowoffset
                    retobject.coloffset = self.coloffset
                    if self._screenstack:
                        prevscreen = self._screenstack[-1]
                        if prevscreen.height > retobject.height and \
                            prevscreen.executelevel == retobject.executelevel and \
                            prevscreen.rowoffset >= 0:
                            retobject.ischild = True
                    self._screenstack.append(retobject)
                else:
                    self._currentobjects.append(retobject)
                    if retobject.gettype() == "FILETRANSFER" and retobject.showui:
                        cmd = Command()
                        cmd.showfilepicker(retobject.filename, retobject.origfilename)
                        self._completedobjects.append(cmd)

    def _handlepacket(self, wgpacket: WinGemPacket):
        ''' Create object that handles packet '''
        retobject = None
        # big case statement to decide what to do with the packet
        if wgpacket.packettype() == "WI":
            self._intialize()
            retobject = Command()
        elif wgpacket.packettype() == "WS":
            retobject = Screen()
        elif wgpacket.packettype() == "EBR":
            options = wgpacket.extractaslist(4)
            tag = [WinGemPacket(x).extract(1, 1, 2) for x in options
                   if WinGemPacket(x).extract(1, 1, 1) == "TAG"]
            tag = tag[0] if tag else ""
            if tag[:6] == "WGBGB:":
                browserid = int(tag[6:])
                if browserid > (len(self._bgbrowserlist) - 1):
                    for index in range(len(self._bgbrowserlist), browserid + 1):
                        newbrowser = BGBrowser(str(index), (index != browserid))
                        if index != browserid:
                            self._completedobjects.append(newbrowser)
                        self._bgbrowserlist.append(newbrowser)
                retobject = self._bgbrowserlist[-1]
            else:
                # report browser
                # keep track of names for WGI request
                if wgpacket.extract(2) != "CLOSE":
                    if not tag:
                        # if no tag, add to packet
                        tag = "WF" + str(int(random.random() * 1000))
                        wgpacket.replace("TAG", 4, len(options) + 1, 1)
                        wgpacket.replace(tag, 4, len(options) + 1, 2)
                    self._rptbrowserlist[tag] = tag
                elif tag in self._rptbrowserlist and wgpacket.extract(2) == "CLOSE":
                    self._rptbrowserlist.pop(tag)
                elif tag == "ALL" and wgpacket.extract(2) == "CLOSE":
                    self._rptbrowserlist.clear()
                retobject = Command()
        elif wgpacket.packettype() == "WDD":
            if wgpacket.extract(2) == "UNLOAD":
                try:
                    self._rptbrowserlist.pop(wgpacket.extract(3))
                except KeyError:
                    # don't care if it's already gone
                    logging.warning("Closed browser, but we didn't have it open? " +
                                    wgpacket.extract(3))
            elif wgpacket.extract(2) == "EXIT":
                if self.canexit:
                    self._processhostdata(chr(27) + "QUIT!")
                else:
                    tempcmd = Command()
                    tempcmd.msg("FLASH", [self._exitmsg], [])
                    self._completedobjects.append(tempcmd)
        elif wgpacket.packettype() == "WDE":
            retobject = Editor()
        elif wgpacket.packettype() in ("WA", "WMA", "WMO"):
            if wgpacket.packettype() == "WA" and \
                    wgpacket.extract(2) in ("ENABLEEXIT", "DISABLEEXIT", "GETSTART"):
                # handle this here
                if wgpacket.extract(2) == "ENABLEEXIT":
                    self.canexit = True
                elif wgpacket.extract(2) == "DISABLEEXIT":
                    self.canexit = False
                    self._exitmsg = wgpacket.extract(3)
                elif self._startdata:
                    self._processhostdata(self._startdata)
                else:
                    self._processhostdata("")
            else:
                retobject = Application()
        elif wgpacket.packettype() == "WGI" and wgpacket.extract(2) != "BROWSERS":
            retobject = Info()
        elif wgpacket.packettype() == "WFT":
            retobject = FileTransfer(self._sessionid)
        elif wgpacket.packettype() == "WXT":
            retobject = EnhancedFileTransfer(self._sessionid)
        elif wgpacket.packettype() in Command.COMMANDPACKETS:
            retobject = Command()
        elif wgpacket.packettype() == "WN":
            retobject = MenuObject()
        elif wgpacket.packettype() == "WDL":
            self._processlog(wgpacket)
        # DDE Packets that we don't immeplement
        elif wgpacket.packettype() == "DSN":
            self._processhostdata("Not implemented.")
        elif wgpacket.packettype() == "DF":
            self._processhostdata("1")
        elif wgpacket.packettype() in PacketProcessor.NOTIMPLEMENTED:
            self._processhostdata("-1")
        elif wgpacket.packettype() == "WC":
            # if we got here, nothing processed the WC packet
            if wgpacket.extract(2) == "QUERYROW":
                self._processhostdata("0")
        elif wgpacket.packettype() == "WLS":
            if wgpacket.extract(2) == "1":
                self.lockscreen = True
            else:
                self.lockscreen = False
        elif wgpacket.packettype() == "WCS":
            self._processhostdata("WCS.END")
        else:
            # TODO: implement error case
            pass
        return retobject

    def _processlog(self, packet: WinGemPacket):
        ''' add data to log as given '''
        logdata = packet.extractfrom(2)
        logging.debug(logdata)

    def _checkstack(self, packet: WinGemPacket):
        ''' Check current objects to see if any of them can use this packet '''
        objlist = []
        if self._screenstack:
            objlist.append(self._screenstack[-1])
        if self._menubar:
            objlist.append(self._menubar)
        if self._commandbar:
            objlist.append(self._commandbar)
        if self._bgbrowserlist:
            objlist.extend(self._bgbrowserlist)
        objlist.extend(self._currentobjects)
        for obj in objlist:
            screenid = self._screenstack[-1].screenid if self._screenstack else 0
            processed, hostdata, retobj = obj.addpacket(packet, screenid=screenid)
            if processed:
                self._processhostdata(hostdata)
                if isinstance(retobj, list):
                    #===========================================================
                    # some items return a list of objects (buttons, commandbar tools)
                    # map(self._processcomplete, retobj) doesn't work for class methods
                    # if singleobj.iscomplete()?
                    #===========================================================
                    _ = [self._processcomplete(singleobj) for singleobj in retobj if singleobj]
                else:
                    if retobj and retobj.iscomplete():
                        if isinstance(obj, MenuBar) and packet.packettype() == "WP" \
                                and self._screenstack:
                            # only set this on definition of the menubar
                            obj.screenid = self._screenstack[-1].screenid
                            obj.draw = self._screenstack[-1].draw
                        if isinstance(obj, MenuBar) and packet.packettype() == "WPD" \
                                and self._screenstack:
                            # find screen, make it match
                            for screen in reversed(self._screenstack):
                                if screen.screenid == obj.screenid:
                                    screen.draw = True
                                    self._processcomplete(screen)
                                    break
                        # if we are complete, move us to the completed stack
                        self._processcomplete(retobj)
                return True
            elif retobj and isinstance(retobj, Screen) and retobj.iscomplete():
                # if we are complete, move us to the completed stack
                # screen started when another screen wasn't finished yet
                self._processcomplete(retobj)
        return False

    def _processhostdata(self, hostdata):
        ''' handle sending host data back '''
        if hostdata is None:
            pass
        else:
            if hostdata and hostdata[0] == chr(27):
                # already prepended with escape character
                pass
            else:
                # prepend the data with <esc>WHIR:
                hostdata = chr(27) + "WHIR:" + str(hostdata)
            self._hostdata.append(hostdata + chr(13))

    def _processcomplete(self, obj):
        ''' Process Completed Objects '''

        # Remove from current objects
        if obj in self._currentobjects:
            self._currentobjects.remove(obj)

        # Set scheme information
        if obj.gettype() == "APP":
            if obj.colourchange:
                target = obj.gettarget()
                colour = obj.getcolour()
                area = obj.getarea()
                if target is not None:
                    obj = Command()
                    obj.changecolour(target, colour, area)

        # Delete button
        if obj.gettype() == "BUTTON":
            if obj.deleted:  # pylint: disable=no-member
                domid = obj.getid()
                obj = Command()
                obj.delitem(domid)

        # pylint: disable=no-member
        if obj.gettype() == "COMMANDBARTOOL":
            #===================================================================
            # loop through list of parents in obj, and add a new COPY of obj to _completed objects
            # where the copies are identical except for the parent value so we can render
            # differently in multiple locations, OR add a deletion obj for itself and its separator
            #===================================================================
            for parent in obj.parents:
                if obj.deleted:
                    # Delete COMMANDBARTOOL
                    domid = obj.parents[parent].getid() + obj.getid()
                    newdelobj = Command()
                    newdelobj.delitem(domid)
                    # Add to completed objects
                    self._completedobjects.append(newdelobj)

                    # If is begingroup, then also delete the separator
                    if obj.begingroup:  # pylint: disable=no-member
                        domid += "-sep"
                        newdelobj = Command()
                        newdelobj.delitem(domid)
                        self._completedobjects.append(newdelobj)
                else:
                    newobj = copy(obj)
                    newobj.parents = {parent: obj.parents[parent]}  # pylint: disable=no-member
                    # Add to completed objects
                    self._completedobjects.append(newobj)
        else:
            # Add to completed objects
            if obj.gettype() not in PacketProcessor.LOCALOBJECTS:
                self._completedobjects.append(obj)

            # Modify properties of object
            if obj.gettype() == "FILETRANSFER" and obj.filemode in ("READ", "WRITE", "APPEND"):
                # build file mapping
                origfile, localfile = obj.getfilenamemap()  # pylint: disable=no-member
                self._pathmap[origfile] = localfile
            elif obj.gettype() == "PROMPT":
                obj.screenid = self._screenstack[-1].screenid
            elif obj.gettype() == "COMMAND":
                command = obj.getcommand()
                if "type" in command:
                    if command['type'] in ["CLOSESCREEN", "CLOSEMENU"]:
                        self._closescreens(command['targetid'])
                    elif command['type'] in PacketProcessor.MODIFYIDCOMMAND:
                        if "targetid" not in command:
                            pass
                        else:
                            targetid = command['targetid']
                            if command['type'] == "WWB":
                                targetid = targetid.replace(" ", "_")
                            if self._screenstack and \
                                    not ("external" in command and command['external'] == 1):
                                cmd = str(self._screenstack[-1].screenid) + "_" + str(targetid)
                                obj.setcommand("targetid", cmd)
                    elif command['type'] == "EXTERNALBROWSER":
                        if 'html' in command:
                            extid = hashlib.md5(
                                command['url'].encode("ISO-8859-1")).hexdigest()
                            self._externalfiles[extid] = command['url']
                            obj.setcommand('url', extid)
            elif obj.gettype() == "APP":
                if obj.rowoffset is not None:
                    self.rowoffset = obj.rowoffset
                if obj.coloffset is not None:
                    self.coloffset = obj.coloffset

    def _closescreens(self, targetid, addcommand=False):
        ''' Close screens above this level '''
        if self._screenstack:
            sid = self._screenstack[-1].screenid
            while self._screenstack and int(sid) >= int(targetid):
                self._screenstack.pop()
                if self._screenstack:
                    sid = self._screenstack[-1].screenid
            if addcommand:
                cmd = Command()
                exlevel = int(int(targetid) / 1000)
                calllevel = int(targetid) % 1000 - 500 + 1
                cmd.closeitem(exlevel, calllevel, True)
                self._processcomplete(cmd)
        if self._menubar:
            retobj = self._menubar.close(int(targetid))
            if retobj:
                self._completedobjects.append(retobj)

    def _applyfilemap(self, value):
        ''' Check to see if our value is in the file map '''
        if not value:
            return ""
        elif isinstance(value, list):
            value = [self._pathmap[val] if val in self._pathmap else val for val in value]
        else:
            if value in self._pathmap:
                value = self._pathmap[value]
        return value

    def _preprocesspacket(self, packet: WinGemPacket):
        ''' Pre-process WD / WPD packets for file mappings '''
        if packet.packettype() in ['WD', 'WPD', 'EBR', 'WDE']:
            value = packet.extractaslist(3)
            value = self._applyfilemap(value)
            value = WinGemPacket.VM.join(value)
            packet.replace(value, 3)
        if ispromptingpacket(packet):
            # clear status bar
            cmd = Command()
            cmd.addpacket(WinGemPacket("WSB" + WinGemPacket.AM + "CLOSE"))
            cmd.prompting = True
            self._completedobjects.append(cmd)
        return packet
