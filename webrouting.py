'''
Created on Oct 19, 2016

This module defines our Flask Routes, Filters and more

@author: bouchcla
'''

import binascii
import datetime
import json
import logging
import sys
import os
import re
import time
import traceback
import uuid
import mimetypes
from functools import wraps
from platform import uname
import requests
from eventlet.queue import Empty, Queue
from flask import (Flask, Response, jsonify, make_response, redirect,
                   render_template, request, send_file, send_from_directory, session, url_for)
from flask_socketio import SocketIO, disconnect
from werkzeug.utils import secure_filename
from markupsafe import Markup

import components
from components import logfilemanager
from components.filetransfer import fixslashes
from components.logfilemanager import LogFiles, togglelogging
from connector import resource
from connector.configuration import CONFIG, get_credentials
from connector.logfilereader import readlogfile
from connector.sessionmanager import SessionManager
from connector.utility import unicodetoascii
from connector.wingempacket import WinGemPacket
from telnet.telnetmanager import TelnetManager

try:
    from jinja2.exceptions import UndefinedError
    # if jinja2 < 3.1 then use evalcontextfilter
    from jinja2 import evalcontextfilter
except ImportError:
    # in jinja2 >=3.1 evalcontextfilter was replaced by pass_eval_context
    from jinja2 import pass_eval_context as evalcontextfilter

