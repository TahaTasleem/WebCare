'''
Created on Jan 25, 2017

@author: bouchcla
'''
import base64
import logging
import os.path
from configparser import ConfigParser, NoOptionError, NoSectionError
from datetime import datetime

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from connector.wingempacket import WinGemPacket
from connector import resource


class WDConfigParser(ConfigParser):
    '''
        Extend config parser to allow for lists
        see: http://stackoverflow.com/questions/335695/lists-in-configparser
    '''

    def getlist(self, section, option):
        ''' Get List of strings '''
        value = str(self.get(section, option))
        return list(filter(None, (x.strip() for x in value.splitlines())))

    def getlistint(self, section, option):
        ''' Get list of integers '''
        return [int(x) for x in self.getlist(section, option)]


def translateloglevel(loglevel: str):
    ''' convert log level to internal logging representation '''
    if loglevel == "0":
        return logging.NOTSET
    elif loglevel == "1":
        return logging.ERROR
    elif loglevel == '2':
        return logging.WARN
    elif loglevel == '3':
        return logging.INFO
    elif loglevel == '4':
        return logging.DEBUG
    else:
        return 9

CONFIG = {}

# Executable Defaults
CONFIG["EXECUTABLE"]= False
CONFIG["INSTANCE_PATH"] = ""

