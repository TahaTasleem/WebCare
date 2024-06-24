''' SSH Connection Module '''

# import os  # Used to setup the Paramiko log file
import logging  # Used to setup the Paramiko log file
import socket  # This method requires that we create our own socket
import selectors
import time
import traceback
import paramiko  # Provides SSH functionality
from connector.resource import loadstring
from connector.configuration import CONFIG


class SSH():
    ''' SSH Connection Handler '''

    def __init__(self):
        ''' Construtor '''
        self._socket = None
        self._channel = None
        self._transport = None
        self._lastread = time.time()
        self.eof = False
        self._user = ""
        self._password = ""
        self._passcode = ""
        self._callback = None

    def inter_handler(self, title, instructions, prompt_list):  # pylint: disable=W0613
        """
        inter_handler: the callback for paramiko.transport.auth_interactive

        The prototype for this function is defined by Paramiko, so all of the
        arguments need to be there, even though we don't use 'title' or
        'instructions'.

        The function is expected to return a tuple of data containing the
        responses to the provided prompts. Experimental results suggests that
        there will be one call of this function per prompt, but the mechanism
        allows for multiple prompts to be sent at once, so it's best to assume
        that that can happen.

        Since tuples can't really be built on the fly, the responses are
        collected in a list which is then converted to a tuple when it's time
        to return a value.

        Experiments suggest that the username prompt never happens. This makes
        sense, but the Username prompt is included here just in case.
        """

        resp = []  # Initialize the response container

        # Walk the list of prompts that the server sent that we need to answer
        for prompt in prompt_list:
            # str() used to to make sure that we're dealing with a string rather
            # than a unicode string
            # strip() used to get rid of any padding spaces sent by the server
            # print(prompt)
            # print(prompt, title, instructions)
            logging.debug("Prompting for %s", prompt[0])

            promptstring = str(prompt[0]).strip().lower()

            if any(x in promptstring for x in ["user", "username"]):
                resp.append(self._user)
            elif "new password" in promptstring:
                # password change, need to wait, signal original thread
                if not title:
                    title = loadstring("IDS_CAP0139")
                result = self._callback(prompt[0], title, "PASSWORD")
                if result:
                    resp.append(result)
                else:
                    raise paramiko.AuthenticationException
            elif any(x in promptstring for x in CONFIG["AUTHSTRINGS"]):
                if self._passcode:
                    resp.append(self._passcode)
                else:
                    if not title:
                        title = loadstring("IDS_CAP0139")
                    result = self._callback(prompt[0], title, "TEXT")
                    if result:
                        resp.append(result)
                    else:
                        raise paramiko.AuthenticationException
            elif "password" in promptstring:
                resp.append(self._password)
            else:
                logging.info("Unknown authentication mechanism: " + prompt)

        return tuple(resp)  # Convert the response list to a tuple and return it

    def open(self, host, port, username=None, password=None, passcode=None, callback=None):
        ''' Open an SSH Connection '''

        # Setup Paramiko logging; this is useful for troubleshooting
        # paramiko.util.log_to_file(os.path.expanduser('~/paramiko.log'), logging.DEBUG)
        self._user = username
        self._password = password
        self._passcode = passcode
        self._callback = callback

        try:
            # Create a socket and connect it to port 22 on the host
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((host, port))

            # Make a Paramiko Transport object using the socket
            self._transport = paramiko.Transport(self._socket)

            # Tell Paramiko that the Transport is going to be used as a client
            self._transport.start_client(timeout=40)

            # do authentication (interactive to handle all cases)
                        # determine what types of authentication are allowed
            try:
                self._transport.auth_none(username)
            except paramiko.BadAuthenticationType as badauthexception:
                allowed_auth_methods = frozenset(badauthexception.allowed_types)
            else:
                # Server allowed auth with no credentials, wtf?
                return False

            # do interactive if we can
            # otherwise fallback to password
            if "keyboard-interactive" in allowed_auth_methods:
                self._transport.auth_interactive_dumb(username, self.inter_handler)
            elif "password" in allowed_auth_methods:
                self._transport.auth_password(username, password, event=None)

            self._transport.set_keepalive(60)

            if self._transport.is_authenticated: # pylint: disable=using-constant-test
                # we've connect, so open a channel
                # get the pty and the invoke a shell to communicate over
                self._channel = self._transport.open_session()
                self._channel.get_pty()
                self._channel.invoke_shell()
            else:
                logging.info("Failed to authenticate without error.")
                return False
        except paramiko.AuthenticationException:
            raise
        except:  # pylint: disable=W0702
            # may need to return more information here
            logging.error("Failed to connect: %s", str(traceback.format_exc().splitlines()))
            return False

        return True

    def write(self, data):
        ''' Sends data to the channel '''
        if not self._transport.is_alive or self._channel.closed:
            self.eof = True
            return
        try:
            self._channel.sendall(data)
        except socket.error:
            self.eof = True
            raise

    def read(self):
        ''' Reads data from the channel '''
        if not self._transport or not self._channel:
            self.eof = True
            return ""
        if not self._transport.is_alive or self._channel.closed:
            self.eof = True
            return ""
        retdata = ""
        with selectors.DefaultSelector() as selector:
            selector.register(self._channel, selectors.EVENT_READ)
            x = selector.select(0.005)
            if x:
                self._channel.settimeout(0)
                # largest packet is 88k
                # which is 65000 write, base64'd
                try:
                    buf = self._channel.recv(4096)
                    # print(buf)
                except EOFError:
                    self.eof = True
                except BrokenPipeError:
                    # unix error when socket goes away
                    self.eof = True
                except socket.timeout:
                    pass
                if buf:
                    retdata = buf.decode("ISO-8859-1").replace('\0', "")
                    self._lastread = time.time()
                if (time.time() - self._lastread) > 1:
                    # test to see if we are still connected
                    try:
                        # need to send a noop
                        self._transport.send_ignore(1)
                    except BrokenPipeError:
                        # unix death
                        self.eof = True
                    self._lastread = time.time()
        return retdata

    def close(self):
        ''' Close up connection '''
        try:
            self._transport.close()
        except:  # pylint: disable=W0702
            # connection may be gone already
            pass