UUID_RE = re.compile(
    r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[4][0-9A-Fa-f]{3}-[89AB][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}")

# Flask application valid session list, socketio pieces, Telnet Manager
FLASKAPP = Flask(__name__)
#Variable storing Current Working Directory
CWD = os.path.abspath(os.path.dirname(sys.executable))
if getattr(sys, 'frozen', False):
    CONFIG["EXECUTABLE"] = True
SIO_CONFIG = { "async_mode": None }
if CONFIG["CORS_ALLOWED_ORIGINS"]:
    SIO_CONFIG["cors_allowed_origins"] = CONFIG["CORS_ALLOWED_ORIGINS"]
SOCKETIO = SocketIO(FLASKAPP, **SIO_CONFIG)
SIO_THREAD = None
SIO_QUEUE = Queue()
TM = TelnetManager(SIO_QUEUE)
if CONFIG['PRODUCTION']:
    FLASKAPP.config["SESSION_COOKIE_SECURE"] = True
    FLASKAPP.config["SESSION_COOKIE_NAME"] = "wd" + binascii.hexlify(os.urandom(16)).decode()
else:
    FLASKAPP.config["SESSION_COOKIE_NAME"] = "wddev_" + uname()[1]
# default caching for static files to 1 week (Google PageSpeed Recommendation)
FLASKAPP.config['SEND_FILE_MAX_AGE_DEFAULT'] = 604800

# set the secret key
# keep it unique per instance and don't allow reuse
FLASKAPP.secret_key = os.urandom(24)

# ===============================================
# Flask Base Stuff Overrides
# ===============================================


class WDResponse(Response):
    ''' Override default charset '''
    charset = "ISO-8859-1"


FLASKAPP.response_class = WDResponse

# ===============================================
# Supporting Functions
# ===============================================

def socketsession(requireloggedin=False):
    ''' Determine if our session exists and possibly if logged in '''
    def decorator(function):
        ''' decorator for the passed in function '''
        @wraps(function)
        def decorated_function(*args, **kwargs):
            ''' determines if our session is logged in '''
            current_session = uuid.UUID(request.args['sessionid'])
            if not current_session:
                # no session passed in
                logging.info("No current session")
                disconnect()
            elif "sessions" not in session:
                #print("no sessions at all!")
                logging.info("Session does not exist (%s)", current_session)
                # no session cookie
                disconnect()
            else:
                sessionlist = session['sessions']
                if current_session in sessionlist:
                    if requireloggedin and not SESSIONS.isloggedin(current_session):
                        # not logged in
                        logging.info("User is no longer logged in (%s - %s)",
                                     SESSIONS.getuser(current_session), current_session)
                        disconnect()
                else:
                    #print(current_session, sessionlist)
                    logging.info("Invalid session (%s - %s).",
                                 SESSIONS.getuser(current_session), current_session)
                    # not a valid session
                    disconnect()
            return function(*args, **kwargs)
        return decorated_function
    return decorator

def session_required(requireloggedin=False, externalroute=False):
    ''' Determine if our session exists and possibly if logged in '''
    def decorator(function):
        ''' decorator for the passed in function '''
        @wraps(function)
        def decorated_function(*args, **kwargs):
            ''' determines if our session is logged in '''
            if 'tabsession' not in kwargs:
                #print("No tab session", function, kwargs)
                return rejectroute(externalroute)
            current_session = kwargs['tabsession']
            if not current_session:
                # no session passed in
                #print("no current session")
                return rejectroute(externalroute)
            elif "sessions" not in session:
                #print("no sessions at all!")
                # no session cookie
                return rejectroute(externalroute)
            else:
                sessionlist = session['sessions']
                if current_session in sessionlist:
                    if requireloggedin and not SESSIONS.isloggedin(current_session):
                        # not logged in
                        return rejectroute(externalroute)
                else:
                    #print(current_session, sessionlist)
                    # not a valid session
                    return rejectroute(externalroute)
            return function(*args, **kwargs)
        return decorated_function
    return decorator


def rejectroute(externalroute):
    ''' return data to caller depending on case '''
    if externalroute:
        return ('', 403)
    else:
        return jsonify(login=True)


# ===============================================
# WebSocket/LongPolling support
# ===============================================

@SOCKETIO.on_error_default
def error_handler(errorobj):
    ''' record any socket io errors '''
    logging.error('An error has occurred: %s', str(errorobj))

@SOCKETIO.on("connect")
@socketsession(True)
def connection_request():
    ''' handle connection '''
    if "sessionid" in request.args:
        tabsession = uuid.UUID(request.args["sessionid"])
    else:
        # no session, force disconnect
        disconnect()
    #print("connection", tabsession, request.sid, request.namespace)
    TM.setsocket(tabsession, request.sid)
    TM.unsetdisconnecttime(tabsession)


@SOCKETIO.on('incoming')
@socketsession(True)
def test_message(message):
    ''' handle data '''
    data = message.get('data', dict())
    noenter = data.get("noenter", 0)
    inputdata = data.get("in", None)
    tabsession = data.get("session", None)
    # only do something if we got data from the client
    if inputdata is not None:
        try:
            TM.senddata(uuid.UUID(tabsession), str(inputdata) + (chr(13) if noenter != 1 else ""))
        except KeyError:
            # logging.exception("incoming!")
            logging.debug("Invalid session request (%s)", tabsession)

@SOCKETIO.on("disconnect")
@socketsession(True)
def disconnected():
    ''' record time of disconnect '''
    try:
        tabsession = uuid.UUID(request.args['sessionid'])
        TM.setdisconnecttime(tabsession)
    except KeyError:
        pass

def emitter():
    ''' emit message '''
    while True:
        try:
            data = SIO_QUEUE.get()
            message = data.get("message", "")
            roomid = data.get("roomid", "")
            #print(message,roomid)
            if message:
                SOCKETIO.emit("data", message, room=roomid)
        except Empty:
            pass


# ===============================================
# Routes
# ===============================================

@FLASKAPP.route("/<uuid:tabsession>/input", methods=['GET', 'POST'])
@session_required(True)
def uiinput(tabsession):
    ''' UI input/output '''
    skipdata = False
    addenter = True
    inputdata = ""
    if request.method == "POST":
        inputdata = request.form['in']
        if "skipdata" in request.form:
            skipdata = request.form['skipdata'] == "1"
        if "noenter" in request.form:
            addenter = (False if request.form['noenter'] == "1" else True)
    else:
        inputdata = request.args['in']
        if "skipdata" in request.args:
            skipdata = request.args['skipdata'] == "1"
        if "noenter" in request.args:
            addenter = (False if request.args['noenter'] == "1" else True)
    try:
        TM.senddata(tabsession, inputdata + (chr(13) if addenter else ""))
    except KeyError:
        return rejectroute(False)
    if skipdata:
        return ('', 204)
    else:
        # don't wait more than a half second
        maxwait = (0.03 if addenter else 0.5)
        wait = 0
        while not TM.hasdata(tabsession) and wait < maxwait:
            time.sleep(0.01)
            wait += 0.01
        return internalpoll(tabsession)


@FLASKAPP.route("/<uuid:tabsession>/poll", methods=['GET'])
@session_required(True)
def poll(tabsession):
    ''' Polling Route '''
    return internalpoll(tabsession)


def internalpoll(tabsession):
    ''' poll for data '''
    # not tied to a route so we can call it from uiinput/poll safely
    if TM.getconnected(tabsession):
        results, renderids = TM.getdataarray(tabsession)
        return jsonify(results=results, renderids=renderids)
    else:
        # we are getting polled from something that has been disconnected
        # destroy the internal session variable
        # this causes us to lose any disconnected messages we may have
        # so may need to be a bit smarter
        retdata = rejectroute(False)
        if TM.hasdata(tabsession):
            results = TM.getlogout(tabsession)
            if results:
                retdata = jsonify(results=results, renderids={})
        SESSIONS.removesession(tabsession)
        return retdata


@FLASKAPP.route("/<uuid:tabsession>/about", methods=['GET'])
@FLASKAPP.route("/login/<uuid:tabsession>/about", methods=['GET'])
@session_required(True, True)
def about(tabsession):
    ''' about webdirect '''
    return render_template("about.html", sessionid=tabsession)


@FLASKAPP.route("/status", methods=['GET'])
def status():
    ''' return status '''
    if CONFIG['PRODUCTION']:
        return rejectroute(True)
    return render_template("status.html", sessions=SESSIONS.getsessions())

# @FLASKAPP.route("/logmanager", methods=['POST', 'GET'])
# @session_required
# def viewlogs():
#     '''opens logging interface'''
#     tuserid = request.values['userid'] if 'userid' in request.values else ""
#     tusersessions = LF.getusersguids(tuserid)
#     return render_template("logs.html", usersessions=tusersessions)


@FLASKAPP.route("/<uuid:tabsession>/getlog", methods=['POST', 'GET'])
@FLASKAPP.route("/login/<uuid:tabsession>/getlog", methods=['POST', 'GET'])
@session_required(True, True)
def getlogs(tabsession):
    ''' returns a download type response with the log content of userguid '''
    tsession = str(
        tabsession) if tabsession is not None else request.values['userguid']
    resp = make_response(LogFiles().getlogfiles(tsession).encode("ISO-8859-1"))
    resp.headers["Content-Disposition"] = "attachment ; filename = " + tsession + ".log"
    resp.headers["Content-Type"] = "text/plain; charset=ISO-8859-1"
    return resp


@FLASKAPP.route("/<uuid:tabsession>/togglelog", methods=['POST', 'GET'])
@FLASKAPP.route("/login/<uuid:tabsession>/togglelog", methods=['POST', 'GET'])
@session_required(True)
def toggleuserlogging(tabsession):
    ''' Flips the logging boolean for the session '''
    return jsonify(togglelogging(str(tabsession)))


@FLASKAPP.route("/healthcheck", methods=["GET"])
@FLASKAPP.route("/login/healthcheck", methods=["GET"])
def healthcheck():
    ''' return 200 saying we are up '''
    return 'WebDirect is running.', 200

@FLASKAPP.route("/go/<server>/<account>")
@FLASKAPP.route("/go/<server>")
@FLASKAPP.route("/<server>/<account>")
@FLASKAPP.route("/<server>")
@FLASKAPP.route("/login/<loginserver>")
@FLASKAPP.route('/', methods=['GET', 'POST'])
def wdmain(server=None, account=None, loginserver=None):
    ''' main entry point '''
    if not server:
        server = request.values['server'] if "server" in request.values else ""
    if not loginserver:
        loginserver = request.values['loginserver'] if "loginserver" in request.values else ""
    if not account:
        account = request.values['account'] if "account" in request.values else ""

    if (not loginserver and not server and CONFIG["DEFAULT"] and
            CONFIG["DEFAULT"] in CONFIG["SERVERS"]):
        if CONFIG["AUTO"][CONFIG["DEFAULT"]]:
            loginserver = CONFIG["DEFAULT"]
            server = ""
            account = ""
        else:
            server = CONFIG["DEFAULT"]
            loginserver = ""
            account = ""

    # First pass at an azure login URL, open the msal page
    if (loginserver and CONFIG["AZURE"][loginserver] and
            "auth_token" not in str(request.query_string)):
        return render_template("azurelogin.html",
                               clientid=CONFIG["CLIENTID"][loginserver],
                               tenantid=CONFIG["TENANTID"][loginserver])

    # check to see if our background thread is running
    # global required by eventlet to share the variable across threads
    global SIO_THREAD # pylint: disable=global-statement
    if SIO_THREAD is None:
        SIO_THREAD = SOCKETIO.start_background_task(emitter)

    # setup session id and add it to valid list
    localsessionid = SESSIONS.createnew()
    sessionslist = []
    if "sessions" in session:
        sessionslist = session['sessions']
    sessionslist.append(localsessionid)
    session['sessions'] = sessionslist
    if request.query_string:
        SESSIONS.setstartdata(localsessionid, request.query_string.decode("utf-8"))
    else:
        SESSIONS.setstartdata(localsessionid, "")

    try:
        clientip = request.headers["X-Real-IP"]
    except KeyError:
        clientip = request.remote_addr
    SESSIONS.setclientip(localsessionid, clientip)

    autologin = False
    if (loginserver and loginserver in CONFIG["SERVERS"] and
            CONFIG["AUTO"][loginserver]):
        SESSIONS.setloginserver(localsessionid, loginserver)
        autologin = True

    return render_template('webdirect.html', sessionid=localsessionid,
                           serveroverride=server, accountoverride=account,
                           allowfreeformlogin=CONFIG["ALLOWFREEFORMLOGIN"],
                           autologin=autologin, loginserver=loginserver,
                           languageobject=resource.getcurrentlanguagemap())


@FLASKAPP.route("/go/", methods=['GET', 'POST'])
def go():  # pylint:disable=invalid-name
    ''' If target route specified wihout server or account send to root route '''
    return redirect(url_for('wdmain'))


@FLASKAPP.route("/<uuid:tabsession>/connect", methods=['POST'])
@FLASKAPP.route("/login/<uuid:tabsession>/connect", methods=['POST'])
@session_required()
def connect(tabsession):
    ''' connect to host '''
    resp = ""
    server = SESSIONS.getloginserver(tabsession)
    enable_logging = False

    if CONFIG['CAPTCHA'] and not server:
        try:
            res = verify_captcha(request.values["captcha"])
            if res is False:
                resp = {"error": "Captcha verification failed. Please try again."}
                return jsonify(resp)
        except KeyError:
            pass # Do Nothing

    # if we already have a connection on this session id
    # assume it's an invalid external request
    if TM.getconnected(tabsession):
        return rejectroute(True)

    # Flip to a new sid to prevent hijacking stale, non-used sessions
    localsessionid = SESSIONS.createnew()
    sessionslist = []
    if "sessions" in session:
        sessionslist = session['sessions']
    try:
        sessionslist.remove(tabsession)
    except KeyError:
        pass
    sessionslist.append(localsessionid)
    session['sessions'] = sessionslist
    SESSIONS.setstartdata(localsessionid, SESSIONS.getstartdata(tabsession))
    SESSIONS.setloginserver(localsessionid, SESSIONS.getloginserver(tabsession))
    logging.info("Flipped sid from " + str(tabsession) +
                 " to " + str(localsessionid))
    tabsession = localsessionid

    try:
        clientip = request.headers["X-Real-IP"]
    except KeyError:
        clientip = request.remote_addr
    SESSIONS.setclientip(tabsession, clientip)

    if server:
        user, password = get_credentials(server)
        account = CONFIG["ACCOUNTS"][server][0]
        ssl = CONFIG["SSL"][server]
        passcode = ""

        logging.info("Auto-connection made for " + str(tabsession) +
                     " from " + clientip + " to " + server)

        if user == "" or password == "":
            resp = {"error": "Error with server configuration, contact your system administrator"}
    else:
        user = request.values['user'] if 'user' in request.values else ""
        password = request.values['password'] if 'password' in request.values else ""
        server = request.values['server'] if 'server' in request.values else ""
        account = request.values['account'] if 'account' in request.values else ""
        ssl = request.values['ssl'] if 'ssl' in request.values else ""
        passcode = request.values['passcode'] if 'passcode' in request.values else None
        enable_logging = request.values['logging'] if 'logging' in request.values else "false"

        if isinstance(enable_logging, str):
            enable_logging = enable_logging.lower() == 'true'

        logging.info("Connection made for " + str(tabsession) +
                     " from " + clientip + " (" + user + ")")

        # In free-form mode, don't validate input parms
        if not CONFIG["ALLOWFREEFORMLOGIN"]:
            if user == "":
                resp = {"error": "No username specified"}
            elif password == "":
                resp = {"error": "No password specified"}
            elif server not in CONFIG["SERVERS"]:
                resp = {"error": "Not a valid server"}
            elif account not in CONFIG["ACCOUNTS"][server]:
                resp = {"error": "Not a valid account"}

    if resp == "":
        # All good, attempt host connection
        # logging.info(
        #   "login details %s, %s, %s, %s", user, password, server, account)
        host = CONFIG["HOST"][server]
        ssh = CONFIG["SSH"][server]
        TM.starttelnetsession(tabsession, host, ssl, user, password, account, ssh, passcode,
                              SESSIONS.getstartdata(tabsession), enable_logging)
        resp = {'connect': True, 'sid': tabsession}
        usersession = {"guid": str(tabsession), "logging": enable_logging,
                       "userIP": clientip}
        logfilemanager.registerusersession(user, usersession)
        SESSIONS.setuser(tabsession, user)
        SESSIONS.setloggedin(tabsession, True)

    return jsonify(resp)

def verify_captcha(response):
    ''' Verify Captcha Response '''
    data = {'secret': '6LeGqM8pAAAAAA0zWyMIe5kdNlOIay-hkes3KSFd',
            'response': response}
    # If www.google.com doesn't resolve (dnspython problem in windows containers)
    # fallback to trying a few Google IP addresses.
    # This is kind of a terrible workaround and should be removed when
    # a) We remove eventlet for some other threading library, or
    # b) we are able to move to Linux containers only
    urls = ["www.google.com",
            "142.250.69.196",
            "172.217.13.164",
            "172.253.122.106"]
    for url in urls:
        try:
            if url == "www.google.com":
                verify = True
            else:
                verify = False
            results = requests.post('https://' + url + '/recaptcha/api/siteverify',
                                    data=data,
                                    timeout=1,
                                    verify=verify)
            info = json.loads(results.text)
            return info.get('success', False)
        except requests.exceptions.ConnectionError as einfo:
            logging.error(einfo)
    return True  # If we can't verify, let it pass


@FLASKAPP.route("/<uuid:tabsession>/logout", methods=['GET', 'POST'])
def logout(tabsession):
    ''' a session has left the browser '''
    logging.debug("Received logout/exit for " + str(tabsession))
    TM.stoptelnetsession(tabsession)
    SESSIONS.removesession(tabsession)
    if "sessions" in session:
        sessionlist = session['sessions']
        if tabsession in sessionlist:
            sessionlist.remove(tabsession)
            session['sessions'] = sessionlist
    return ('', 204)


@FLASKAPP.route("/<uuid:tabsession>/upload/<filename>", methods=['POST'])
@FLASKAPP.route("/login/<uuid:tabsession>/upload/<filename>", methods=['POST'])
@session_required(True)
def upload(tabsession, filename):
    ''' receive a file for upload '''
    if request.method == "POST":
        for uploadfile in request.files:
            filepath = os.path.join("uploads", str(tabsession))
            if not os.path.exists(filepath):
                os.mkdir(filepath)
            filepath = os.path.join(filepath, secure_filename(filename))
            request.files[uploadfile].save(filepath)
            # return filename
            if request.form.get('retfile', "0") == "1":
                TM.senddata(tabsession, chr(27) + "WHIR:" + filepath + chr(13))
            elif request.form.get('noresponse', "0") == "1":
                pass
            else:
                TM.senddata(tabsession, chr(27) + "WDF" + WinGemPacket.AM + "DONE" +
                            WinGemPacket.AM + filepath)
        return jsonify(filepath=fixslashes(filepath))
    return ('', 204)


@FLASKAPP.route("/<uuid:tabsession>/render", methods=['POST'])
@FLASKAPP.route("/<cmd>/<uuid:tabsession>/render", methods=['POST'])
@session_required(True)
def renderdata(tabsession, cmd=None):
    ''' Render object '''
    renderids = request.form["id"]
    renderitem = json.loads('{"ids":' + renderids + "}")
    # print(renderids, renderitem)
    finaldata = dict()
    for renderid in renderitem["ids"]:
        obj = TM.getrenderdata(tabsession, renderid)
        datatoadd = ""
        if obj:
            try:
                if obj.gettype() == "SCREEN":
                    datatoadd = render_template("screen.html", screen=obj, cmd=cmd)
                elif obj.gettype() == "BGBROWSER":
                    datatoadd = render_template("bgbrowser.html", browser=obj, cmd=cmd)
                elif obj.gettype() == "PROMPT":
                    screenobj = TM.getscreen(tabsession, obj.screenid)
                    if screenobj and obj:
                        datatoadd = render_template("prompt.html", prompt=obj,
                                                    screen=screenobj, cmd=cmd)
                elif obj.gettype() == "GRID":
                    screenobj = TM.getscreen(tabsession, int(obj.gridid.split("_")[0]))
                    if screenobj and obj:
                        datatoadd = render_template("grid.html", grid=obj,
                                                    screen=screenobj)
                elif obj.gettype() == "TEXT":
                    screenobj = TM.getscreen(tabsession, obj.screenid)
                    if screenobj and obj:
                        datatoadd = render_template("text.html", text=obj,
                                                    screen=screenobj)
                elif obj.gettype() == "MENU":
                    datatoadd = render_template("menu.html", menu=obj)
                elif obj.gettype() == "BUTTON":
                    screenobj = TM.getscreen(tabsession, obj.screenid)
                    if screenobj and obj:
                        datatoadd = render_template("button.html", button=obj,
                                                    screen=screenobj)
                elif obj.gettype() == "COMMANDBAR":
                    datatoadd = render_template("commandbar.html", commandbar=obj)
                # May eventually need COMMANDBARBAND rendering
                elif obj.gettype() == "COMMANDBARTOOL":
                    commandbar = TM.getcommandbar(tabsession)
                    commandbar.update_for_alt_languages()
                    datatoadd = render_template("commandbartool.html",
                                                tool=obj,
                                                commandbar=commandbar,
                                                myband=obj.parents[list(obj.parents.keys())[0]])
                elif obj.gettype() == "MENUBAR":
                    screenobj = TM.getscreen(tabsession, obj.screenid)
                    if screenobj and obj:
                        datatoadd = render_template("menubar.html", menubar=obj,
                                                    screen=screenobj,
                                                    startrow=0, startcol=0)
                elif obj.gettype() == "EDITOR":
                    # JHO 20170927: Don't think this can ever happen now
                    datatoadd = render_template("editor.html", editor=obj)
            except UndefinedError:
                # sometimes screen is closed before prompt drawing
                logging.error("Template error: " + str(traceback.format_exc().splitlines()))

            if isinstance(datatoadd, str):
                datatoadd = re.sub(r'^\s+(?=(<|\w+="|data-|>\n))', "",
                                        datatoadd, flags=re.MULTILINE)
            finaldata["r"+renderid] = datatoadd
    return jsonify(finaldata)


@FLASKAPP.route("/<uuid:tabsession>/edit/<path:filepath>", methods=['GET', 'PUT'])
@FLASKAPP.route("/login/<uuid:tabsession>/edit/<path:filepath>", methods=['GET', 'PUT'])
@session_required(True)
def edit(tabsession, filepath):
    ''' Edit File '''
    # Must have a path
    if not filepath:
        return ('', 400)  # Bad Request (I like 418 better)

    dirname, filename = components.filetransfer.getfiletuple(filepath, "READ", str(tabsession))
    filename = secure_filename(filename)
    newfilepath = dirname + filename

    # Only read/write content under static\data
    if dirname[0:12] != "static" + os.sep + "data" + os.sep:
        return ('', 403)  # Forbidden

    # Only read/write content that exists
    if not os.path.isfile(newfilepath):
        return ('', 404)  # Not Found

    # Read content and return on GET request
    if request.method == "GET":
        return send_file(newfilepath, "text/plain;charset=ISO-8859-1")

    # Save backup
    backupfolder = "static" + os.sep + "data" + os.sep + "editorbackups" + os.sep
    if os.path.isdir(backupfolder):
        backupfilepath = backupfolder + filename + "-" + \
            datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        with open(backupfilepath, "wb") as bakfile:
            bakfile.write(request.data)
        bakfile.close()

    # update WD file from PUT
    try:
        with open(newfilepath, "wb") as upfile:
            filedata = request.data
            # value is hard-coded from flask layer, so we know it's utf-8
            filedata = filedata.decode("utf-8")
            filedata = unicodetoascii(filedata)
            # convert to host friendly encoding
            filedata = filedata.encode("ISO-8859-1")
            upfile.write(filedata)
        upfile.close()
    except UnicodeEncodeError as einfo:
        errnum = 500
        errmsg = ""

        if einfo.start >= 0 and einfo.end >= 0:
            # Extract bad character
            badchar = filedata[int(einfo.start):int(einfo.end)]

            # Find line number
            lines = filedata.split(badchar)[0]
            lines = lines.split("\n")
            linendx = len(lines)

            # Find column
            lastline = lines[-1]
            colndx = len(lastline) + 1

            # Translate bad character for display in non-unicode realm
            badchar = badchar.encode("ISO-8859-1", "xmlcharrefreplace").decode("ISO-8859-1")

            # Build error message
            errnum = 400  # Bad Request
            errmsg = "'" + badchar + "' is an invalid character.  Please fix before saving.<br>"
            errmsg += "Line: " + str(linendx) + "<br>"
            errmsg += "Column: " + str(colndx)

        return (errmsg, errnum)  # Server Error
    except Exception as einfo:  # pylint:disable=broad-except
        logging.error(einfo)
        return ('', 500)  # Server Error
    else:  # success
        TM.senddata(tabsession, chr(27) + "WHIR:WDEC" + WinGemPacket.VM + "SAVE" + chr(13))
        return ('', 204)


@FLASKAPP.route("/<uuid:tabsession>/external/<fileid>", methods=['GET'])
@FLASKAPP.route("/login/<uuid:tabsession>/external/<fileid>", methods=['GET'])
@session_required(True, True)
def external(tabsession, fileid):
    ''' get external file '''
    filename = TM.getexternalfile(tabsession, fileid)
    return render_template("externalbrowser.html", target=filename, sessionid=tabsession)


@FLASKAPP.route("/<uuid:tabsession>/diff", methods=['GET'])
@FLASKAPP.route("/login/<uuid:tabsession>/diff", methods=['GET'])
@FLASKAPP.route("/<uuid:tabsession>/view", methods=['GET'])
@FLASKAPP.route("/login/<uuid:tabsession>/view", methods=['GET'])
@session_required(True)
def view(tabsession):
    ''' Get view single file or diff of two '''

    if request.path[-5:] == "/diff":
        diff = True
        action = "DIFF"
        modfilepath = request.args["mod"]
    else:
        diff = False
        action = "EDIT"
        modfilepath = ""

    origfilepath = request.args["orig"]

    # Must have a path
    if (diff and not modfilepath) or not origfilepath:
        return ('', 400)  # Bad Request (I like 418 better)

    # Separate and rebuild "modified" file path
    moddirname, modfilename = components.filetransfer.getfiletuple(
        modfilepath, "READ", str(tabsession))
    modfilename = secure_filename(modfilename)
    newmodfilepath = moddirname + modfilename

    # Separate and rebuild "original" file path
    origdirname, origfilename = components.filetransfer.getfiletuple(
        origfilepath, "READ", str(tabsession))
    origfilename = secure_filename(origfilename)
    neworigfilepath = origdirname + origfilename

    # Only read/write content under static\data
    if (diff and moddirname[0:12] != "static" + os.sep + "data" + os.sep) or \
            origdirname[0:12] != "static" + os.sep + "data" + os.sep:
        return ('', 403)  # Forbidden

    # Only read/write content that exists
    if (diff and not os.path.isfile(newmodfilepath)) or not os.path.isfile(neworigfilepath):
        return ('', 404)  # Not Found

    return render_template("editorwrapper.html", sessionid=tabsession,
                           modfilepath=modfilepath, origfilepath=origfilepath,
                           action=action)

@FLASKAPP.route("/loggedout/<loginserver>", methods=['GET'])
@FLASKAPP.route("/loggedout", methods=['GET'])
def loggedout(loginserver=None):
    ''' Landing page for autologin sessions that log out '''
    return render_template("loggedout.html", loginserver=loginserver)

# ===============================================
# Performance Test Suite
# ===============================================


@FLASKAPP.route("/performance", methods=["GET"])
def performance():
    ''' Test Performance '''
    if not CONFIG['PERFORMANCE']:
        return rejectroute(True)
    return render_template("performance.html")


@FLASKAPP.route("/perfupload", methods=["POST"])
def perfupload():
    ''' Test Upload '''
    if not CONFIG['PERFORMANCE']:
        return rejectroute(True)
    return ("", 204)


@FLASKAPP.route("/perfdownload", methods=["GET"])
def perfdownload():
    ''' Test Download '''
    if not CONFIG['PERFORMANCE']:
        return rejectroute(True)
    def generate():
        ''' generate data '''
        yield ("101010101010" * 1048576) + '\n'
    return Response(generate(), mimetype='text')


@FLASKAPP.route("/perflatency", methods=["GET"])
def perflatency():
    ''' Test Latency '''
    if not CONFIG['PERFORMANCE']:
        return rejectroute(True)
    return ("", 204)


@FLASKAPP.route("/perflog", methods=["POST"])
def perflog():
    ''' Log a performance result '''
    if not CONFIG['PERFORMANCE']:
        return rejectroute(True)
    results = request.json
    try:
        clientip = request.headers["X-Real-IP"]
    except KeyError:
        clientip = request.remote_addr
    # log data
    logging.info("Performance Results: " + str(results) + ", from " + clientip)
    return ("", 204)


@FLASKAPP.route("/static/data/<version>/<uuid:tabsession>/<path:file>", methods=['GET'])
@session_required(True, True)
def static_session_file(version, tabsession, file):
    ''' Require session before returning static files from session-specific folder '''
    as_attachment = True if os.path.splitext(file)[1] == ".txt" else False
    mimetype = mimetypes.guess_type(file)[0]
    if mimetype:
        mimetype += ";charset=ISO-8859-1"
    directory = "static/data/" + version + "/" + str(tabsession) + "/"
    if CONFIG["EXECUTABLE"]:
        directory = os.path.join(CWD, directory)
    return send_from_directory(directory, file, as_attachment=as_attachment, mimetype=mimetype)


# ===============================================
# Test Route - TODO: disable when not in debug mode?
# ===============================================


@FLASKAPP.route("/<uuid:tabsession>/logfile", methods=['GET'])
def runlogfile(tabsession):
    ''' connect to host '''
    logging.info("Run log file")
    try:
        logfilepath = request.args['logfile']
        logdelay = request.args['logdelay']
        readlogfile(logfilepath, float(logdelay), TM, tabsession)
        SESSIONS.setloggedin(tabsession, True)
    except (IndexError, KeyError):
        if CONFIG['PRODUCTION']:
            return rejectroute(True)
        else:
            return jsonify({"error": "Session not established, refresh the page."})
    except IOError:
        if CONFIG['PRODUCTION']:
            return rejectroute(True)
        else:
            return jsonify({"error": "Could not read logfile " + logfilepath})
    return ('', 204)


@FLASKAPP.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    if not(request.path and request.path[:8] == "/static/") or \
            request.path[-3:] == "htm" or request.path[-4:] == "html" or \
            UUID_RE.search(request.path):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Expires'] = '0'
    return response


# ===============================================
# Jinja2 Custom Filters
# ===============================================


@FLASKAPP.template_filter('convertrowunittoem')
def convertrowunittoem(value):
    ''' Convert Row Unit to EM '''
    return components.applyscaling(value, True)


@FLASKAPP.template_filter('convertcolunittoem')
def convertcolunittoem(value):
    ''' Convert Col Unit to EM '''
    return components.applyscaling(value, False)


@FLASKAPP.template_filter('removehotkey')
def removehotkey(tag):
    ''' Remove hotkey indicator (ampersand) and convert double ampersands to &amp; '''
    return resource.removehotkey(tag)[0]


@FLASKAPP.template_filter('dateformat')
def dateformat(value, iformat='%d-%m-%Y'):
    ''' format date '''
    return value.strftime(iformat)


@FLASKAPP.template_filter('timeformat')
def timeformat(value, iformat='%H:%M'):
    ''' format time '''
    return value.strftime(iformat)


@FLASKAPP.template_filter('loadstring')
def loadstring(value):
    ''' get resource value '''
    return removehotkey(resource.loadstring(value))


@FLASKAPP.template_filter('nl2br')
@evalcontextfilter
def nl2br(eval_ctx, value):
    ''' convert newline to <br> '''
    result = value.replace('\r\n', Markup('<br>'))
    result = result.replace('\n', Markup('<br>'))
    result = result.replace('\r', Markup('<br>'))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


@FLASKAPP.template_filter('namefrompath')
def namefrompath(value):
    ''' Parse URL '''
    return value.split("/")[-1].split("\\")[-1]

@FLASKAPP.template_filter('py2js')
def py2js(value):
    ''' Convert python variable to JS variables '''
    if value:
        return "true"
    else:
        return "false"

# Configure JINJA2 Formatting
FLASKAPP.jinja_env.trim_blocks = True
FLASKAPP.jinja_env.lstrip_blocks = True

# Force auto-reloading of templates
FLASKAPP.jinja_env.auto_reload = True
FLASKAPP.config['TEMPLATES_AUTO_RELOAD'] = True

# Setup Session Manager
SESSIONS = SessionManager()
