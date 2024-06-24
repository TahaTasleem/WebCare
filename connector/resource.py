'''
Created on Dec 12, 2016

@author: holthjef
'''
# pylint:disable=line-too-long,too-many-lines

# See API.bas in WinGem for various bitmap/icon, string loading functions

import os
import logging
import re
import html
import threading

import components
from connector.languageresource import _STRING_MAP, LANG_EN, LANG_FR

def removehotkey(stringresource: str):
    ''' Return string without hotkey identifier (ampersand), and hotkey '''

    cleanstring = ""
    hotkey = ""

    #===============================================================================
    # Find single ampersand and return next character
    #  - First block in brackets says "if preceding character is not an ampersand"
    #  - Second block in brackets says "if following character is not an ampersand or a space"
    #  - The ampersand in the middle is the target ampersand
    # Note: If language is france string should be unescaped first before removing hot key identifier to avoid double decoding of characters
    #===============================================================================

    if _LANGUAGE == LANG_FR:
        stringresource = html.unescape(stringresource)

    searchresult = re.search(r"(?<!&)&(?![& ])", stringresource)
    if searchresult:
        hotkeyndx = searchresult.span()[0] + 1
        if hotkeyndx > 0 and hotkeyndx < len(stringresource):
            hotkey = stringresource[hotkeyndx]

    # Remove all single ampersands that are valid hotkey indicators
    cleanstring = re.sub(r"(?<!&)&(?![& ])", "", stringresource)

    # Replace double ampersands with ampersand literal
    cleanstring = cleanstring.replace("&&", "&amp;")

    return cleanstring, hotkey


def loadimage(resourceid: str):
    ''' Return path for image in POSIX/URI format'''

    resourceid = resourceid.lower()

    try:
        # Assume icons don't differ between languages
        imagepath = _IMAGE_MAP[LANG_EN][resourceid]
    except KeyError:
        imagepath = _loadimagefrom(resourceid, os.sep.join(["static", "wdres"]))

    # If image was not found in wdres load it from static/data folder
    if resourceid and not imagepath:
        imagepath = _loadimagefromdata(resourceid)

    return imagepath


def _loadimagefrom(resourceid: str, location: str):
    ''' Return path for image in POSIX/URI format from specified location relative to webdirect '''

    # Returns empty string if not found
    imagepath = ""

    # Get Webdirect directory
    wddir = getwddir()

    try:
        # resourceid should already be lowered by loadimage()
        searchdir = os.path.join(wddir, location)
        filelist = os.listdir(searchdir)

        filename = ""
        for filename in filelist:
            if resourceid == filename.lower():
                # Always return in unix/uri style (location may contain os-specific seperator)
                imagepath = os.path.join(location, filename).replace("\\", "/")
                # image path will be static/wdres/xyz.zyx, split and take everything from wdres on
                tpath = imagepath.split("/")[1:]
                # make it back into a string with "/" seperators, assumed safe since it used to leave it at
                # those previously.
                imagepath = "/".join(tpath)
                # Assume icons don't differ between languages
                _IMAGE_MAP[LANG_EN][resourceid] = imagepath
                break
    except FileNotFoundError:
        logging.error(" ".join(["Loading resource", resourceid,
                                "failed to find", searchdir]))

    return imagepath

def _loadimagefromdata(resourceid: str):
    """
    Load image from data folder
    """

    # fix slashes for os indepedent behaviour and remove leading ../ if any
    resourceid = re.sub( r"^\.\.[\\/]", "", components.filetransfer.fixslashes(resourceid) )

    # if dataverfolder is mentioned in the file itself then use it
    dataverfolder, resourceid = getwddatadirifinresourcepath(resourceid)

    # If there is session related folder (i.e created by filetransfer) get resource from it otherwise scan all folders for availablity
    dataverfolder = getwddatadirbysession() or getwddatadirbyscanning(resourceid)

    # If no dataversionfolder is returned then return empty string
    if not dataverfolder:
        return ""

    dataverfolder = components.filetransfer.fixslashes(dataverfolder)
    # get file name
    file_name = os.path.join(dataverfolder, resourceid)

    # check file exists and file_name is in directory i.e user did not used something like "..." to scroll to the folders (security issue)
    file_name = file_name if file_name.startswith(dataverfolder) and os.path.exists(file_name) and os.path.isfile(file_name) else ''

    if file_name:
        # get file path
        file_match = re.match(r"^.+static.(data.[vV]\d+.*)", file_name)

        # if file match then return relative path of the resource
        file_name =  file_match.group(1).replace("\\", "/") if file_match else ""

    return file_name


