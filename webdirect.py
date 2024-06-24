'''
Created on Oct 19, 2016

@author: bouchcla
'''
# because we need to let eventlet handle threads, we need specific ordering of imports
# disable pylint's checking, because it incorrectly complains
# pylint: disable=wrong-import-position,wrong-import-order
import eventlet
eventlet.monkey_patch()

import logging
import os
import re
import shutil

import click

from webrouting import FLASKAPP, TM, SOCKETIO
from connector.configuration import CONFIG
from connector.logging import setuplogging


class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.
    '''

    def __init__(self, app):
        ''' constructor '''
        self.app = app

    def __call__(self, environ, start_response):
        ''' update path if behind a reverse proxy '''
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)


def cleanupolddirectories():
    ''' cleans up old directories in static folder '''
    guidre = r"[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}"
    for directory in os.listdir('static/data/'):
        if os.path.isdir("static/data/" + directory):
            if re.match(r"V[\d]{2,4}[\d\w]{0,1}", directory, flags=re.I):
                for subdirectory in os.listdir("static/data/" + directory + "/"):
                    if os.path.isdir("static/data/" + directory + "/" + subdirectory):
                        # remove any directories that are a GUID
                        if re.search(guidre, subdirectory, flags=re.I):
                            shutil.rmtree("static/data/" + directory + "/" + subdirectory,
                                          ignore_errors=True)
            if re.search(guidre, directory, flags=re.I):
                shutil.rmtree("static/data/" + directory, ignore_errors=True)
    try:
        for directory in os.listdir('uploads/'):
            if os.path.isdir("uploads/" + directory):
                if re.search(guidre, directory, flags=re.I):
                    shutil.rmtree("uploads/" + directory, ignore_errors=True)
    except Exception:  # pylint: disable=W0703
        # don't care if uploads isn't there yet
        pass


def setupfolders():
    ''' Setup any folders we need for webdirect '''
    if not os.path.exists("uploads/"):
        os.mkdir("uploads/")


def runserver():
    """  Runs Webdirect Server """
    ssl_kwargs = {}

    ssl_keyfile = CONFIG["SSL_KEY"]
    ssl_certfile = CONFIG["SSL_CERTIFICATE"]

    # enable ssl if it is enabled in config and cert and key is present
    if CONFIG["SSL_ENABLE"] and ssl_certfile and ssl_keyfile:
        ssl_kwargs = {"certfile" : ssl_certfile, "keyfile" : ssl_keyfile}

    SOCKETIO.run(FLASKAPP, host="0.0.0.0", port=CONFIG["PORT"], **ssl_kwargs)


@click.command()
@click.option("--config", default="webdirect.ini", help="Location of config file")
@click.option("--static", default="static/", help="Location of static files")
def main(config, static):  # pylint: disable=W0613
    ''' setup routine '''
    # don't do this if using a shared docker volume
    # cleanupolddirectories()
    FLASKAPP.config.update(CONFIG)
    setupfolders()
    setuplogging()
    # handle case where we are behind a reverse proxy (like nginx)
    FLASKAPP.wsgi_app = ReverseProxied(FLASKAPP.wsgi_app)
    # Serve the application from Waitress
    # port should be configured
    logging.info("Starting WebDirect v" + CONFIG["VERSION"] + " - " + CONFIG['BUILD'])
    runserver()

    # finalize cleanup
    TM.closetelnetsessions()


if __name__ == "__main__":
    main(None, None)
