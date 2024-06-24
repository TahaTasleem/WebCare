'''
Created on Sep 27, 2016
@author: bouchcla
'''
import datetime
import logging
import os
import re
import shutil
import sys
import time
import traceback
import uuid
from threading import Event, Thread

from components.commandbar import \
    CommandBarTool  # pylint: disable=unused-import
from components.tcldata import TCLData
from connector.configuration import CONFIG

from telnet.telnetthread import CommDataSet, TelnetThread


class TelnetManager(object):
    ''' Telnet Session Manager '''

    def __init__(self, socketioqueue):
        ''' Constructor '''
        # used to keep track of threads
        self._data = dict()
        self.queue = socketioqueue

        # Used by threads, need to be thread safe
        self._shutdown = Event()

        # Scheduler to clean up dead data holders
        localthread = Thread(
            target=self.taskscheduler,
            name="TM Cleanup Scheduler",
            daemon=True)
        localthread.start()

    def taskscheduler(self):
        ''' run scheduler every two minutes
            runs as a daemon, so can just let it die on it's own
        '''
        while True:
            self.cleanupdeadsessiondata()
            time.sleep(120)
        sys.exit()

    def setupqueues(self, telnetid, enable_logging=False):
        ''' sets up queues for session '''
        # setup a new input queue
        commdata = CommDataSet(enable_logging)
        commdata.telnetmgr = self
        commdata.id = telnetid
        self._data[telnetid] = commdata

    def setsocket(self, telnetid, socket):
        ''' sets the socket '''
        self._data[telnetid].socketid = socket

    def getsocket(self, telnetid):
        ''' returns the socket '''
        return self._data[telnetid].socketid

    def datahandler(self, telnetid):
        ''' handles data return '''
        tid = telnetid
        if not isinstance(tid, uuid.UUID):
            tid = uuid.UUID(telnetid)
        results = {}
        renderids = {}
        if self.getconnected(tid):
            results, renderids = self.getdataarray(tid)
        else:
            # we have been disconnected, check to see if there is anything left to send
            if self.hasdata(tid):
                results = self.getlogout(tid)
                renderids = {}
        if results:
            # prepare data for client
            data = {
                "message": {
                    "results": results,
                    "renderids": renderids
                },
                "roomid": self._data[tid].socketid
            }
            self.queue.put(data)

    def starttelnetsession(self, telnetid, host, ssl=False,
                           user: str = None,
                           password: str = None,
                           account: str = None,
                           ssh: bool = False,
                           passcode: str = None,
                           startdata: str = None,
                           enable_logging: bool = False):
        ''' Builds and starts telnet thread '''
        if telnetid in self._data:
            self._data.pop(telnetid)
        self.setupqueues(telnetid, enable_logging)
        # run our new thread
        telnetthread = TelnetThread(host, ssl, user, password,
                                    account, ssh, passcode, startdata)
        localthread = Thread(
            target=telnetthread.runconnection, args=(
                self._data[telnetid], self._shutdown),
            name=telnetid)
        localthread.start()

    def stoptelnetsession(self, telnetid):
        ''' Stop a specific telnet thread '''
        if telnetid in self._data:
            self._data[telnetid].stop = True

    def closetelnetsessions(self):
        ''' Close down telnet threads '''
        logging.info("Shutting down telnet manager")
        self._shutdown.set()
        time.sleep(0.25)

    def senddata(self, telnetid, data):
        ''' sends data to telnet channel '''
        self._data[telnetid].inputq.append(data)

    def hasdata(self, telnetid):
        ''' has data or not '''
        if telnetid in self._data:
            return self._data[telnetid].outputq
        else:
            return False

    def getdata(self, telnetid):
        ''' Checks for data, returns some if any '''
        result = TCLData()
        if self._data[telnetid].outputq:
            result = self._data[telnetid].outputq.popleft()
        return result

    def adddata(self, telnetid, data):
        ''' Add data to output queue '''
        self._data[telnetid].outputq.append(data)

    def datatype(self, telnetid):
        ''' return data type of top item '''
        if self._data[telnetid].outputq:
            topdata = self._data[telnetid].outputq[0]
            return topdata.gettype()
        else:
            return ""

    def getrenderdata(self, telnetid, renderid):
        ''' Return Data for Render Targets '''
        item = None
        try:
            item = self._data[telnetid].renderq.pop(renderid)
        except KeyError:
            logging.error("Render Item not present: " + renderid + "\r\n" +
                          str(traceback.format_exc().splitlines()))
        return item

    def getcurrentscreen(self, telnetid):
        ''' return topmost screeen (if exists) '''
        if self._data[telnetid].screenstack:
            return self._data[telnetid].screenstack[-1]
        else:
            return None

    def getcommandbar(self, telnetid):
        ''' return Command Bar '''
        return self._data[telnetid].commandbar

    def getexternalfile(self, telnetid, file):
        ''' get external file from details '''
        extfile = None
        try:
            extfile = self._data[telnetid].externalfiles[file]
        except KeyError:
            pass
        return extfile

    def getscreen(self, telnetid, screenid):
        ''' return screeen matching screenid (if exists) '''
        if self._data[telnetid].screenstack:
            for screen in self._data[telnetid].screenstack:
                if screen.screenid == int(screenid):
                    return screen
            return None
        else:
            return None

    def getscreenstack(self, telnetid):
        ''' returns full screen stack '''
        return self._data[telnetid].screenstack

    def getdataarray(self, telnetid):
        ''' Return dictionary of return types '''
        response = []
        renderids = []
        while True:
            try:
                element = self._data[telnetid].outputq.popleft()
                # Avoid re-rendering the same element, grids hit this often
                if self._data[telnetid].renderq:
                    renderid = str(self._data[telnetid].renderid)
                    try:
                        if self._data[telnetid].renderq[renderid] == element and \
                                element.gettype() != "COMMANDBAR":
                            # AWD-1990 - this breaks command bars sometimes
                            continue
                    except KeyError:
                        pass
                returnelement = {"datatype": element.gettype()}
                if element.gettype() == "TCL":
                    returnelement["tcldata"] = element.getdata()
                elif element.gettype() == "COMMAND":
                    if 'type' not in element.getcommand():
                        # can get a blank command from somewhere
                        continue
                    if element.getcommand()['type'] == "DISPLAY":
                        targetid = element.getcommand()['targetid']
                        # check to make our screen / prompt still exists
                        screen = self.getscreen(telnetid, targetid.split("_")[0])
                        if not screen:
                            continue
                        # see if our screen exists
                        prompt = screen.getprompt(int(targetid.split("_")[1]))
                        if not prompt:
                            continue
                    returnelement["command"] = element.getcommand()
                    if element.prompting:
                        returnelement["prompting"] = True
                else:
                    if element.gettype() == "SCREEN":
                        screen = self.getscreen(telnetid, element.screenid)
                        if not screen:
                            # if we've been closed, don't send the screen
                            continue
                    if element.gettype() in ['PROMPT', 'BUTTON', 'GRID', 'TEXT']:
                        screen = self.getscreen(telnetid, element.screenid)
                        if not screen:
                            # screen may have been closed, don't send stuff if it is
                            continue
                    returnelement["targetid"] = element.getid()
                    # add to renderq
                    self._data[telnetid].renderid += 1
                    renderid = str(self._data[telnetid].renderid)
                    returnelement['renderid'] = renderid
                    renderids.append(renderid)
                    self._data[telnetid].renderq[renderid] = element
                    if element.gettype() == "COMMANDBARTOOL":
                        # Should only have one parent at this point
                        parentid = list(element.parents.keys())[0]
                        band = element.parents[parentid]
                        # Pass id of band that contains tool
                        returnelement["parentid"] = parentid
                        # Pass tool position in band in browser
                        returnelement["position"] = band.gettoolclientpos(element)
                response.append(returnelement)
            except IndexError:
                # nothing left to process, return
                break
            except KeyError:
                logging.exception("Key error in get data")
                break

        return response, renderids

    def getlogout(self, telnetid):
        ''' see if there is a message to return '''
        response = []
        while True:
            try:
                element = self._data[telnetid].outputq.popleft()
                returnelement = {"datatype": element.gettype()}
                if element.gettype() == "COMMAND":
                    command = element.getcommand()
                    if command["type"] == "LOGOUT":
                        returnelement["command"] = command
                        response.append(returnelement)
                    if command["type"] == "NAVEXT":
                        returnelement["command"] = command
                        response.insert(0, returnelement)
            except (IndexError, KeyError):
                # nothing left to process, return
                break

        return response

    def getid(self, telnetid):
        ''' Get target id for item if it's to be rendered '''
        targetid = ""
        if self.datatype(telnetid) != "TCL":
            targetid = self._data[telnetid].outputq[0].getid()
        return targetid

    def getconnected(self, telnetid):
        ''' Determine if we are connected or not '''
        if telnetid in self._data:
            return self._data[telnetid].connected
        else:
            return False

    def setconnected(self, telnetid, connected):
        ''' Set connected status, used only by log manager '''
        self._data[telnetid].connected = connected

    def setdisconnecttime(self, telnetid):
        ''' set disconnected time '''
        logging.debug("Socket Disconnect: %s, timestamp: %i", telnetid, time.time())
        self._data[telnetid].lasttouch = time.time()

    def unsetdisconnecttime(self, telnetid):
        ''' set disconnected time '''
        logging.debug("Socket Connected: %s, timestamp: %i", telnetid, time.time())
        self._data[telnetid].lasttouch = None

    def cleanupdeadsessiondata(self):
        ''' Cleanup any dead session data '''
        keys = self._data.keys()
        deadsessions = [key for key in keys if not self._data[key].connected]
        for key in deadsessions:
            # cleanup session
            logging.debug("Cleaned up dead session data " + str(key))
            del self._data[key]

        # clean up old folders
        isguid = re.compile("^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
        datapath = 'static/data/'
        for version_dir in os.listdir(datapath):
            version_path = os.path.join(datapath, version_dir)
            for subdir in os.listdir(version_path):
                session_folder = os.path.join(version_path, subdir)
                if re.search(isguid, subdir) and os.path.isdir(session_folder):
                    folder_time = os.stat(session_folder).st_mtime
                    folder_date = datetime.datetime.fromtimestamp(folder_time)
                    folder_age = (datetime.datetime.today() - folder_date).days
                    if folder_age > CONFIG['FOLDERCLEANUP']:
                        logging.debug("Cleaned up dead session data " + subdir)
                        shutil.rmtree(session_folder, ignore_errors=True)

        # clean up old uploads, too
        uploadpath = 'uploads/'
        if os.path.exists(uploadpath):
            for subdir in os.listdir(uploadpath):
                if re.search(isguid, subdir) and uuid.UUID(subdir) not in self._data:
                    upload_folder = os.path.join(uploadpath, subdir)
                    if os.path.isdir(upload_folder):
                        logging.debug("Cleaned up dead session data " + subdir)
                        shutil.rmtree(upload_folder, ignore_errors=True)
