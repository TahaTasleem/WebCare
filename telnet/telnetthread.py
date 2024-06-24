'''
Created on Oct 12, 2016

@author: bouchcla
'''
import logging
import os
import re
import shutil
import socket
import sys
import telnetlib
import time
import traceback
from collections import deque
from ssl import SSLWantWriteError
from threading import Event, current_thread
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from paramiko import AuthenticationException
from _collections import OrderedDict

# this import is used, but pylint can't pick it up
import connector.logging  # pylint: disable=unused-import
from components import logfilemanager
from components.command import Command
from components.commandbar import CommandBar
from connector import resource
from connector.configuration import CONFIG
from connector.packetprocessor import PacketProcessor
from connector.resource import loadstring
from connector.utility import unicodetoascii
from connector.wingempacket import WinGemPacket

from telnet.ssh import SSH
from telnet.telnetssl import TelnetSSL


class CommDataSet(object):
    ''' class to  manage communication '''

    def __init__(self, enable_logging = False):
        ''' Constructor '''
        self.id = None
        self.outputq = deque()
        self.inputq = deque()
        self.renderq = dict()
        self.renderid = 0
        self.screenstack = []
        self.externalfiles = dict()
        self.lasttouch = 0
        self.suppresslog = False
        self.stop = False
        self.commandbar = CommandBar(enable_logging)
        self.connected = False
        self.socketid = None
        self.telnetmgr = None


