'''
Created on Aug 2, 2018

@author: bouchcla
'''

import datetime
import logging
import uuid


class SessionData():
    ''' Class to represent session data '''

    def __init__(self):
        ''' Setup data '''
        self.loggedin = False
        self.user = ""
        self.start = datetime.datetime.now()
        self.clientip = ""
        self.loginserver = ""


class SessionManager():
    ''' Class to manage WebDirect Sessions '''

    def __init__(self):
        ''' Setup our internal data '''
        self._sessions = dict()

    def createnew(self):
        ''' Create a new session '''
        newsessionid = uuid.uuid4()
        sessiondata = SessionData()
        self._sessions[newsessionid] = sessiondata
        return newsessionid

    def removesession(self, sessionid):
        ''' Remove old session '''
        if sessionid in self._sessions:
            del self._sessions[sessionid]
        else:
            logging.debug("Attempted to delete unknown session " + str(sessionid))

    def isloggedin(self, sessionid):
        ''' Check to see if session is logged in '''
        if sessionid in self._sessions:
            return self._sessions[sessionid].loggedin
        else:
            return False

    def setuser(self, sessionid, user):
        ''' Set the user for the session '''
        if sessionid in self._sessions:
            self._sessions[sessionid].user = user

    def setloggedin(self, sessionid, loggedin):
        ''' Set the user for the session '''
        if sessionid in self._sessions:
            self._sessions[sessionid].loggedin = loggedin

    def setstartdata(self, sessionid, startdata):
        ''' Set the start data for the session '''
        if sessionid in self._sessions:
            self._sessions[sessionid].startdata = startdata

    def setclientip(self, sessionid, clientip):
        ''' Set the client ip for the session '''
        if sessionid in self._sessions:
            self._sessions[sessionid].clientip = clientip

    def setloginserver(self, sessionid, loginserver):
        ''' Set the loginserver for the session, used by autologin '''
        if sessionid in self._sessions:
            self._sessions[sessionid].loginserver = loginserver

    def getuser(self, sessionid):
        ''' Get the user for the session '''
        if sessionid in self._sessions:
            return self._sessions[sessionid].user
        else:
            return None

    def getstartdata(self, sessionid):
        ''' Get the start data for the session '''
        if sessionid in self._sessions:
            return self._sessions[sessionid].startdata
        else:
            return None

    def getloginserver(self, sessionid):
        ''' Get the loginserver for the session '''
        if sessionid in self._sessions:
            return self._sessions[sessionid].loginserver
        else:
            return None

    def getsessions(self):
        ''' return the session dataset '''
        return self._sessions
