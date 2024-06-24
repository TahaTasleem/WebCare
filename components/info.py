'''
Created on Nov 18, 2016

@author: bouchcla
'''
from datetime import datetime
import logging
import os
import threading

from components.filetransfer import getfiletuple, fixslashes
from components.wdobject import BaseWDObject
from components.logfilemanager import getsessionip
from connector.configuration import CONFIG
from connector.wingempacket import WinGemPacket


class Info(BaseWDObject):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super().__init__("INFO")

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Handle WGI Packets '''
        if packet.packettype() != "WGI":
            return False, ""
        subpacket = packet.extract(2)
        hostdata = ""
        if subpacket == "COMPUTERNAME":
            hostdata = "WEBDIRECT"
        elif subpacket == "OSVER":
            hostdata = "6" + WinGemPacket.VM + "2" + WinGemPacket.VM + \
                "9200" + WinGemPacket.VM + ""
        elif subpacket == "IEVERSION":
            hostdata = "9" + WinGemPacket.VM + "11"
        elif subpacket == "IP.ADDRESS":
            hostdata = getsessionip(threading.current_thread().name)
            # hostdata = "10.39.5.95"
        elif subpacket == "DATAPATH":
            hostdata = "static" + os.sep + "data" + os.sep
        elif subpacket == "DIR":
            hostdata = self._getdirectory(packet)
        elif subpacket == "URL":
            hostdata = CONFIG["BASEROUTE"]
        elif subpacket == "VERSION":
            hostdata = CONFIG["VERSION"]
        elif subpacket == "DISKFREE":
            hostdata = 0
        elif subpacket == "USERNAME":
            hostdata = "WEBDIRECT"
        elif subpacket == "APPLICPATH":
            hostdata = ""
        elif subpacket == "ISADMIN":
            hostdata = "0"
        elif subpacket == "WINDOWSTATE":
            hostdata = "2"
        elif subpacket == "REGISTRY":
            hostdata = ""
        elif subpacket == "CSIDL":
            hostdata = ""
        elif subpacket == "ENV.STRING":
            hostdata = ""
        self._complete = True
        return True, hostdata, None

    def getbrowsers(self, bgbrowsers: list, rptbrowsers: dict):
        ''' get list of browsers '''
        packet = WinGemPacket("")
        bgbtags = []
        bgburls = []
        for bgb in bgbrowsers:
            bgbtags.append(bgb.browserid)
            bgburls.append(bgb.url)
        packet.replace(WinGemPacket.SM.join(bgbtags), 1, 1)
        packet.replace(WinGemPacket.SM.join(bgburls), 1, 2)

        # Report Browsers is a Dictionary
        packet.replace(WinGemPacket.SM.join(rptbrowsers.keys()), 1, 3)
        packet.replace(WinGemPacket.SM.join(rptbrowsers.values()), 1, 4)

        return packet.stringify()

    def _getdirectory(self, packet: WinGemPacket):
        ''' Returns the contents of the directory specified. '''
        directory = os.path.normpath(packet.extract(3))
        directory = fixslashes(directory)
        sessionid = threading.current_thread().name
        if sessionid == "MainThread":
            sessionid = ""
        if not os.path.isdir(directory):
            return ""
        # determine directory location
        localdir = getfiletuple(directory, "", sessionid, isdir=True)[0]

        files = []
        isdir = []
        size = []
        fdate = []
        times = []

        # get data from directory
        try:
            directorylist = os.scandir(localdir)
            for item in directorylist:
                files.append(item.name)
                amidir = item.is_dir()
                fstat = item.stat()
                if amidir:
                    isdir.append("Y")
                    size.append("-1")
                else:
                    isdir.append("N")
                    size.append(str(fstat.st_size))
                timestamp = fstat.st_mtime
                fdatetime = datetime.fromtimestamp(timestamp)
                fdate.append(fdatetime.strftime("%Y/%m/%d"))
                times.append(fdatetime.strftime("%H:%M:%S"))
        except (IOError, OSError):
            logging.error("Failed to find directory: " + localdir)
        return WinGemPacket.SM.join(files) + WinGemPacket.VM + \
            WinGemPacket.SM.join(isdir) + WinGemPacket.VM + \
            WinGemPacket.SM.join(size) + WinGemPacket.VM + \
            WinGemPacket.SM.join(fdate) + WinGemPacket.VM + \
            WinGemPacket.SM.join(times)
