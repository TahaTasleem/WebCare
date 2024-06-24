'''
Created on Nov 10, 2016

@author: bouchcla
'''
import binascii
import logging
import os
import random
import shutil
import threading
import urllib
from typing import List

from connector import resource
from connector.configuration import CONFIG
from connector.wingempacket import WinGemPacket

import components
from components.filetransfer import getfiletuple
from components.wdobject import BaseWDObject


class Command(BaseWDObject):
    ''' A Command To Run on UI '''

    COMMANDPACKETS = ['WM', 'WXN', 'WX', 'WSB', 'WPM', 'WH',
                      'WMB', 'WMS', 'WST', 'WI', 'WUH', 'WFE',
                      'WIV', 'WDV', 'WWB', 'EBR', 'WUB', 'WFB',
                      'WXM', "WSA", "WDF", "WRC"]
    URLSPAWN = "rundll32 url.dll,fileprotocolhandler"

    def __init__(self):
        ''' Constructor '''
        super(Command, self).__init__("COMMAND")
        self._cacheable = False
        self._complete = True
        self._command = {}
        self.prompting = False

    def __str__(self):
        ''' format string for printing '''
        return str(self._command)

    def getcommand(self):
        ''' Return command dictionary for json-ification '''
        return self._command

    def setcommand(self, commandkey, commandvalue):
        ''' ability to set command key/value pairs '''
        if commandvalue is None:
            # delete it
            try:
                self._command.pop(commandkey)
            except KeyError:
                pass
        else:
            self._command[commandkey] = commandvalue

    def logout(self, msg=None, error=None):
        ''' Logged out / disconnected '''
        self._command['type'] = "LOGOUT"
        if msg:
            self._command['msg'] = msg
        else:
            self._command['msg'] = "Logged out"
        if error:
            self._command['msgtype'] = "ERROR"

    def navext(self, url: str):
        ''' Navigate to an external page '''
        self._command['type'] = "NAVEXT"
        self._command['exturl'] = url

    def doneconnecting(self):
        ''' Allow TCL window to be shown when necessary '''
        self._command['type'] = "DONECONNECTING"

    def showtcl(self):
        ''' Show TCL window '''
        self._command['type'] = "SHOWTCL"

    def delitem(self, domid: str):
        ''' Delete an Item as specified by their DOM id '''
        self._command['type'] = "DELITEM"
        self._command['targetid'] = domid

    def editfile(self, filepath: str, language: str = None, readonly: bool = False):
        ''' Edit a host file '''
        self._command['type'] = "EDITFILE"
        self._command['uri'] = filepath
        self._command['language'] = language
        self._command['readonly'] = readonly

    def diff(self, filepathorig: str, filepathmod: str, language: str = None):
        ''' Edit a host file '''
        self._command['type'] = "DIFF-FILE"
        self._command['uriOrig'] = filepathorig
        self._command['uriMod'] = filepathmod
        self._command['language'] = language

    def changecolour(self, target: str, colour: str, area: str):
        ''' sends a command to the JS to appply background colours'''
        self._command['type'] = "CHANGECOLOUR"
        self._command['area'] = area
        self._command['targetid'] = target
        self._command['colour'] = colour

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' A Command To Process '''
        handlepacket = False
        hostdata = None
        if packet.packettype() in Command.COMMANDPACKETS:
            handlepacket = True
            if packet.packettype() in ["WM", "WPM"]:
                hostdata = self._parsewm(packet)
            elif packet.packettype() in ["WX", "WXN"]:
                self._parsewx(packet)
            elif packet.packettype() == "WXM":
                self._command['type'] = "CLEARFLASH"
            elif packet.packettype() == "WSB":
                self._parsewsb(packet)
            elif packet.packettype() == "WMB":
                self._parsewmb(packet)
            elif packet.packettype() == "WST":
                self._parsewst(packet)
            elif packet.packettype() == "WMS":
                self._parsewms(packet)
            elif packet.packettype() == "WI":
                self._initui()
            elif packet.packettype() in ["WFE", "WFB"]:
                self._parsewfe(packet)
            elif packet.packettype() in ["WUH", "WUB"]:
                self._parsewuh(packet)
            elif packet.packettype() == "WWB":
                self._parsewwb(packet)
            elif packet.packettype() in ["WIV", "WDV"]:
                self._parsewiv(packet)
            elif packet.packettype() == "EBR":
                self._parseebr(packet)
            elif packet.packettype() == "WH":
                handlepacket = True  # self._parsewh(packet)
            elif packet.packettype() == "WSA":
                handlepacket, hostdata = self._parsewsa(packet)
            elif packet.packettype() == "WRC":
                self._parsewrc(packet)
            elif packet.packettype() == "WDF":
                handlepacket = self._parsewdf(packet)
        elif packet.packettype() == "WP":
            handlepacket = True
            self._parsewp(packet)
        return handlepacket, hostdata, None


    def copyblobs(self, srcaccount, destaccount, copydirs):
        """ Copy Blobs. '' inside copydirs will copy whole source to destination account """
        if not copydirs or destaccount == srcaccount:
            return
        basesrc = getfiletuple(srcaccount, '', '', isdir=True)[0]
        basedest = getfiletuple(destaccount, '', '', isdir=True)[0]
        try:
            if not os.path.exists(basedest):
                os.makedirs(basedest)
            for eachdir in copydirs:
                source = os.path.join(basesrc, eachdir)
                destination = os.path.join(basedest, eachdir)
                try:
                    self.recursive_overwrite(source, destination)
                except: # pylint: disable=bare-except
                    continue
        except: # pylint: disable=bare-except
            return

    def recursive_overwrite(self, src, dest, ignore=None):
        ''' recursively overwrites src and dest '''
        if os.path.isdir(src):
            if not os.path.isdir(dest):
                os.makedirs(dest)
            files = os.listdir(src)
            if ignore is not None:
                ignored = ignore(src, files)
            else:
                ignored = set()
            for file in files:
                if file not in ignored:
                    srcfile = os.path.join(src, file)
                    destfile = os.path.join(dest, file)
                    self.recursive_overwrite(srcfile, destfile, ignore)
        else:
            shutil.copyfile(src, dest)

    def _initui(self):
        ''' Send initialization command '''
        self._command['type'] = "INITUI"
        return None

    def _parsewrc(self, packet: WinGemPacket):
        ''' Parse WRC Packet '''
        if packet.extract(2) == "COPYBLOBS":
            self.copyblobs(packet.extract(3), packet.extract(4), packet.extractaslist(5))


    def _parsewm(self, packet: WinGemPacket):
        ''' Parse Message Packet '''
        result = None
        try:
            result = self.msg(packet.extract(2), packet.extractaslist(3),
                              packet.extractaslist(4))
        except ValueError:
            logging.error("Error Parsing position for flash message."
                          "Submitted packet is - " + packet.stringify())
        return result

    def question(self, heading: str, label: str, inputtype: str = "TEXT"):
        ''' Ask user question '''
        self._command['type'] = "QUESTION"
        self._command['header'] = heading
        self._command['label'] = label
        self._command['inputtype'] = inputtype

    def msg(self, msgtype: str, message: List[str], options: List[str]):
        ''' Parse Message Packet '''
        # don't show a blank message
        if not message:
            return ""

        self._command['type'] = "MSG"
        self._command['msg'] = ("<br>".join(message)).replace(chr(10), "<br>")
        self._command['msgtype'] = msgtype

        fulloptions = [WinGemPacket(x).extractaslist(1, 1) for x in options]
        # build buttons for the appropriate types of messages
        self._command['button'] = []
        if self._command['msgtype'] == "ATTENTION":
            self._command['button'].append({"buttonlabel": "OK", "returndata": "WHIR:OK"})
            self._command['button'].append(
                {"buttonlabel": "Cancel", "returndata": "WHIR:Cancel"})
        elif self._command['msgtype'] != "FLASH":
            # covers button creation for ERROR,FATAL,EXPLAIN,TELL
            self._command['button'].append({
                "buttonlabel": "OK",
                "returndata": "WHIR:"
            })
        if self._command['msgtype'] != "FLASH":
            headerstr = ""
            imagestr = ""
            if self._command['msgtype'] == "TELL" or self._command['msgtype'] == "EXPLAIN":
                imagestr = "info.svg"
                headerstr = "Information"
            elif self._command['msgtype'] == "ERROR" or self._command['msgtype'] == "FATAL":
                imagestr = "exclamation.svg"
                headerstr = "Error"
            elif self._command['msgtype'] == "ATTENTION":
                imagestr = "exclamation.svg"
                headerstr = "Attention"
            self._command['header'] = headerstr
            self._command['image'] = resource.loadimage(imagestr)
        for dataoption in fulloptions:
            if dataoption[0] == "HEADING":
                self._command['header'] = dataoption[1]
            elif dataoption[0] == "POSITION":
                try:
                    self._command['xpos'] = components.applyscaling(
                        float(dataoption[1]), False)
                    self._command['ypos'] = components.applyscaling(float(dataoption[2]), True)
                except ValueError as exception:
                    raise ValueError from exception
            elif dataoption[0] == "PROMPT":
                self._command['targetid'] = dataoption[1]
            elif dataoption[0] == "ICON":
                imageres = ""
                if dataoption[1] == "CRITICAL" or dataoption[1] == "WARNING":
                    imageres = "exclamation.svg"
                elif dataoption[1] == "INFORMATION":
                    imageres = "info.svg"
                self._command['image'] = resource.loadimage(imageres)
        return None

    def closeitem(self, exlevel: int, calllevel: int, screen: bool):
        ''' build close screen '''
        exlevel = exlevel * 1000
        if screen:
            self._command['type'] = "CLOSESCREEN"
            self._command['targetid'] = exlevel + (500 + calllevel)
        else:
            self._command['type'] = "CLOSEMENU"
            self._command['targetid'] = exlevel + calllevel

    def _parsewx(self, packet: WinGemPacket):
        ''' parse wx / wxn packet '''
        self.closeitem(int(packet.extract(2)),
                       int(packet.extract(3)) if packet.extract(3) else 0,
                       (packet.packettype() == "WX"))

    def _parsewsb(self, packet: WinGemPacket):
        ''' parse wsb packet '''
        self._command['type'] = "STATUSBAR"
        wsbtype = packet.extract(2)
        if wsbtype == "UPDATE":
            self._command['update'] = packet.extract(3)
            options = packet.extract(4).split(WinGemPacket.VM)
            for opt in options:
                if opt == "NOTEXT":
                    pass
                if WinGemPacket.SM in opt:
                    msg = opt.split(WinGemPacket.SM)
                    if msg and msg[0] == "MSG":
                        self._command['message'] = msg[1]
        elif wsbtype == "MESSAGE":
            self._command['message'] = packet.extract(3)
        else:
            # SHOW, HIDE, INIT, CLOSE
            self._command[wsbtype.lower()] = 1
            if wsbtype == "INIT":
                self._command['message'] = packet.extract(3)

    def _parsewmb(self, packet: WinGemPacket):
        ''' parse wmb packet '''
        self._command['type'] = "MENUBAR"
        action = packet.extract(2)
        self._command['action'] = action
        if action == "SETFOCUS":
            self._command['target'] = packet.extract(3)
        elif action == "ENABLE":
            self._command['target'] = str(int(packet.extract(4)) * 1000 +
                                          int(packet.extract(5)) + 500) + \
                "_" + packet.extract(3)

    def _parsewst(self, packet: WinGemPacket):
        ''' parses the WST packet '''
        arealist = packet.extractaslist(2)
        datalist = packet.extractaslist(3)
        self._command["type"] = "UPDATETEXT"
        self._command.setdefault("target", [])
        self._command.setdefault("value", [])
        for datandx, dataoption in enumerate(arealist):
            if dataoption == "USER":
                self._command["target"].append("#userinfo")
                self._command["value"].append(datalist[datandx])
            elif dataoption == "PORT":
                if CONFIG['PRODUCT'] == "AXIS":
                    portinfo = resource.loadstring("IDS_CAP0085")
                else:
                    portinfo = resource.loadstring("IDS_CAP0086")
                portinfo += datalist[datandx]
                self._command["target"].append("#portinfo")
                self._command["value"].append(portinfo)

    def _parsewms(self, packet: WinGemPacket):
        '''parses the WMS packet '''
        options = packet.extractaslist(2)
        fulloptions = [WinGemPacket(x).extractaslist(1, 1) for x in options]
        self._command["type"] = "MAIL"
        # assumed default icon
        self._command["iconname"] = resource.loadimage("envelope.svg")
        for dataoption in fulloptions:
            if dataoption[0] == "UNREAD":
                self._command["unreadnum"] = dataoption[1]
            elif dataoption[0] == "TOTAL":
                # according to GUICommand, this isnt implemented
                # testing in WinGem shows that the message doesnt change at all with
                # the information passed to it
                self._command["totalnum"] = dataoption[1]
            elif dataoption[0] == "ICON":
                if dataoption[1] != "":
                    self._command["iconname"] = resource.loadimage(dataoption[1])
            elif dataoption[0] == "SHOW":
                self._command["visible"] = True
            elif dataoption[0] == "HIDE":
                self._command["visible"] = False
            elif dataoption[0] == "SEND":
                self._command["sendtype"] = dataoption[1]
                self._command["sendtext"] = dataoption[2]
            elif dataoption[0] == "MSG":
                self._command["message"] = dataoption[1]
            elif dataoption[0] == "FLASH":
                self._command["flash"] = True

    def _parsewuh(self, packet: WinGemPacket):
        ''' Parse Update Browser Packet '''
        self._command['type'] = "UPDATEBROWSER"
        target = packet.extract(2)
        if target[:6] == "WGBGB:":
            target = target[:5] + "_" + target[6:]
        self._command['targetid'] = target
        self._command['element'] = packet.extract(3)
        self._command['html'] = packet.extract(4)
        self._command['updatetype'] = packet.extract(5)
        self._command['external'] = packet.packettype() == "WUB"

    def _parsewfe(self, packet: WinGemPacket):
        ''' Parse Fire Event Packet '''
        self._command['type'] = "FIREEVENT"
        target = packet.extract(2)
        if target[:6] == "WGBGB:":
            target = target[:5] + "_" + target[6:]
        self._command['targetid'] = target
        self._command['element'] = packet.extract(3)
        self._command['event'] = packet.extract(4).upper()
        self._command['external'] = packet.packettype() == "WFB"

    def _parsewiv(self, packet: WinGemPacket):
        ''' Parse insert/delete row Packet '''
        if packet.packettype() == "WIV":
            self._command['type'] = "INSERTMV"
        elif packet.packettype() == "WDV":
            self._command['type'] = "DELETEMV"
        self._command['prompt'] = packet.extract(2, 1)
        self._command['mvpos'] = packet.extract(2, 2)

    def _parsewwb(self, packet: WinGemPacket):
        ''' Parse WWB Packet '''
        self._command['type'] = "WAITONBUTTON"
        self._command['targetid'] = packet.extract(2)

    def _parseebr(self, packet: WinGemPacket):
        ''' Parse EBR Packet '''
        self._command['type'] = "EXTERNALBROWSER"

        options = packet.extractaslist(4)
        tag = [WinGemPacket(x).extract(1, 1, 2) for x in options
               if WinGemPacket(x).extract(1, 1, 1) == "TAG"]
        tag = tag[0] if tag else ""
        if tag:
            browserid = tag[:5] + "_" + tag[6:]
            self._command['targetid'] = browserid
        else:
            browserid = tag
        options = [[WinGemPacket(x).extract(1, 1, 1), WinGemPacket(x).extract(1, 1, 2)]
                   for x in options]
        from webrouting import (  # pylint: disable=import-outside-toplevel
            convertcolunittoem, convertrowunittoem)
        for opt in options:
            optname = opt[0]
            try:
                if optname == "SHOW":
                    self._command["visible"] = True
                elif optname == "HIDE":
                    self._command["visible"] = False
                elif optname == "ENABLE":
                    # enable?
                    pass
                elif optname == "DISABLE":
                    # disable?
                    pass
                elif optname == "ZORDER":
                    self._command["zorder"] = opt[1]
                elif optname == "WWIDTH" and browserid == "WGBGB_1":
                    try:
                        wwidth = float(opt[1]) * 0.5
                        self._command["width"] = str(wwidth) + "em"
                    except ValueError:
                        logging.error("Error Parsing left bgbrowser width."
                                      "Submitted packet is - " + packet.stringify())
                elif optname == "TITLE":
                    title = opt[1]
                    if CONFIG['PRODUCT'] == "AXIS":
                        title = "AXIS " + resource.loadstring("IDS_CAP0036") + " - " + title
                    else:
                        title = "GoldCare " + \
                            resource.loadstring("IDS_CAP0036") + " - " + title
                    self._command['title'] = title
                elif optname == "WWIDTH":
                    self._command['width'] = convertcolunittoem(float(opt[1]))
                elif optname == "WHEIGHT":
                    self._command['height'] = convertrowunittoem(float(opt[1]))
                elif optname == "WTOP":
                    self._command['top'] = convertrowunittoem(float(opt[1]))
                elif optname == "WLEFT":
                    self._command['left'] = convertcolunittoem(float(opt[1]))
                elif optname == "WSA":
                    self._command['nowdd'] = True
            except ValueError:
                logging.error("Failed to read item (" + optname + ") " + packet.stringify())
        url = packet.extract(3)
        if tag[:6] != "WGBGB:":
            # treat as new window
            self._command['newwindow'] = 1
            self._command['cmd'] = packet.extract(2)
            if packet.extract(2) == "CLOSE" and not tag:
                if packet.extract(4) == "ALL":
                    tag = "ALL"
            if tag == "":
                tag = "WF" + str(int(random.random() * 1000))
            self._command['tag'] = tag
        if url:
            # sometimes (MYOR), you get a value mark at the end of the url
            if WinGemPacket.VM in url:
                url = WinGemPacket(url).extract(1, 1)
            urldata = ""
            if "?" in url:
                # need to handle data getting tacked on to a url,
                # because getfiletuple will strip it
                spliturl = url.split("?")
                url = spliturl[0]
                urldata = spliturl[1]
            # may need to convert this to a real url
            # host may send ./blah and we need to translate that to full path
            isrealurl = urllib.parse.urlparse(url)[0] != ""
            self._command['realurl'] = isrealurl
            if url.lower() != "about:blank" and not isrealurl:
                directory, filename = getfiletuple(url, "r", threading.current_thread().name)
                url = directory + filename
            if url.lower() == "about:blank" and url != "about:blank":
                # sometimes the host sends it with capital A
                url = url.lower()
            if urldata:
                url += "?" + urldata
            self._command['url'] = url
            if (url.split(".")[-1] in ("html", "HTML", "htm", "HTM") and
                    tag[:6] != "WGBGB:" and
                    not isrealurl) and packet.extract(2) != "PRINT":
                self._command['html'] = 1

    # def _parsewh(self, packet: WinGemPacket):
        #''' Parse Heading '''
        #title = packet.extract(2)
        # if title:
        #   self._command['type'] = "UPDATETITLE"
        #   title += " - " + CONFIG['PRODUCT']
        #   if not CONFIG['PRODUCTION']:
        #       title += " (Development)"
        #   self._command['value'] = title
        # return True

    def _parsewsa(self, packet: WinGemPacket):
        ''' Parse WSA Packet '''
        spawnapp = packet.extract(2)
        if Command.URLSPAWN in spawnapp.lower():
            # send this to a browser instead
            # get url first
            x = spawnapp.lower().find(Command.URLSPAWN)
            url = spawnapp[x + len(Command.URLSPAWN):].strip()
            # strip quotes around url
            url = url[1:-1] if (url[0] == url[-1]) and url.startswith(("'", '"')) else url
            if url:
                # add a random number after it to force the file to be not cached
                url += "?v=" + binascii.hexlify(os.urandom(8)).decode("utf-8")
                ebrpacket = WinGemPacket("EBR" + WinGemPacket.AM + "DISPLAY"
                                         + WinGemPacket.AM + url
                                         + WinGemPacket.AM + "WSA")
                self._parseebr(ebrpacket)
                return True, "1"
        return True, "-1"

    def _parsewp(self, packet: WinGemPacket):
        '''
        Parse WP Packet
        Only used by a grid to update certain properties on a prompt
        Currently only Prompt Literal
        '''
        self._command['type'] = "UPDATEPROMPT"
        self._command['targetid'] = packet.extract(2)
        self._command['promptliteral'] = packet.extract(11)
        # tlb as well
        options = packet.extractaslist(12)
        for option in options:
            if "DDD" in option:
                self._command['tlb'] = True
            if "DDL" in option:
                self._command['tlb'] = True
                self._command['tlbleft'] = True
            if "DDI" in option:
                self._command['tlb'] = True
                self._command['tlbicon'] = resource.loadimage(
                    WinGemPacket(option).extract(1, 1, 2))

    def showfilepicker(self, targetfile: str, origfile: str, returnfilename: bool = False):
        ''' Send command to show file picker '''
        self._command['type'] = "FILEPICKER"
        self._command['targetfile'] = targetfile
        self._command['retfile'] = returnfilename
        if origfile:
            self._command['origfile'] = origfile

    def _parsewdf(self, packet: WinGemPacket):
        ''' Parse WDF to call ui picker '''
        if packet.extract(2) == "PICK":
            self.showfilepicker("", packet.extract(4), True)
            return True
        else:
            return False

    def updateaclist(self, listname: str, listcontents: list):
        ''' update auto complete list '''
        self._command['type'] = "UPDATEACLIST"
        self._command['name'] = listname
        self._command['list'] = listcontents

    def updatetext(self, value: str, target: str):
        ''' Update an element's text '''
        self._command['type'] = "UPDATETEXT"
        self._command.setdefault("target", [])
        self._command.setdefault("value", [])
        self._command["target"].append(target)
        self._command["value"].append(value)
