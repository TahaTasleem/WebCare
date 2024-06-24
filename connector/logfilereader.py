'''
Created on Oct 27, 2016

@author: bouchcla
'''
import logging
import re
import threading
import time
from string import punctuation
from components.command import Command
from components.filetransfer import FileTransfer
from connector.packetprocessor import PacketProcessor
from connector.wingempacket import WinGemPacket
from telnet.telnetmanager import TelnetManager


def readlogfile(logfilepath: str, logdelay: float, tlnmgr: TelnetManager, sessionid):
    '''
    Read Log File in Separate Thread
    '''
    logging.info("Reading log file!")
    logfile = LogFileReader("tests/logs/" + logfilepath)
    localthread = threading.Thread(target=processlogfile,
                                   args=(logfile, logdelay, tlnmgr, sessionid),
                                   name=sessionid)
    localthread.start()


def processlogfile(logfile, logdelay: float, tlnmgr: TelnetManager, sessionid):
    ''' Threaded Log File Reader '''
    logging.info("Processing Log File")
    tlnmgr.setupqueues(sessionid)
    tlnmgr.setconnected(sessionid, True)
    # pylint: disable=protected-access
    pktprocessor = PacketProcessor(sessionid, tlnmgr.getscreenstack(sessionid),
                                   tlnmgr._data[sessionid].externalfiles,
                                   tlnmgr._data[sessionid].commandbar)
    sleep_time = 0.1
    while True:
        if tlnmgr._data[sessionid].socketid is None:
            time.sleep(sleep_time)   # let SOCKETIO on connect set socketid"
            sleep_time += 0.1
            if sleep_time == 0.6:    # just 5 retries,usually sleeps once
                break
            continue
        logdata = logfile.nextpacket()
        # logging.debug("Read packet: " + logdata)
        # print("Read packet: " + logdata)
        if logdata:
            temppacket = WinGemPacket(logdata.replace(chr(2), "").replace(chr(3), ""))
            if temppacket.extract(1) == "WDP":
                if temppacket.extract(2) == "PAUSE":
                    pauselen = temppacket.extract(3)
                    time.sleep(int(pauselen))
            else:
                if temppacket.extract(1) in ['EBR', 'WSA', 'WHIR', 'WPD', 'WD', 'WFT']:
                    logdata = FileTransfer.UUID.sub(str(sessionid), logdata)
                returndata = pktprocessor.processinput(logdata)
                for rdata in returndata[0]:
                    if rdata:
                        tlnmgr.adddata(sessionid, rdata)
                        tlnmgr.datahandler(sessionid)
        else:
            break
        if logdelay:
            time.sleep(logdelay / 1000)
    tcmd = Command()
    tcmd.msg("FLASH", ['Log playback has been completed.'], [])
    tcmd.setcommand("type", "MSG")
    tlnmgr.adddata(sessionid, tcmd)
    tlnmgr.datahandler(sessionid)


class LogFileReader(object):
    '''
    Read entries from a log file
    '''

    def __init__(self, logfile: str):
        '''
        Constructor
        '''
        self._logfilename = logfile
        self._buffer = ""
        try:
            self._logstream = open(logfile, "r", encoding="iso-8859-1")
        except IOError:
            logging.error("Failed to open logfile " + logfile)
            raise

        # Build our regular expressions

        # WinGem Style Packets
        self._outre = re.compile(r"\[[\d :]*\] OUT([\s\w])*\| ")
        self._inre = re.compile(r"\[[\d :]*\] IN([\s\w" +
                                re.escape(punctuation.replace("|", "")) + r"])*\| ")

        # WebDirect Style Packets
        self._outrewd = re.compile(r"\[[\d\- ,:]*\](\w|\-)*\|\|OUT\|")
        self._inrewd = re.compile(r"\[[\d\- ,:]*\](\w|\-)*\|\|IN \|")

        # This gets both timestamps
        self._timestampre = re.compile(r"\[[\d,\- :]*\]")

    def nextpacket(self, includestxetx=True):
        ''' Get the next packet '''
        completepacket = False
        fullpacket = ""
        while not completepacket:
            if self._buffer:
                dataread = self._buffer
                self._buffer = ""
            else:
                dataread = self._logstream.readline()
                if not dataread:
                    completepacket = True
                dataread = dataread.rstrip()
            # print("processing " + dataread)
            # regular expression to find beginning markers
            hasout = self._outre.match(dataread)
            hasin = self._inre.match(dataread)
            hasout2 = self._outrewd.match(dataread)
            hasin2 = self._inrewd.match(dataread)
            hastimestamp = self._timestampre.match(dataread)
            if completepacket:
                # if not dataread:
                # no data, we're done
                completepacket = True
            elif not (hasout or hasout2) and not (hasin or hasin2) and not fullpacket:
                # bad crap
                pass
            elif (hasin or hasin2) and fullpacket:
                completepacket = True
                self._buffer = dataread
            elif hastimestamp and fullpacket:
                # end of packet, got timestamp though
                completepacket = True
            elif (hasout or hasout2) and fullpacket:
                completepacket = True
            elif hasout or hasout2:
                # throw away line
                pass
            elif hasin:
                # start of packet
                fullpacket = self._inre.sub("", dataread)
            elif hasin2:
                # start of packet
                fullpacket = self._inrewd.sub("", dataread)
            elif fullpacket and dataread:
                # continuing a packet
                fullpacket += chr(10)
                fullpacket += self._inre.sub("", dataread)
        if includestxetx and fullpacket:
            fullpacket = chr(2) + fullpacket + chr(3)
        if fullpacket:
            fullpacket = fullpacket.replace(chr(253), WinGemPacket.VM).replace(
                chr(254), WinGemPacket.AM).replace(chr(252), WinGemPacket.SM)
        return fullpacket

    def close(self):
        ''' Close down log file '''
        self._logstream.close()