def base_dir():
    """ Get the parent directory or absolute path for the running code."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    CONFIG["INSTANCE_PATH"]= parent_dir

def open_path_file(file_path, mode='r', encoding=None):
    """Open a file located within the INSTANCE_PATH directory."""
    full_path = os.path.join(CONFIG["INSTANCE_PATH"], file_path)
    return open(full_path, mode, encoding=encoding)


# WebDirect Details, hard coded
MAJOR = 1
MINOR = 6
PATCH = 10
BUILD = "dev"
BUILDDATE = datetime.today()
try:
    base_dir()
    with open_path_file("build.hash", "r", encoding="utf-8") as versionnum:
        BUILD = versionnum.read()
        BUILDDATE = datetime.fromtimestamp(os.path.getmtime("build.hash"))
except IOError:
    # ignore file errors, assume dev version
    pass


CONFIG['BROWSERTIMEOUT'] = 15  # 15 minutes
CONFIG["VERSION"] = f"{MAJOR}.{MINOR}.{PATCH}"
CONFIG["BUILD"] = str(BUILD)
CONFIG["BUILDDATE"] = BUILDDATE
CONFIG['FOLDERCLEANUP'] = 3  # 3 days

# Defaults
CONFIG["PRODUCTION"] = False
CONFIG["PERFORMANCE"] = False
CONFIG["PRODUCT"] = "AXIS"
CONFIG["MFA"] = {}
CONFIG["PORT"] = 8080
CONFIG["SERVERS"] = ()
CONFIG["ACCOUNTS"] = {}
CONFIG["SSL"] = {}
CONFIG["SSH"] = {}
CONFIG["HOST"] = {}
CONFIG["AZURE"] = {}
CONFIG["AUTO"] = {}
CONFIG["USER"] = {}
CONFIG["PASS"] = {}
CONFIG["CLIENTID"] = {}
CONFIG["TENANTID"] = {}
CONFIG["ALLOWFREEFORMLOGIN"] = False
CONFIG["LOGINEXCEPTIONURL"] = ""
CONFIG["AUTHSTRINGS"] = ["duo", "otp."]
CONFIG["DEFAULT"] = ""
CONFIG["CORS_ALLOWED_ORIGINS"] = ""
CONFIG["CAPTCHA"] = False

# Logging defaults if no config file
CONFIG["LOG_PACKETS"] = 0
CONFIG["LOG_CONSOLE"] = 1
CONFIG["LOG_FILE"] = 3
CONFIG["LOGGING"] = True


def readsettings(config):
    """ Read configuration that comes under [WEBDIRECT] """
    CONFIG["PRODUCT"] = config.get("WEBDIRECT","product", fallback = "GoldCare")
    CONFIG["PRODUCTION"] = config.getboolean("WEBDIRECT", "production", fallback=False)
    CONFIG["PERFORMANCE"] = config.getboolean("WEBDIRECT", "performance", fallback=False)
    CONFIG["PORT"] = config["WEBDIRECT"].get("port",fallback=8080)
    CONFIG["SSL_ENABLE"] = config.getboolean("WEBDIRECT", "ssl_enable", fallback=False)
    CONFIG["SSL_CERTIFICATE"] = config["WEBDIRECT"].get("ssl_certificate", fallback="cert.pem")
    CONFIG["SSL_KEY"] = config["WEBDIRECT"].get("ssl_key", fallback="key.pem")
    CONFIG["EXECUTABLE"] = config.getboolean("WEBDIRECT","executable",fallback=False)
    # Not yet
    # if CONFIG["PRODUCT"] == "GoldCare":
    #     CONFIG["CAPTCHA"] = True
    CONFIG["CAPTCHA"] = config.getboolean("WEBDIRECT","captcha",fallback=CONFIG["CAPTCHA"])

    try:
        CONFIG["ALLOWFREEFORMLOGIN"] = config.getboolean("WEBDIRECT", "allowfreeformlogin",
                                                             fallback=False)
    except ValueError:
        CONFIG["ALLOWFREEFORMLOGIN"] = False

    CONFIG["LOGINEXCEPTIONURL"] = config.get("WEBDIRECT", "loginexceptionurl", fallback="")
    CONFIG["DEFAULT"] = config.get("WEBDIRECT", "default", fallback="")
    CONFIG["LOGGING"] = config.getboolean("WEBDIRECT", "logging", fallback=False)

    # setup CORS Allowed Origins
    try:
        CONFIG["CORS_ALLOWED_ORIGINS"] = config.getlist("WEBDIRECT", "cors_allowed_origins")
    except (ValueError, NoOptionError):
        pass

    # setup timeout
    CONFIG['BROWSERTIMEOUT'] = config.getint("WEBDIRECT", "browsertimeout", fallback=15)

    # folder cleanup
    CONFIG['FOLDERCLEANUP'] = config.getint("WEBDIRECT", "foldercleanup", fallback=7)

    #language config (load language if not available default to english)
    language = config["WEBDIRECT"].get("language", 'en').lower()

    if language not in ("fr", "en"):
        language = "en"

    resource.setlanguage(language)

    # authorization strings
    try:
        authstrings = config.getlist("WEBDIRECT", "authstrings")
    except (ValueError, NoOptionError):
        authstrings = []
    CONFIG['AUTHSTRINGS'].extend(authstrings)


def readlogs(config):
    """ Read configuration that comes under [LOGGING] """
    CONFIG["LOG_PACKETS"] = translateloglevel(config.get("LOGGING", "packet", fallback=0))
    CONFIG["LOG_CONSOLE"] = translateloglevel(config.get("LOGGING", "console", fallback=1))
    CONFIG["LOG_FILE"] = translateloglevel(config.get("LOGGING", "logfile", fallback=3))

def readservers(config):
    """ Read configuration that comes under [SERVERS] """
    CONFIG['SERVERS'] = config.getlist("SERVERS", "names")
    for servername in CONFIG["SERVERS"]:
        try:
            CONFIG["ACCOUNTS"][servername] = config.getlist("-".join(("SERVER", servername)),
                                                                "account")
            CONFIG["SSL"][servername] = config.getboolean("-".join(("SERVER", servername)),
                                                              "ssl", fallback=True)
            CONFIG["SSH"][servername] = config.getboolean("-".join(("SERVER", servername)),
                                                              "ssh", fallback=False)
            CONFIG["MFA"][servername] = config.getboolean("-".join(("SERVER", servername)),
                                                              "mfa", fallback=False)
        except NoSectionError:
            CONFIG["ACCOUNTS"][servername] = ()
            CONFIG["SSL"][servername] = True
            CONFIG["SSH"][servername] = False
            CONFIG["MFA"][servername] = False
        except ValueError:
            CONFIG["SSL"][servername] = True
            CONFIG["SSH"][servername] = False
            CONFIG["MFA"][servername] = False

        try:
            CONFIG["HOST"][servername] = config.get(
                    "-".join(("SERVER", servername)), "host")
        except (ValueError, NoOptionError):
            CONFIG["HOST"][servername] = servername

        try:
            CONFIG["AUTO"][servername] = config.getboolean("-".join(("SERVER", servername)),
                                                               "auto", fallback=False)
        except (ValueError, NoOptionError):
            pass

        if CONFIG["AUTO"][servername]:
            try:
                CONFIG["USER"][servername] = config.get(
                        "-".join(("SERVER", servername)), "user")
            except (ValueError, NoOptionError):
                CONFIG["USER"][servername] = ""

            try:
                CONFIG["PASS"][servername] = config.get(
                        "-".join(("SERVER", servername)), "pass")
            except (ValueError, NoOptionError):
                CONFIG["PASS"][servername] = ""
            try:
                CONFIG["AZURE"][servername] = config.getboolean(
                        "-".join(("SERVER", servername)), "azure", fallback=False)
                CONFIG["CLIENTID"][servername] = config.get(
                        "-".join(("SERVER", servername)), "clientid")
                CONFIG["TENANTID"][servername] = config.get(
                        "-".join(("SERVER", servername)), "tenantid")
            except (ValueError, NoOptionError):
                CONFIG["AZURE"][servername] = False
                CONFIG["CLIENTID"][servername] = ""
                CONFIG["TENANTID"][servername] = ""


def readconfigfromfile(filelocation):
    '''
    Read in configuration from file.

    This function is responsible for loading configuration settings from an INI file. 
    The INI file may be compiled with the executable, and if an external configuration
    file is provided, it will overwrite the settings provided in that file, falling back
    to default settings when necessary.

    Args:
        filelocation (str): The path to an external INI file containing configuration settings.

    Returns:
        bool: True if the external INI file was successfully read and processed, False otherwise.
        '''
    location = os.path.join(CONFIG["INSTANCE_PATH"],"webdirect.ini")
    config = WDConfigParser()
    default_config = WDConfigParser()
    default_config.read(location)
    if config.read(filelocation):
        if "WEBDIRECT" not in config:
            readsettings(default_config)
        else:
            readsettings(config)

        if "LOGGING" not in config:
            readlogs(default_config)
        else:
            readlogs(config)

        if "SERVERS" not in config:
            readservers(default_config)
        else:
            readservers(config)

        return True
    return False
    #===========================================================================
    # for x in CONFIG["ACCOUNTS"]:
    #     print("Server:" + x)
    #     print("  SSL:" + str(CONFIG["SSL"][x]))
    #     for y in CONFIG["ACCOUNTS"][x]:
    #         print("  Accounts:" + y)
    #===========================================================================


# Support the ability to read config file from a folder
# Docker on Windows doesn't support file mapping, only folder mapping
if not readconfigfromfile("config/webdirect.ini"):
    filepath = os.path.join(CONFIG["INSTANCE_PATH"],"webdirect.ini")
    readconfigfromfile(filepath)

def key_from_file(key_file):
    ''' extract the key from the file '''
    try:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )
        key_file.close()
        return private_key
    except (ValueError, IndexError):
        return ""

def cipher_from_file(cipher_file):
    ''' extract the cipher from the file'''
    try:
        ciphertext = cipher_file.read()
        ciphertext = base64.b64decode(ciphertext)
        cipher_file.close()
        return ciphertext
    except (ValueError, IndexError):
        return ""

def get_credentials(server):
    '''try to read the user/pass from stored location'''
    try:
        key_file = open_path_file('config' + os.sep + 'gclogin.pem', 'rb')
        private_key = key_from_file(key_file)
    except FileNotFoundError:
        try:
            key_file = open_path_file('gclogin.pem', 'rb')
            private_key = key_from_file(key_file)
        except FileNotFoundError:
            private_key = ""

    if private_key:
        try:
            cipher_file = open_path_file('config' + os.sep + 'static' + os.sep + 'gclogin', 'rb')
            ciphertext = cipher_from_file(cipher_file)
        except FileNotFoundError:
            try:
                cipher_file = open_path_file('static' + os.sep + 'gclogin', 'rb')
                ciphertext = cipher_from_file(cipher_file)
            except FileNotFoundError:
                ciphertext = ""

    if private_key and ciphertext:
        try:
            plaintext = private_key.decrypt(
                ciphertext,
                padding.PKCS1v15()
            )
            plaintext = plaintext.decode("ISO-8859-1").split(WinGemPacket.VM)
            user = plaintext[0]
            password = plaintext[1]
        except (ValueError, IndexError):
            user = CONFIG["USER"][server]
            password = CONFIG["PASS"][server]
    else:
        user = CONFIG["USER"][server]
        password = CONFIG["PASS"][server]
    return user, password
