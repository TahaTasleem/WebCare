'''
Created on Jun 15, 2017

@author: rosenada
'''
import os
from os import path

SESSIONLIST = {}


def registerusersession(user: str, usersession):
    ''' adds user and session to list '''
    if user in SESSIONLIST:
        SESSIONLIST[user].append(usersession)
    else:
        SESSIONLIST[user] = [usersession]


def removeusersession(sessionguid: str):
    ''' removes a session from a user '''
    user = getuserfromguid(sessionguid)
    # copy the nonmatching guids over on top of the existing list
    if user in SESSIONLIST:
        SESSIONLIST[user] = [g for g in SESSIONLIST[user] if g.get('guid') != sessionguid]


def getuserfromguid(guid: str):
    ''' return user name based on guid '''
    for user in SESSIONLIST:
        for session in SESSIONLIST.get(user):
            if session.get("guid") == guid:
                return str(user)
    return ""


def getsessionip(guid: str):
    ''' flips the logging info for the guid '''
    userssessionlist = getusersguids(getuserfromguid(guid))
    for session in userssessionlist:
        if guid == session.get("guid"):
            session["logging"] = not session["logging"]
            return session["userIP"]
    return ""


def getusersguids(user: str):
    ''' returns a users active guids '''
    return SESSIONLIST.get(user)


def togglelogging(guid: str):
    ''' flips the logging info for the guid '''
    userssessionlist = getusersguids(getuserfromguid(guid))
    if userssessionlist:
        for session in userssessionlist:
            if guid == session.get("guid"):
                session["logging"] = not session["logging"]
                return session["logging"]
    return False


def cansessionlog(guid: str):
    ''' based on supplied guid, checks if that process can log '''
    userssessionlist = getusersguids(getuserfromguid(guid))
    # on the initial login/bootup, a "MainThread" and "waitress" run through
    # here, they arent real user sessions but we want their logs anyway so
    # let them through
    if userssessionlist is None:
        return True
    for session in userssessionlist:
        if guid == session.get("guid"):
            return session.get("logging")
    return False


class LogFiles(object):
    ''' returns logging information '''

    def getlogfiles(self, sessionguid: str):
        ''' returns the logs files '''
        lognames = os.listdir(path.abspath(os.getcwd() + os.sep + "logs"))
        lognames.sort(reverse=True)
        loglist = ""
        for file in lognames:
            loglist += "Log entries in " + str(file) + os.linesep
            loglist += self.checklogfile(file, sessionguid)
        return loglist

    def checklogfile(self, file, sessionguid):
        ''' looks for guid in log files '''
        loglines = ""
        # path.abspath(path.join(__file__, os.pardir))
        with open("logs" + os.sep + file, encoding="ISO-8859-1") as logfile:
            addedlastline = False
            for line in logfile:
                if "Sending global request" in line:
                    addedlastline = False
                elif sessionguid in line:
                    addedlastline = True
                    loglines += line
                elif line[0] != "[" and addedlastline:
                    loglines += line
                else:
                    addedlastline = False
        return loglines