def loadstring(resourceid: str):
    ''' Return string for current language '''

    try:
        textstring = getcurrentlanguagemap()[resourceid]
    except Exception:  # pylint:disable=broad-except
        textstring = ""

    return textstring


def getcolorref(resourceid: str):
    ''' Return string for current language '''

    try:
        if len(resourceid) == 6:
            # Colour is already a hex code, just return it
            textstring = resourceid
        else:
            textstring = _COLOUR_MAP[_LANGUAGE][resourceid]
    except Exception:  # pylint:disable=broad-except
        textstring = ""

    return textstring


def getwddir():
    """
    Get webdirect directory
    """

    # Get webdirect path (done this way to work in unittest, too)
    mydir = os.path.split(__file__)[0]
    wddir = os.path.split(mydir)[0]

    return wddir


def getwddatadir():
    """ Get static/data folder path """
    wddir = getwddir()
    return os.path.join(wddir, "static/data")


def getdatafolderrootandsubdirs():
    """Returns Folder path to static/data and its subdirs (i.e version directories)"""
    datafolder =  getwddatadir()

    for _,version_dirs,_ in os.walk(datafolder):
        return datafolder, version_dirs

    return datafolder, []

def getwddatadirbysession():
    """ Get Static/Data directory based on current session """
    # folder version, a single session can be in multiple folder select the latest one
    folderver = ""
    folderverdate = None

    # get data folder and versions directories
    datafolder, version_dirs = getdatafolderrootandsubdirs()
    sessionid = getsessionid()

    for version_dir in version_dirs:
        version_folder = os.path.join(datafolder, f"{version_dir}")
        session_path = os.path.join(version_folder, f"{sessionid}")

        if os.path.exists(session_path) and os.path.isdir(session_path):
            session_path_mod_time = os.path.getmtime(session_path)

            # if current session folder modified date is greater than earlier replace it with the new
            if not folderverdate or session_path_mod_time > folderverdate:
                folderverdate = session_path_mod_time
                folderver = version_folder

    # return data/XXXX/ (i.e version folder)
    return folderver


def getwddatadirbyscanning(resourceid):
    """ Scan resource in version directories """
    # get data folder and versions directories
    datafolder, version_dirs = getdatafolderrootandsubdirs()

    for version_dir in version_dirs:
        version_folder = os.path.join(datafolder, f"{version_dir}")
        resource_location = os.path.join(version_folder, resourceid)

        # if file is found in version_folder then return it
        if os.path.exists(resource_location):
            return version_folder


def getwddatadirifinresourcepath(resourceid):
    """ Extract data version folder if in resource (if it exists also returns resource path with respect to data ver folder) """
    # get data folder and versions directories

    resource_match = re.match(r"([vV]\d{2,4}[\d\w]{0,1})[\\/](.*)", resourceid)
    dataverfolder = None

    if resource_match:
        version_folder = resource_match.group(1)
        dataverfolder =  os.path.join( getwddatadir(), version_folder )
        resourceid = resource_match.group(2)

    return dataverfolder, resourceid


def getsessionid():
    """Get Current Socket Session Id"""
    return threading.current_thread().name

def setlanguage(language: str):
    ''' Change language currently in use '''

    global _LANGUAGE  # pylint:disable=global-statement
    _LANGUAGE = language
    return True


def getlanguage():
    ''' Return language currently in use '''
    return _LANGUAGE

def getcurrentlanguagemap():
    """
    Returns Current Language Map Object
    """
    return _STRING_MAP[_LANGUAGE]


_LANGUAGE = LANG_EN

