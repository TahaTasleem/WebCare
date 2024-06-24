'''
Created on Feb 21, 2017

@author: daemo
'''

import logging
import logging.handlers
import os
from connector.configuration import CONFIG
from components.logfilemanager import cansessionlog

# disable raising of expections from within logging system
# usually just Unicode Encoding Issues
logging.raiseExceptions = False

# Extending the logger
PACKET_LEVEL_NUM = 9
logging.addLevelName(PACKET_LEVEL_NUM, "packet")


def packet(self, message, *args, **kws):
    ''' Packet log function '''
    # Yes, logger takes its '*args' as 'args'.
    if self.isEnabledFor(PACKET_LEVEL_NUM):
        self._log(PACKET_LEVEL_NUM, message, args, **kws)  # pylint: disable=protected-access


logging.Logger.packet = packet


class WebdirectFormatter(logging.Formatter):
    ''' set up custom formatter to conditionally apply logging
     if their session is enabled, or it's a severe error '''

    def filter(self, record):
        ''' returns whether or not they can log '''
        # always log in development
        if not CONFIG['PRODUCTION']:
            return True
        if CONFIG['LOGGING']:
            # print('logging config on')
            return True
        # always log if it's one of these three
        if record.levelname in ['ERROR', 'CRITICAL', 'WARNING']:
            return True
        # otherwise, check if we should log
        return cansessionlog(record.threadName)


def setuplogging():
    ''' Setup Logging Details '''

    # setup our format and filename, get our logger object
    try:
        os.mkdir("logs")
    except FileExistsError:
        # if it exists, we don't care
        pass
    except (OSError, IOError):
        print("Failed to create log directory")
        exit(-1)

    # setup a packet logger, default to packet level
    log_filename = 'logs/packets.log'
    logformat = logging.Formatter('[%(asctime)s]%(threadName)-36s|{%(filename)s:%(lineno)d}||%(message)s') # pylint:disable=line-too-long
    wdlogger = logging.getLogger("packetlogger")
    wdlogger.addFilter(WebdirectFormatter())
    # wdlogger.setLevel(PACKET_LEVEL_NUM)
    wdlogger.setLevel(CONFIG["LOG_PACKETS"])
    handler = logging.handlers.RotatingFileHandler(
        log_filename, maxBytes=5000000, backupCount=10)
    handler.setFormatter(logformat)
    handler.setLevel(5)
    wdlogger.addHandler(handler)

    # General WebDirect Logging (Debug, Errors, Info, etc...)
    logformat = logging.Formatter('%(asctime)s|%(levelname)-8s|%(threadName)-36s|{%(filename)s:%(lineno)d}||%(message)s') # pylint:disable=line-too-long
    log_filename = 'logs/webdirect.log'
    wdlogger = logging.getLogger()
    wdlogger.addFilter(WebdirectFormatter())
    wdlogger.setLevel(min(CONFIG["LOG_CONSOLE"], CONFIG["LOG_FILE"]))

    # setup a file logger
    handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=5000000)
    handler.setFormatter(logformat)
    handler.setLevel(CONFIG["LOG_FILE"])
    wdlogger.addHandler(handler)

    # Setup our streaming logger
    handler = logging.StreamHandler()
    handler.setFormatter(logformat)
    handler.setLevel(CONFIG["LOG_CONSOLE"])
    wdlogger.addHandler(handler)
