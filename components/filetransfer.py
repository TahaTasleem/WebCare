'''
Created on Oct 19, 2016

@author: bouchcla
'''
import base64
import errno
import logging
import os
import re
import traceback
import uu
from werkzeug.utils import secure_filename

from components.wdobject import BaseWDObject
from connector.configuration import CONFIG
from connector.wingempacket import WinGemPacket


def fixslashes(filepath: str):
    ''' Fix file path slashes '''
    if os.sep != "/" and "/" in filepath:
        filepath = filepath.replace("/", os.sep)
    if os.sep != "\\" and "\\" in filepath:
        filepath = filepath.replace("\\", os.sep)
    return filepath


def getfiletuple(filename: str, filemode, sessionid, isdir=False):
    ''' determine directory for file '''
    # most paths given will be in windows format
    #  but some may be in unix format, need to handle both cases
    # don't use directory if we are given an absolute path
    #    this should only be the case for tests
    # absolute path can start with
    #    / (unix) or drive: (windows) or \\ (UNC path)
    # also, ignore static/ directory requests

    # fix filename to work in unix/windows regardless of os
    filename = fixslashes(filename)

    # If given empty string, return empty strings
    if not filename:
        return "", ""

    # everything after this should be using os.sep
    trailingslash = False
    if filename[-1] == os.sep:
        trailingslash = True
    origfilename = filename
    if isdir and not trailingslash:
        trailingslash = True
    filename = os.path.normpath(filename)
    ignoredir = False
    if filename[0:1] == os.sep:
        ignoredir = True
    if filename[0:12] == "static" + os.sep + "data" + os.sep:
        ignoredir = True
    if filename[0:7] == "static" + os.sep:
        ignoredir = True
    if filename[0:8] == "uploads" + os.sep:
        ignoredir = True
        # check to see if host added version, if they did, remove it
        hasversion = FileTransfer.VERSIONRE.search(filename)
        if hasversion:
            filename = re.sub(FileTransfer.VERSIONRE, "", filename)

    if ":" in filename or origfilename[0:2] == os.sep + os.sep:
        # absolute windows path or share folder network file
        ignoredir = False
        # GC, so likely V18 or V17
        result = []
        # AXIS, so likely V20171 format
        reg_compile = re.compile(r"(v|V)\d\d\d\d\d$")
        if CONFIG['PRODUCT'] != "AXIS":
            reg_compile = re.compile(r"(v|V)\d\d$")
        for _, dirnames, _ in os.walk("static/data"):
            result.extend([dirname for dirname in dirnames if reg_compile.match(dirname)])
        # get largest first
        result.sort(reverse=True)
        if result:
            filename = "." + os.sep + result[0] + os.sep + "000" + \
                os.sep + os.path.basename(filename)
        else:
            # test case only
            filename = "." + os.sep + "v20171" + os.sep + "000" + \
                os.sep + os.path.basename(filename)
    if trailingslash:
        # normpath will remove a trailing slash
        filename += os.sep

    # do we have a version?
    havever = FileTransfer.VERSIONRE.search(filename)
    haveverport = FileTransfer.VERSIONPORTRE.search(filename)
    haveport = FileTransfer.PORTRE.search(filename)
    haveuuid = FileTransfer.UUID.search(filename)
    defineddir = os.path.dirname(filename)
    defineddir += os.sep
    if not ignoredir:
        directory = "static" + os.sep + "data" + os.sep
        if filemode == "READ":
            pass
            # if origfilename[0:2] != "." + os.sep:
            #    directory = "uploads" + os.sep
        if havever:
            directory += havever.group() + os.sep
        # this converts  vXXXXX/port/file to
        #                static/vXXXXX/sessionid/file
        #     and        port/file to
        #                static/sessionid/file
        #     and        file to
        #                static/sessionid/file
        if haveverport:
            directory += sessionid
            directory = defineddir.replace(haveverport.group(), directory)
        elif havever:
            directory = defineddir.replace(havever.group(), directory)
        elif haveport:
            # we look for port\, so need to replace with ending slash
            directory += sessionid + os.sep
            directory = defineddir.replace(haveport.group(), directory)
        else:
            directory += sessionid + os.sep + defineddir
    elif haveverport and not haveuuid:
        # sometimes we get a static directory with a port # and version
        # because someone is trying to be smart and use get data directory
        directory = defineddir.replace(haveverport.group(), havever.group() +
                                       os.sep + sessionid + os.sep)
    elif haveport and not haveuuid:
        # sometimes we get a static directory with a port #
        # because someone is trying to be smart and use get data directory
        # be careful, could overwrite a UUID
        directory = defineddir.replace(haveport.group(), sessionid + os.sep)
    else:
        directory = defineddir
    directory = os.path.normpath(directory)
    if directory != "/":
        directory += os.sep
    filename = os.path.basename(filename)

    # return directory, filename
    return fixslashes(directory), secure_filename(fixslashes(filename))