# Image file locations (only maintain english list until otherwise necessary)
_IMAGE_MAP = {
    "en": {
        "accounting.ico": "wdres/accounting.svg",
        "afw_reports.ico": "wdres/afw_reports.svg",
        "application.ico": "wdres/application.svg",
        "arrow_empty.ico": "wdres/arrow_empty.svg",
        "arrow_fill.ico": "wdres/arrow_fill.svg",
        "auto_touring.ico": "wdres/auto_touring.svg",
        "axis_navigator.ico": "wdres/axis_navigator.svg",
        "axis_reports.ico": "wdres/axis_reports.svg",
        "axlogo.ico": "wdres/axlogo.svg",
        "back.ico": "wdres/back.svg",
        "blackarrow.ico": "wdres/blackarrow.svg",
        "branch_sch.ico": "wdres/branch_sch.svg",
        "calculator.ico": "wdres/calculator.svg",
        "calendar.ico": "wdres/calendar.svg",
        "canceltool.ico": "wdres/canceltool.svg",
        "cash_mgmt.ico": "wdres/cash_mgmt.svg",
        "cdend.ico": "wdres/cdend.svg",
        "cdfastfwd.ico": "wdres/cdfastfwd.svg",
        "cdrewind.ico": "wdres/cdrewind.svg",
        "cdstart.ico": "wdres/cdstart.svg",
        "certok.ico": "wdres/certok.svg",
        "checkoff.ico": "wdres/checkoff.svg",
        "checkon.ico": "wdres/checkon.svg",
        "client_feedback.ico": "wdres/client_feedback.svg",
        "commands.ico": "wdres/commands.svg",
        "connected.ico": "wdres/connected.svg",
        "copy.ico": "wdres/copy.svg",
        "counter_svc.ico": "wdres/counter_svc.svg",
        "critical.ico": "wdres/critical.svg",
        "database_mkg.ico": "wdres/database_mkg.svg",
        "debug_circlog.ico": "wdres/debug_circlog.svg",
        "debug_clm.ico": "wdres/debug_clm.svg",
        "debug_log.ico": "wdres/debug_log.svg",
        "debug_sessioninfo.ico": "wdres/debug_sessioninfo.svg",
        "dialog_mktg.ico": "wdres/dialog_mktg.svg",
        "disconnected.ico": "wdres/disconnected.svg",
        "download_green.ico": "wdres/download_green.svg",
        "download_red.ico": "wdres/download_red.svg",
        "download_yellow.ico": "wdres/download_yellow.svg",
        "ent_info_sys.ico": "wdres/ent_info_sys.svg",
        "envelope.ico": "wdres/envelope.svg",
        "execute.ico": "wdres/execute.svg",
        "exclamation.ico": "wdres/exclamation.svg",
        "file.ico": "wdres/file.svg",
        "folderopen.ico": "wdres/folderopen.svg",
        "font2.ico": "wdres/font2.svg",
        "fontdecrease.ico": "wdres/fontdecrease.svg",
        "fontincrease.ico": "wdres/fontincrease.svg",
        "formnameactive.ico": "wdres/formnameactive.svg",
        "formnameinactive.ico": "wdres/formnameinactive.svg",
        "forward.ico": "wdres/forward.svg",
        "gc_log.ico": "wdres/gc_log.svg",
        "gchelp.ico": "wdres/gchelp.png",
        "gclogo.ico": "wdres/gclogo.svg",
        "getlist.ico": "wdres/getlist.svg",
        "help.ico": "wdres/help.svg",
        "history.ico": "wdres/history.svg",
        "hollowarrow.ico": "wdres/hollowarrow.svg",
        "hotel_car_res.ico": "wdres/hotel_car_res.svg",
        "incentive.ico": "wdres/incentive.svg",
        "info.ico": "wdres/info.svg",
        "information.ico": "wdres/information.svg",
        "inventoryb.ico": "wdres/inventoryb.svg",
        "leads_mgmt.ico": "wdres/leads_mgmt.svg",
        "lifetime_value.ico": "wdres/lifetime_value.svg",
        "linedown.ico": "wdres/linedown.svg",
        "lineup.ico": "wdres/lineup.svg",
        "logout.ico": "wdres/logout.svg",
        "magnifyingglass.ico": "wdres/magnifyingglass.svg",
        "med_ins.ico": "wdres/med_ins.svg",
        "mem_req_tracking.ico": "wdres/mem_req_tracking.svg",
        "membership.ico": "wdres/membership.svg",
        "menudown.ico": "wdres/menudown.svg",
        "menureport.ico": "wdres/menureport.svg",
        "menutable.ico": "wdres/menutable.svg",
        "menuup.ico": "wdres/menuup.svg",
        "monitor_clr.ico": "wdres/monitor_clr.svg",
        "monitor_npd.ico": "wdres/monitor_npd.svg",
        "monitor_ok.ico": "wdres/monitor_ok.svg",
        "mrts_request.ico": "wdres/mrts_request.svg",
        "msg_man.ico": "wdres/msg_man.svg",
        "mtn_tables.ico": "wdres/mtn_tables.svg",
        "myor.ico": "wdres/myor.svg",
        "myorb.ico": "wdres/myorb.svg",
        "navback.ico": "wdres/navback.svg",
        "navforward.ico": "wdres/navforward.svg",
        "navigator.ico": "wdres/navigator.svg",
        "newmail.ico": "wdres/newmail.svg",
        "openfolderdd.ico": "wdres/openfolderdd.svg",
        "pagedown.ico": "wdres/pagedown.svg",
        "pageend.ico": "wdres/pageend.svg",
        "pagestart.ico": "wdres/pagestart.svg",
        "pageup.ico": "wdres/pageup.svg",
        "paste.ico": "wdres/paste.svg",
        "printer.ico": "wdres/printer.svg",
        "printscreen.ico": "wdres/printscreen.svg",
        "promo_resp_tracking.ico": "wdres/promo_resp_tracking.svg",
        "purchasing.ico": "wdres/purchasing.svg",
        "question.ico": "wdres/question.svg",
        "refresh.ico": "wdres/refresh.svg",
        "reportmenuitem.ico": "wdres/reportmenuitem.svg",
        "resizeterminalheight.ico": "wdres/resizeterminalheight.svg",
        "resizeterminalwidth.ico": "wdres/resizeterminalwidth.svg",
        "road_service.ico": "wdres/road_service.svg",
        "search.ico": "wdres/search.svg",
        "services_utilized.ico": "wdres/services_utilized.svg",
        "settings.ico": "wdres/settings.svg",
        "setup.ico": "wdres/setup.svg",
        "spell_check1.ico": "wdres/spell_check1.svg",
        "ssl.ico": "wdres/ssl.svg",
        "sundry.ico": "wdres/sundry.svg",
        "trav_chq.ico": "wdres/trav_chq.svg",
        "travel.ico": "wdres/travel.svg",
        "up.ico": "wdres/up.svg",
        "upfolder.ico": "wdres/upfolder.svg",
        "upload_green.ico": "wdres/upload_green.svg",
        "upload_red.ico": "wdres/upload_red.svg",
        "upload_yellow.ico": "wdres/upload_yellow.svg",
        "uptool.ico": "wdres/uptool.svg",
        "users.ico": "wdres/users.svg",
        "users_key.ico": "wdres/users_key.svg",
        "utilities.ico": "wdres/utilities.svg"
    }
}


