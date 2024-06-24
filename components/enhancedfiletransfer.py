'''
Created on May 2, 2018

@author: cartiaar
'''

import os

from ftplib import FTP, FTP_TLS, error_perm, error_proto, error_reply, error_temp, all_errors
from components.filetransfer import getfiletuple
from components.wdobject import BaseWDObject
from connector.wingempacket import WinGemPacket


class EnhancedFileTransfer(BaseWDObject):
    ''' Enhanced File Transfer Object '''

    def __init__(self, sessionid):
        ''' Constructor '''
        super(EnhancedFileTransfer, self).__init__("ENHANCEDFILETRANSFER")

        self._sessionid = str(sessionid)
        self._direction = ""
        self._connectiontype = ""
        self._ftphost = ""
        self._ftpport = ""
        self._ftpuser = ""
        self._ftppassword = ""
        self._connectiontype = ""
        self._scriptuser = False
        self._pcstatus = 0
        self._hidden = False
        self._recursive = False
        self._destdir = ""
        self._autoacceptcerts = True
        self._uncpath = ""
        self._filelist = None
        self._filesize = 0
        self._error = False

    def addpacket(self, packet: WinGemPacket, **extras):
        ''' Add a packet to the enhanced file transfer object '''
        processed = False
        hostdata = ""
        errorcode = 0
        errormsg = ""

        if packet.packettype() == "WXT":
            self._direction = packet.extract(2)
            transfertype = packet.extract(3, 1)
            if transfertype == "FTP":
                self._ftphost = packet.extract(3, 2, 1)
                self._ftpport = packet.extract(3, 2, 2)
                self._ftpuser = packet.extract(3, 2, 3)
                self._ftppassword = packet.extract(3, 2, 4)

                if packet.extract(3, 2, 5) == "SECURE":
                    self._connectiontype = "FTPS"
                else:
                    self._connectiontype = "FTP"

                if packet.extract(3, 2, 6) == "SCRIPTUSER":
                    self._scriptuser = True

                if self._ftphost == "":
                    errorcode = 1
                    errormsg = "No host supplied"
            elif transfertype == "UNC":
                self._connectiontype = "UNC"
                self._uncpath = packet.extract(3, 2, 1)
            else:
                errorcode = 2
                errormsg = "Unsupported type"

            if errorcode == 0:
                configdetails = packet.extractaslist(4)
                for detail in configdetails:
                    minipacket = WinGemPacket(detail)
                    detailtype = minipacket.extract(1, 1, 1)
                    if detailtype == "HOST.STATUS":
                        statuslevel = minipacket.extract(1, 1, 2)
                        if statuslevel == "1":
                            self._pcstatus = 1
                        elif statuslevel == "2":
                            self._pcstatus = 2
                        elif statuslevel == "4":
                            self._pcstatus = 4
                        else:
                            self._pcstatus = 0
                    elif detailtype == "HIDDEN":
                        self._hidden = True
                    elif detailtype == "RECURSIVE":
                        self._recursive = True
                    elif detailtype == "SYSTEM":
                        self._recursive = True  # Wingem bug, probably never implmeneted?
                    elif detailtype == "REMOTE.DIR":
                        self._destdir = minipacket.extract(1, 1, 2)
                    elif detailtype == "NOAUTOACCEPT":
                        self._autoacceptcerts = False

                if self._destdir == "":
                    errorcode = 4
                    errormsg = "No destination folder specified"

            if errorcode == 0:
                self._filelist = packet.extractaslist(5)

                errorcode, errormsg = self._transferfiles()

            hostdata = "WXTC" + WinGemPacket.VM + str(errorcode) + WinGemPacket.VM + errormsg
            if errorcode == 0:
                hostdata += WinGemPacket.VM + "1" + WinGemPacket.SM + str(self._filesize)

            processed = True

        #self._complete = True

        return processed, hostdata, self

    def _transferfiles(self):
        if self._connectiontype == "FTP" or self._connectiontype == "FTPS":
            try:
                if self._connectiontype == "FTP":
                    if self._ftpport != "":
                        if self._ftpport.isnumeric():
                            ftp = FTP()
                            ftp.connect(self._ftphost, self._ftpport)
                            ftp.login(self._ftpuser, self._ftppassword)
                        else:
                            return 6, "The supplied port is not a number"
                    else:
                        ftp = FTP(self._ftphost, self._ftpuser, self._ftppassword)
                else:
                    if self._ftpport != "":
                        if self._ftpport.isnumeric():
                            ftp = FTP_TLS()
                            ftp.connect(self._ftphost, self._ftpport)
                            ftp.login(self._ftpuser, self._ftppassword)
                        else:
                            return 6, "The supplied port is not a number"
                    else:
                        ftp = FTP_TLS(self._ftphost, self._ftpuser, self._ftppassword)
                    ftp.prot_p()

                ftp.cwd(self._destdir)
            except (error_reply, error_temp, error_perm, error_proto) as error:
                return int(error.args[0][:3]), error.args[0][4:]
            except all_errors as error: # pylint: disable=W0612
                return 11, "Error during connection"

            for singlefile in self._filelist:
                # determine directory of file
                _dir, _filename = getfiletuple(singlefile, "READ", self._sessionid)
                try:
                    filehandle = open(_dir + _filename, 'rb')
                except FileNotFoundError:
                    return 10, "Could not open file " + _filename + " in folder " + _dir
                self._filesize = os.fstat(filehandle.fileno()).st_size
                try:
                    ftp.storbinary('STOR ' + _filename, filehandle)
                except (error_reply, error_temp, error_perm, error_proto) as error:
                    return int(error.args[0][:3]), error.args[0][4:]
                except all_errors as error:
                    return 12, "Error during upload"

                filehandle.close()

            try:
                ftp.quit()
            except all_errors:
                pass

        return 0, ""
