'''
Created on June 16, 2017

@author: holthjef
'''
import os
import threading
from werkzeug.utils import secure_filename
from components.command import Command
import components.filetransfer


# from components.filetransfer import getfiletuple
from components.wdobject import BaseWDObject
# from connector.configuration import CONFIG
from connector.wingempacket import WinGemPacket


class Editor(BaseWDObject):
    '''
    Code-focused text editor
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super().__init__("EDITOR")

        self._action = None
        self.filepath = None
        self.origfilepath = None
        self.contenttype = ""
        self.stringrepresentation = None
        self.readonly = False

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Parse WebDirect Edit packet '''
        # See \\share\fileshar\Tech\Applics\WinGem\Design\GUICommandSet.doc (WDEDIT section)

        success = False

        if packet.packettype() != "WDE":
            return False, None, None

        self.stringrepresentation = packet.stringify()

        # Extract action (EDIT vs DIFF)
        self._action = packet.extract(2)

        self.filepath = packet.extract(3, 1)

        self.origfilepath = packet.extract(3, 2)

        options = packet.extract(4).split(WinGemPacket.VM)

        # Loop through options
        for option in options:
            optionlist = option.split("=")
            if optionlist:
                keyword = optionlist[0].upper()
                if len(optionlist) > 1:
                    value = optionlist[1]
                else:
                    value = None

                if keyword == "CONTENTTYPE":
                    # Get content-type, if specified
                    self.contenttype = value or ""

                if keyword == "READONLY":
                    if value == "Y":
                        self.readonly = True

        # Validate new file
        statusmsg = self._verifyfile(self.filepath)
        if not statusmsg and self._action == "DIFF":
            # Validate old file
            statusmsg = self._verifyfile(self.origfilepath)

        if not statusmsg:
            success = True

        self._complete = True

        #=======================================================================
        # Return cmd if editor request succeeds, otherwise None
        # Return data for host if editor request fails, otherwise None
        #=======================================================================
        editcmd = None
        hostdata = None
        if success:
            editcmd = Command()
            if self._action == "DIFF":
                editcmd.diff(self.origfilepath, self.filepath, self.contenttype)
            else:
                editcmd.editfile(self.filepath, self.contenttype, self.readonly)
        else:
            if self._action == "DIFF":
                editcmd = Command()
                editcmd.msg("FLASH", ["Error processing Compare", "", statusmsg], [])
            else:
                if not self.readonly:
                    # Editting is happening, so a response is expected
                    # Will get prefixed with "<esc>WHIR:"
                    hostdata = "WDEC" + WinGemPacket.VM + "FAIL-GEN" + WinGemPacket.VM + statusmsg
        return True, hostdata, editcmd

    def _verifyfile(self, filepath: str):
        # Verify the file exists in WD
        dirname, filename = components.filetransfer.getfiletuple(filepath,
                                                                 "READ",
                                                                 threading.current_thread().name)
        filename = secure_filename(filename)
        newfilepath = dirname + filename

        statusmsg = None

        # Only read/write content under static\data
        if dirname[0:12] != "static" + os.sep + "data" + os.sep:
            statusmsg = "Invalid location specified: " + filepath

        # Only read/write content that exists
        if not statusmsg and not os.path.isfile(newfilepath):
            statusmsg = "File does not exist: " + filepath

        return statusmsg

    def getid(self):
        ''' override getid '''
        return "WDFileEditor"