# System colours, hardcoded as we can't access the system
_COLOUR_MAP = {
    "en": {
        "COLOR_3DDKSHADOW": "333333",
        "COLOR_3DFACE": "999999",
        "COLOR_3DHILIGHT": "dddddd",
        "COLOR_3DHIGHLIGHT": "dddddd",
        "COLOR_3DLIGHT": "cccccc",
        "COLOR_3DSHADOW": "444444",
        "COLOR_ACTIVEBORDER": "dddddd",
        "COLOR_ACTIVECAPTION": "dddddd",
        "COLOR_APPWORKSPACE": "bbbbbb",
        "COLOR_BACKGROUND": "999999",
        "COLOR_BTNFACE": "999999",
        "COLOR_BTNHILIGHT": "dddddd",
        "COLOR_BTNHIGHLIGHT": "dddddd",
        "COLOR_BTNSHADOW": "444444",
        "COLOR_BTNTEXT": "000000",
        "COLOR_CAPTIONTEXT": "000000",
        "COLOR_DESKTOP": "999999",
        "COLOR_GRAYTEXT": "999999",
        "COLOR_HIGHLIGHT": "dddddd",
        "COLOR_HIGHLIGHTTEXT": "bbbbbb",
        "COLOR_INACTIVEBORDER": "bbbbbb",
        "COLOR_INACTIVECAPTION": "bbbbbb",
        "COLOR_INACTIVECAPTIONTEXT": "444444",
        "COLOR_INFOBK": "999999",
        "COLOR_INFOTEXT": "000000",
        "COLOR_MENU": "999999",
        "COLOR_MENUTEXT": "000000",
        "COLOR_SCROLLBAR": "999999",
        "COLOR_WINDOW": "ffffff",
        "COLOR_WINDOWFRAME": "999999",
        "COLOR_WINDOWTEXT": "000000"
    }
}