class TelnetThread(object):
    ''' Manages a telnet thread connection for WebDirect '''

    # =========================================================================
    # _SCRIPTERROR = {"WDERR-SCRIPT-001" : "Password change required",
    #                 "WDERR-SCRIPT-002" : "User ID or password failed",  # (LOCAL)
    #                 "WDERR-SCRIPT-003" : "Host has terminated the connection",  # (LOCAL)
    #                 "WDERR-SCRIPT-004" : "Your acount is disabled",
    #                 "WDERR-SCRIPT-005" : "UniVerse user limit has been reached",
    #                 "WDERR-SCRIPT-006" : "Account doesn't exist or is invalid",
    #                 "WDERR-SCRIPT-007" : "This version of UniVerse has expired",
    #                 "WDERR-SCRIPT-008" : "Terminal setting is not correct"}
    # =========================================================================
    _SCRIPTERROR = {"WDERR-SCRIPT-001": resource.loadstring("IDS_ERROR0107"),
                    "WDERR-SCRIPT-002": resource.loadstring("IDS_ERROR0108"),
                    "WDERR-SCRIPT-003": resource.loadstring("IDS_ERROR0109"),
                    "WDERR-SCRIPT-004": resource.loadstring("IDS_ERROR0110"),
                    "WDERR-SCRIPT-005": resource.loadstring("IDS_ERROR0111"),
                    "WDERR-SCRIPT-006": resource.loadstring("IDS_ERROR0112"),
                    "WDERR-SCRIPT-007": resource.loadstring("IDS_ERROR0113"),
                    "WDERR-SCRIPT-008": resource.loadstring("IDS_ERROR0114"),
                    "WDERR-SCRIPT-009": resource.loadstring("IDS_ERROR0115"),
                    "WDERR-SCRIPT-010": resource.loadstring("IDS_ERROR0116")}


    # Which errors do NOT launch an external URL
    _SCRIPTERRORLOCAL = {"WDERR-SCRIPT-002", "WDERR-SCRIPT-003", "WDERR-SCRIPT-009",
                         "WDERR-SCRIPT-010"}

    def __init__(self,
                 host: str,
                 ssl: bool,
                 user: str = None,
                 password: str = None,
                 account: str = None,
                 ssh: bool = False,
                 passcode: str = None,
                 startdata: str = None):
        ''' Constructor '''
        # Set SSL-ness
        if CONFIG["ALLOWFREEFORMLOGIN"] and ssl is not None:
            self._ssl = ssl
        else:
            self._ssl = CONFIG["SSL"][host] if host in CONFIG["SSL"] else True
        self._ssh = ssh

        # Set port defaults
        if self._ssh:
            self._port = 22
        elif self._ssl:
            self._port = 992
        else:
            self._port = 23

        # Determine host and port override
        hostinfo = host.split(":")
        self._host = hostinfo[0] if hostinfo else ""
        if len(hostinfo) > 1:
            self._port = int(hostinfo[1])

        self._user = user
        self._password = password
        self._account = account
        self._passcode = passcode
        self._startdata = startdata

        self._foundtermtypeprompt = False

        # Tokens expected during OS phase
        self._expectos = ["ogin",
                          "ame",
                          "assword",
                          "ccount",
                          "TERM =",
                          "UniVerse Command Language"]

        # Tokens expected during UV phase
        self._expectuv = ["Your VOC is out of date. Update to current release (Y/N)?",
                          "Y>",
                          ">",
                          "Terminal Type",
                          "TYPE TERMINAL",
                          "Menu item number:"]

        # Start with OS-level tokens
        self._expect = self._expectos
        self._osoruv = "os"

        # =======================================================================
        # Same token for invalid account as for invalid user/pw. Handled later on.
        # OrderedDict is used so more serious errors can be listed earlier.
        #   RHAXIS reports BOTH "ermission denied" AND "Login incorrect" when locked
        #     but only "Login incorrect" if it's a username/password issue
        # =======================================================================
        # pylint: disable=line-too-long
        self._expectexception = OrderedDict([("Your password was", "WDERR-SCRIPT-001"),
                                             ("change your password", "WDERR-SCRIPT-001"),
                                             ("ermission denied", "WDERR-SCRIPT-004"),
                                             ("account has restrictions that prevent you from logging on",
                                              "WDERR-SCRIPT-004"),
                                             ("ncorrect", "WDERR-SCRIPT-002"),
                                             ("nvalid", ""),
                                             ("ccount is disabled", "WDERR-SCRIPT-004"),
                                             ("hanging password for", "WDERR-SCRIPT-001"),
                                             ("UniVerse user limit has been reached",
                                              "WDERR-SCRIPT-005"),
                                             ("UniVerse user limit on server has been reached",
                                              "WDERR-SCRIPT-005"),
                                             ("account entered does not exist", "WDERR-SCRIPT-006"),
                                             ("This version of UniVerse has expired",
                                              "WDERR-SCRIPT-007"),
                                             ("expired", "WDERR-SCRIPT-001"),
                                             ("not a valid account", "WDERR-SCRIPT-006"),
                                             ("Menu item number:", "WDERR-SCRIPT-008"),
                                             ("terminating", "WDERR-SCRIPT-003"),
                                             ("BAD PASSWORD", "WDERR-SCRIPT-009"),
                                             ("passwords do not", "WDERR-SCRIPT-010")])

        self._scriptfinished = False

        self._dataset = None
        self._channel = None
        self._pktprocessor = None
        self._lastsent = 0

        self._tempstore = list()

        self.ssl_errors = 0
        self.ispassexpired = False #flag will be used in password change dialog in ssh
        self.ispasschangetriggered = False #additional flag to support password change

    def runconnection(self, dataset: CommDataSet,
                      shutdown: Event = None):
        '''
        Runs connection to telnet
        Runs in it's own thread
        '''

        # Open Telnet Connection
        self._dataset = dataset
        if not self._open():
            return

        connectionopen = True
        cleanuphost = False
        closedbybrowser = False

        self._pktprocessor = PacketProcessor(
            str(dataset.id), dataset.screenstack,
            dataset.externalfiles, dataset.commandbar, self._startdata)

        while connectionopen and self._dataset.connected:

            if shutdown is not None and shutdown.is_set():
                logging.info("Shutdown Event Signalled")
                connectionopen = False

            finalinputdata = self._channelloop()

            # done loop, handle data from telnet
            if finalinputdata:
                # logging.info("Input=" + finalinputdata)
                connectionopen = self._processdata(finalinputdata)

            # check to see if we are still being polled
            # allow for 5 minutes of non-polling
            checktime = (time.time() - (60 * CONFIG['BROWSERTIMEOUT']))
            if self._dataset.lasttouch and \
                    self._dataset.lasttouch < checktime:
                # browser has gone away, disconnect
                logging.info("No browser connection, terminating telnet session")
                logging.debug("Last Touch: %i vs current: %i", self._dataset.lasttouch, checktime)
                connectionopen = False
                cleanuphost = True
            if self._dataset.stop:
                logging.info("told to stop by browser disconnect")
                connectionopen = False
                cleanuphost = True
                closedbybrowser = True

            # yield to other threads
            time.sleep(0)

        if cleanuphost:
            self._cleanuphost(closedbybrowser)

        if self._dataset.socketid:
            # send any remaining data back over websocket
            self._dataset.telnetmgr.datahandler(current_thread().name)

        # cleanup socket and data structures
        self._channel.close()
        self._cleanupsession()
        self._dataset.inputq.clear()

        # make sure we exit our thread
        sys.exit(0)

    def _interactiveprompt(self, promptmsg: str, title: str, inputtype: str):
        ''' handle request for extra data during login '''
        # logging.info("Requesting more info: %s", promptmsg)
        cmd = Command()
        instructions = "<br/>".join(promptmsg.splitlines())
        cmd.question(title, instructions, inputtype)
        self._dataset.outputq.append(cmd)
        waittime = 0
        while not self._dataset.socketid and waittime < 60:
            # may need to wait a bit for the websocket to be established
            time.sleep(0.1)
            waittime += 0.1
        if self._dataset.socketid:
            # send data back over websocket
            self._dataset.telnetmgr.datahandler(self._dataset.id)
        waittime = 0
        while not self._dataset.inputq and waittime < 600:
            # wait for answer from client
            # cap wait time at 10 minutes,
            # host will likely kill it before then
            time.sleep(0.1)
            waittime += 0.1
        result = None
        if self._dataset.inputq:
            data = self._dataset.inputq.pop()
            # data is prepended with <ESC>WHIR:
            if data[:6] == chr(27) + "WHIR:":
                result = data[6:]
                # remove the \r that the input route adds
                if result[-1] == chr(10) or result[-1] == chr(13):
                    result = result[:-1]
        # logging.info("Got? %s", result)
        self._dataset.inputq.clear()
        return result

    def _open(self):
        ''' open telnet connection '''
        logging.info(
            "Starting Telnet for %s on port %s", self._host, self._port)

        self._dataset.connected = True
        try:
            if self._ssh:
                self._channel = SSH()
                try:
                    # ssh requires authentication on a different level,
                    # so remove these from script processor
                    self._expect.remove("ogin")
                    self._expect.remove("ame")
                    self._expect.remove("assword")
                    self._channel.open(self._host, self._port, self._user,
                                       self._password, self._passcode, self._interactiveprompt)
                except AuthenticationException:
                    self._addlogout(resource.loadstring("IDS_ERROR0108"), True)
                    self._dataset.connected = False
            else:
                self._channel = TelnetSSL(self._ssl)
                self._channel.open(self._host, self._port)
            self._lastsent = time.time()
        except Exception:  # pylint: disable=W0703
            # Any exception here is a failure to connect
            errmsg = loadstring("IDS_ERROR0071") + " " + self._host + " (WDERR-LOGIN-001)"
            logging.error(errmsg)
            logging.error(traceback.format_exc().splitlines())
            self._dataset.connected = False
            self._addlogout(errmsg, True)

        if self._dataset.socketid and self._dataset.outputq:
            self._dataset.telnetmgr.datahandler(self._dataset.id)

        return self._dataset.connected

    def _cleanuphost(self, closedbybrowser = False):
        ''' try to cleanly cleanup host session '''
        # print("Attempting to cleanup host")

        try:
            starttime = time.time()
            connectionopen = True
            donequit = False
            doneoff = False
            doneexittolevel = False

            while connectionopen and self._dataset.connected:

                finalinputdata = self._channelloop()

                if finalinputdata:
                    #logging.info("Input=" + finalinputdata)
                    connectionopen = self._processdata(finalinputdata)

                if (time.time() - starttime) > 60:
                    connectionopen = False

                if not doneexittolevel and not self._pktprocessor.canexit:
                    outputstr = chr(27) + "EXITTOLEVEL" + chr(13)
                    self.write(outputstr)
                    logging.info("Attempting EXITTOLEVEL command.")
                    logging.getLogger("packetlogger").packet("OUT|" + outputstr)
                    doneexittolevel = True

                    if closedbybrowser:
                        self._pktprocessor.canexit = True

                if self._pktprocessor.canexit and not donequit:
                    # host says we can leave
                    outputstr = chr(27) + "QUIT!" + chr(13)
                    self.write(outputstr)
                    logging.info("Attempting QUIT! command.")
                    logging.getLogger("packetlogger").packet("OUT|" + outputstr)
                    donequit = True

                if not doneoff:
                    for qitem in self._dataset.outputq:
                        if qitem.gettype() == "TCL":
                            # we are at TCL, attempt to leave cleanly
                            outputstr = "OFF" + chr(13)
                            logging.info("Attempting OFF command.")
                            self.write(outputstr)
                            logging.getLogger("packetlogger").packet("OUT|" + outputstr)
                            doneoff = True

                if self._dataset.outputq:
                    # keep this clean
                    self._dataset.outputq.clear()

        except:  # pylint: disable=W0702
            # don't care about any errors, likely means the host disconnected us
            logging.info("Host disconnected while trying to cleanly quit.")

    def _channelloop(self):
        ''' check for data from telnet '''

        outputdata = ""
        finalinputdata = ""
        fullinputdata = []

        if self._dataset.inputq:
            outputdata = unicodetoascii(self._dataset.inputq.popleft())

        if (time.time() - self._lastsent) > 360 and not outputdata:
            # we haven't sent anything in 5 minutes, so send a keep alive
            # print("Sending Keep alive", (time.time() - self._lastsent))
            if not self._ssh:
                self._channel.sock.sendall(telnetlib.IAC + telnetlib.NOP)
                # reset the timer
                self._lastsent = time.time()

        try:
            if outputdata:
                # print("Output=" + outputdata)
                if outputdata[:3] == chr(27) + "WD":
                    # redirect output to input queue
                    # local webdirect data goes to packet processor
                    if outputdata[-1] in (chr(10), chr(13)):
                        outputdata = outputdata[:-1]
                    fullinputdata.append(chr(2) + outputdata[1:] + chr(3))
                else:
                    if self._dataset.suppresslog:
                        self._dataset.suppresslog = False
                        logdata = "*****"
                    else:
                        logdata = outputdata
                    logging.getLogger("packetlogger").packet("OUT|" + logdata)
                    retrywrite = True

                    # chunk the data into 65K pieces
                    # for data in chunkstring(outputdata, 65535):
                    while retrywrite:
                        try:
                            # self._channel.write(data.encode("ISO-8859-1"))
                            if not self._ssh:
                                self._channel.sock.settimeout(0.2)
                            self.write(outputdata)
                            self._lastsent = time.time()
                            retrywrite = False
                        except SSLWantWriteError:
                            # need to retry after waiting a bit
                            # should we not wait longer than a certain amount of time,
                            # or break it into smaller chunks?
                            self.ssl_errors += 1
                            # pass
                    # let other side know we are ready
                    if not self._ssh:
                        self._channel.sock.sendall(telnetlib.IAC + telnetlib.GA)

            inputdata = self._channel.read().replace(chr(0),"")
            if inputdata:
                fullinputdata.append(inputdata)

        except (EOFError, ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as error:
            # disconnected
            logging.info("Disconnected: %s", str(error))
            self._addlogout("Disconnected", True)

        except socket.timeout:
            # print("timeout", self._channel.eof)
            # don't care if socket times out
            pass

        except (IOError, socket.error):
            logging.error("IOError: " + traceback.format_exc())
            self._dataset.connected = False

        if fullinputdata:
            finalinputdata = "".join(fullinputdata)

        if self._channel.eof:
            # because we use a timeout, we can get to EOF without an error now
            logging.info("Host closed connection.")

            if self.ispasschangetriggered:
                self._addlogout("Password changed, try logging in using new password.", False)
            else:
                self._addlogout("Disconnected", True)

        if self.ssl_errors:
            # print("ssl errors during write", self.ssl_errors)
            self.ssl_errors = 0

        return finalinputdata

    def _processdata(self, finalinputdata):
        ''' Process Incoming Data '''

        connectionopen = True

        # respond to a term request right away
        if chr(5) in finalinputdata:
            self._dataset.inputq.append("WinGem-3000.0.4" + chr(13))
            finalinputdata.replace(chr(5), "")

        # this should be passed to the packet processor at this point
        # instead of handling it directly
        data = self._massagedata(finalinputdata)
        self._checkforscriptend(data)
        returnobjects, hostdata = self._pktprocessor.processinput(data)

        for robj in returnobjects:
            if self._pktprocessor.lockscreen:
                self._tempstore.append(robj)
            else:
                if self._tempstore:
                    self._dataset.outputq.extend(self._tempstore)
                    self._tempstore.clear()
                self._dataset.outputq.append(robj)
            if robj.gettype() == "TCL":
                connectionopen = self._processscript(robj.getdata(),
                                                     connectionopen)
        for hobj in hostdata:
            self._dataset.inputq.append(hobj)

        if self._pktprocessor.disconnect:
            # need a cleaner way to do this
            logging.info("Disconnect option flagged.")
            self._channel.close()
            connectionopen = False

        if self._dataset.socketid and self._dataset.outputq:
            # send data back over websocket
            self._dataset.telnetmgr.datahandler(self._dataset.id)

        return connectionopen

    def _addlogout(self, msg: str = None, error: bool = None):
        ''' Add logout to outbound queue '''
        if msg:
            logging.info("logout: " + msg)
        cmd = Command()
        cmd.logout(msg=msg, error=error)
        self._dataset.outputq.append(cmd)
        self._dataset.connected = False

    def _cleanupsession(self):
        ''' Cleanup the session directories '''
        # remove the fake abc session
        sid = current_thread().name
        # remove guid from the log manager list
        logfilemanager.removeusersession(sid)
        shutil.rmtree(
            'static/data/' + sid, ignore_errors=True)
        # TODO: handle version folders in a clean way
        basepath = 'static/data/'
        for fname in os.listdir(basepath):
            path = os.path.join(basepath, fname)
            if os.path.isdir(path) and re.search(r"v[\d]{2,4}[\dAB]{0,1}", path):
                shutil.rmtree(path + "/" + sid, ignore_errors=True)

    def _massagedata(self, inputdata):
        ''' Does a translation of host data '''
        chars = [WinGemPacket.GUIAM, WinGemPacket.GUIVM, WinGemPacket.GUISM]
        repchars = [WinGemPacket.AM, WinGemPacket.VM, WinGemPacket.SM]
        for x, y in zip(chars, repchars):
            if x in inputdata:
                inputdata = inputdata.replace(x, y)
        return inputdata

    def _processscript(self, inputdata: str, connectionopen: bool):
        ''' Looks for expected values and handles them '''

        # Handle expected tokens
        if not self._scriptfinished:

            if self._ssh: # handle password change ssh
                if (not self.ispassexpired) and "assword" in inputdata and "xpired" in inputdata:
                    self.ispassexpired = True

                if self.ispassexpired and "urrent" in inputdata and "assword" in inputdata:
                    self.ispassexpired = False
                    self.ispasschangetriggered = True
                    self._expect.append("assword")

                if self.ispasschangetriggered and 'ew ' in inputdata and 'assword' in inputdata:
                    self._dataset.suppresslog = True

            matchlist = [
                substring for substring in self._expect if substring in inputdata]
            if matchlist:
                if "ogin" in matchlist or "ame" in matchlist:
                    if self._user:
                        self._dataset.inputq.append(self._user + chr(13))
                    self._expect.remove("ogin")
                    self._expect.remove("ame")
                    # self._expect.append("assword")
                elif "assword" in matchlist:  # Bug for bug, baby!
                    if self._password:
                        self._dataset.inputq.append(self._password + chr(13))
                        self._dataset.suppresslog = True
                    self._expect.remove("assword")
                    # self._expect.append("ccount")
                elif "ccount" in matchlist:
                    if self._account:
                        self._dataset.inputq.append(self._account + chr(13))
                    self._expect.remove("ccount")
                elif "TERM =" in matchlist:
                    self._dataset.inputq.append(chr(13))
                    # self._expect.remove("TERM =")
                elif "UniVerse Command Language" in matchlist:
                    # Switch to UV-level tokens
                    self._expect = self._expectuv
                    self._osoruv = "uv"
                    # Rerun using new list in case there's more in this block
                    connectionopen = self._processscript(
                        inputdata, connectionopen)
                elif "Your VOC is out of date. Update to current release (Y/N)?" in matchlist:
                    self._dataset.inputq.append("Y" + chr(13))
                elif "Y>" in matchlist:
                    # Keeps following ">" check from making a bad match with
                    # port logoff prompt
                    pass
                elif ">" in matchlist:
                    if self._foundtermtypeprompt:
                        self._finishscript(True)
                        logging.debug("Script Complete: At TCL")
                    else:
                        self._foundtermtypeprompt = True
                        self._dataset.inputq.append("ASK.TERM" + chr(13))
                elif "Terminal Type" in matchlist:
                    self._foundtermtypeprompt = True
                elif "TYPE TERMINAL" in matchlist:
                    self._foundtermtypeprompt = True

            if not self._expect:
                self._finishscript()
                logging.debug("Script Complete: Found last token")
            else:
                matchlist = [substring
                             for substring in self._expectexception
                             if substring in inputdata]
                if matchlist:
                    connectionopen = True
                    # Exception exists
                    if self._expectexception[matchlist[0]] == 'WDERR-SCRIPT-001':
                        self._finishscript(True, False)
                        if not self._ssh:
                            self._dataset.inputq.append(self._password + chr(13))
                    else:
                        # Update error message for "nvalid" token (exists in both
                        # sections)
                        if matchlist[0] == "nvalid":
                            if self._osoruv == "os":
                                # Invalid credentials
                                self._expectexception[
                                    "nvalid"] = "WDERR-SCRIPT-002"
                            else:
                                # Invalid account
                                self._expectexception[
                                    "nvalid"] = "WDERR-SCRIPT-006"

                        # Handle exception
                        connectionopen = self._processscriptexception(matchlist[0],
                                                                    connectionopen)
        return connectionopen

    def _checkforscriptend(self, data: str):
        ''' Signal end of script if prompting packet found '''
        if not self._scriptfinished:
            if any(substring in data for substring in
                   [chr(2) + "WPD", chr(2) + "WPN", chr(2) + "WPP"]):
                self._finishscript()
                logging.debug("Script Complete: Found prompting packet")

    def _finishscript(self, showtcl: bool = False, markfinishscript: bool = True):
        self._scriptfinished = markfinishscript
        # Allow TCL if necessary
        cmd = Command()
        cmd.doneconnecting()
        self._dataset.outputq.append(cmd)
        if showtcl:
            cmd2 = Command()
            cmd2.showtcl()
            self._dataset.outputq.append(cmd2)

    def _processscriptexception(self,
                                matchedtoken: str,
                                connectionopen: bool):
        ''' Handle exception case encountered by login process '''

        # matchedtoken only ever comes in as a result of matching in _expectexception
        errcode = self._expectexception[matchedtoken]
        exturl = CONFIG["LOGINEXCEPTIONURL"]

        # Close connection
        connectionopen = False

        # Clear pending items
        self._dataset.outputq.clear()

        logging.info("Login script found '" + matchedtoken + "'.")

        # Do we have a configured exception URL and error is NOT handled
        # locally?
        if errcode not in TelnetThread._SCRIPTERRORLOCAL and exturl:
            # Redirect to provided URL, passing it some structure of useful
            # information

            # Parse configured URL
            exturlbits = urlparse(exturl)

            # Make list so writeable
            exturlbits = list(exturlbits)

            # Ensure protocol exists
            exturlbits[0] = exturlbits[0] if exturlbits[0] != '' else 'http'

            # Parse and update query
            queryparms = parse_qs(exturlbits[4])
            queryparms["err"] = errcode
            # queryparms["return"] = "" # Handled in webdirect.js
            exturlbits[4] = urlencode(queryparms)

            # Rebuild external URL
            exturl = urlunparse(exturlbits)

            logging.debug("URL: '" + exturl + "'.")

            # Logout
            self._addlogout()

            # Send command to navigate to external URL
            cmd = Command()
            cmd.navext(exturl)
            self._dataset.outputq.append(cmd)
        else:
            errmsg = TelnetThread._SCRIPTERROR[errcode] + " (" + errcode + ")"

            # Logout
            self._addlogout(errmsg, True)

        logging.info("Login terminated.")

        return connectionopen

    def write(self, data):
        ''' Single write point to handle SSH vs Telnet '''
        outdata = ""
        try:
            outdata = data.encode("ISO-8859-1")
        except UnicodeEncodeError as einfo:
            # log the error
            if einfo.start >= 0 and einfo.end >= 0:
                # Extract bad character
                badchar = data[int(einfo.start):int(einfo.end)]
                # badchar = badchar.encode(
                #    "ISO-8859-1", "xmlcharrefreplace").decode("ISO-8859-1")
                badchar_hex = " ".join(f"{ord(i):#0x}" for i in badchar)
                logging.info(
                    "Failed to encode following character(s) '" + badchar +
                    "' (" + badchar_hex + ")")
            else:
                logging.info(
                    "Failed to encode a character '" + str(einfo) + "'")
            # redo it, but ignore the error
            outdata = data.encode("ISO-8859-1", errors='ignore')
        if self._ssh:
            self._channel.write(outdata)
        else:
            self._channel.write(outdata)