class FileTransfer(BaseWDObject):
    ''' File Transfer Object '''

    # Regular Expressions to get version, port
    _VERSION = r"(V|v)[\d]{2,4}[\d\w]{0,1}"
    _PORT = r"[\d]{1,10}"
    VERSIONRE = re.compile(r"\b" + _VERSION + r"\b")
    VERSIONPORTRE = re.compile(r"\b" + _VERSION + "\\" + os.sep + _PORT + r"\b")
    PORTRE = re.compile(r"\b" + _PORT + r"\b")
    UUID = re.compile(
        r"\b" + r"[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}" + r"\b",
        re.IGNORECASE)

    def __init__(self, sessionid):
        ''' Constructor '''
        super(FileTransfer, self).__init__("FILETRANSFER")

        self.origfilename = ""
        self._handle = ""
        self._sessionid = str(sessionid)
        self.filemode = ""
        self.filename = ""
        self._filehandle = None
        self._dir = ""
        self._error = False
        self.showui = False

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Add a packet to the file transfer object '''
        processed = False
        hostdata = ""
        if packet.packettype() == "WFT":
            subcommand = packet.extract(2)
            if subcommand == "OPEN":
                # logging.info("Open File")
                processed, hostdata = self._openfile(packet)
            elif subcommand == "READ":
                # logging.info("Read File")
                processed, hostdata = self._readdata(packet)
            elif subcommand == "WRITE":
                # logging.info("Write File")
                processed, hostdata = self._writedata(packet)
            elif subcommand == "CLOSE":
                # logging.info("Close File")
                processed, hostdata = self._closefile(packet)
            elif subcommand == "CHECKFILE":
                # logging.info("Check File")
                processed, hostdata = self._checkfile(packet)
            elif subcommand == "DELETE":
                # logging.info("Delete File")
                processed, hostdata = self._deletefile(packet)
        elif packet.packettype() == "WDF":
            # finished an upload
            if packet.extract(2) == "DONE":
                # file is ready, we can respond to host
                newpacket = WinGemPacket("WFT" +
                                         WinGemPacket.AM + "OPEN" +
                                         WinGemPacket.AM + self._handle +
                                         WinGemPacket.AM + self.filemode +
                                         WinGemPacket.AM + packet.extract(3))
                processed, hostdata = self._openfile(newpacket)
            elif packet.extract(2) == "CANCEL\r" or packet.extract(2) == "CANCEL":
                # not getting a file back
                hostdata = "0" + \
                    WinGemPacket.VM + "0" + WinGemPacket.VM + "54" + \
                    WinGemPacket.VM + "User cancelled upload."
                processed = True

        return processed, hostdata, self

    def getfilenamemap(self):
        ''' return a tuple of original file to local filename '''
        return (self.origfilename, self._dir + self.filename)

    def _openfile(self, packet: WinGemPacket):
        ''' Create File on Local System '''
        self._handle = packet.extract(3)
        self.filemode = packet.extract(4)
        self.filename = packet.extract(5)
        self.origfilename = self.filename
        hostdata = None

        # determine directory of file
        self._dir, self.filename = \
            getfiletuple(self.filename, self.filemode, self._sessionid)
        # default to read
        openmode = "rb"
        if self.filemode == "APPEND":
            openmode = "ab"
        elif self.filemode == "WRITE":
            openmode = "wb"
            # make sure our directory exists
            self._createdir()

        # try opening the file
        try:
            # logging.debug("File to open=" + self._dir + self.filename)
            self._filehandle = open(
                self._dir + self.filename, mode=openmode)
            hostdata = "1" + WinGemPacket.VM + "0"
        except IOError:
            if openmode == "rb":
                # request input from user
                self.showui = True
                # print(traceback.format_exc())
            else:
                logging.error(
                    "Failed to open file " + self._dir + self.filename)
                formatted_lines = traceback.format_exc().splitlines()
                hostdata = "0" + \
                    WinGemPacket.VM + "0" + WinGemPacket.VM + "52" + \
                    WinGemPacket.VM + formatted_lines[-1]
        return True, hostdata

    def _closefile(self, packet: WinGemPacket):
        ''' Close File '''
        filehandle = packet.extract(3)
        encoded = packet.extract(4)
        processed = True
        success = "1"
        # logging.info("Close Packet, Handle? " + filehandle + " == " + self._handle)

        # close the packet
        if filehandle == self._handle:
            if self._filehandle is not None:
                try:
                    self._filehandle.close()
                    if self._error:
                        success = "0"
                except IOError:
                    success = "0"
                    logging.error("Failed to close file handle " + self._handle)
            else:
                success = "-1"
        else:
            processed = False

        if encoded and processed and success == "1":
            # do we need to decode the file
            if encoded == "UUDECODE":
                self._uudecode()
                # remove uue from filename
                self.filename = self.filename.replace(".uue", "")

        hostdata = None
        if processed:
            hostdata = success + WinGemPacket.VM + self._dir + \
                self.filename + WinGemPacket.VM + "WFTC"
        self._complete = True
        return processed, hostdata

    def _uudecode(self):
        tfile = open(self._dir + self.filename, "rb")
        finalfilename = self.filename.replace(".uue", "")
        # check to see if decoded file exists, if it does, delete it
        if os.path.exists(self._dir + finalfilename):
            os.remove(self._dir + finalfilename)
        try:
            curdir = os.getcwd()
            os.chdir(self._dir)
            uu.decode(tfile, out_file=finalfilename, quiet=True)
            os.chdir(curdir)
        except uu.Error as exc:
            logging.error(
                "Failed to decode file " + self._dir + self.filename + chr(10) +
                "(" + str(exc) + ")")
            os.chdir(curdir)
        tfile.close()
        # delete the UUE file
        if "uue" in self.filename:
            os.remove(self._dir + self.filename)

    def _deletefile(self, packet: WinGemPacket):  # pylint: disable=W0613
        ''' Delete file
            Note: we don't do anything with this, since
                all files will be deleted after a telnet session
                closes
        '''
        self._complete = True
        return True, "1"

    def _writedata(self, packet: WinGemPacket):
        ''' Write data to the file '''
        filehandle = packet.extract(3)
        processed = False
        # logging.info("Write data, Handle? " + filehandle + " == " + self._handle)
        if filehandle == self._handle:
            datatowrite = packet.extract(4)
            # handle base64 errors
            try:
                datatowrite = base64.b64decode(datatowrite)
            except ValueError as exc:
                self._error = True
                logging.error("Failed to decode data, " + self.filename + ", " + str(exc))
            if not self._error:
                try:
                    self._filehandle.write(datatowrite)
                    # self._filehandle.write(datatowrite.encode())
                    self._filehandle.flush()
                    processed = True
                except UnicodeEncodeError as exc:
                    # ignore this for now, but do something?
                    self._error = True
                    logging.error("Failed to write data, " + self.filename + ", " + str(exc))
                except IOError as exc:
                    self._error = True
                    logging.error("Failed to write data, " + self.filename + ", " + str(exc) + "(" +
                                  str(exc.errno) + ")")
        return processed, None

    def _readdata(self, packet: WinGemPacket):
        '''
        Read data from uploaded file
        uploaded file should live in uploads folder
        '''
        filehandle = packet.extract(3)
        encoding = packet.extract(4, 1)
        processed = False
        hostdata = "WFTREAD" + WinGemPacket.VM
        filedone = "0"
        if filehandle == self._handle:
            try:
                # datatoread = self._filehandle.read(4096)
                datatoread = self._filehandle.read(10000)
            except EOFError:
                filedone = "1"
            except IOError as exc:
                self._error = True
                logging.error("Failed to read data " + exc.errno)
            processed = True
            if not datatoread or len(datatoread) < 10000:
                filedone = "1"
            if encoding == "BASE64":
                datatoread = base64.b64encode(datatoread).decode("ISO-8859-1")
            elif encoding == "CARET":
                # TODO: implement caret encoding
                pass
            # print(str(datatoread), filedone)
            hostdata += filedone + WinGemPacket.VM + str(datatoread)
        # logging.debug("Read " + str(len(datatoread)))
        return processed, hostdata

    def _checkfile(self, packet: WinGemPacket):
        ''' Check to see if file exists '''
        # TODO: check local files, for now return 1
        self.filename = packet.extract(3).lower()

        # determine directory of file
        self._dir, self.filename = getfiletuple(self.filename, "", self._sessionid)

        if os.path.exists(self._dir + self.filename):
            retpacket = "1" + WinGemPacket.VM + str(os.path.getsize(self._dir + self.filename))
        else:
            retpacket = "-1" + WinGemPacket.VM + "0"

        self._complete = True
        return True, retpacket

    def _createdir(self):
        ''' Create the folder for the file '''
        if self._dir:
            try:
                os.makedirs(self._dir, exist_ok=True)
            except OSError as exc:  # Python >2.5
                if exc.errno == errno.EEXIST and os.path.isdir(self._dir):
                    pass
                else:
                    raise
