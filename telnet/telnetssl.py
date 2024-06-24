'''
Created on Sep 16, 2016
Extends Telnet package to support SSL
@author: bouchcla
'''
import logging
import ssl
from ssl import Purpose
import socket
import selectors
from telnetlib import Telnet
import telnetlib
import time


class TelnetSSL(Telnet):
    ''' Telnet with support for SSL '''

    def __init__(self, usessl: bool = True):
        ''' Constructor '''
        self._usessl = usessl
        if self._usessl:
            self._sslcontext = ssl.create_default_context(purpose=Purpose.CLIENT_AUTH)
            self._sslcontext.check_hostname = False
            self._sslcontext.verify_mode = ssl.CERT_NONE
            self._sslcontext.set_ciphers('HIGH:!DH:!aNULL')
        self._lastread = time.time()
        self._openhostpacket = False
        super().__init__()

    def open(self, host, port=0, timeout=None):
        ''' Ovewrite open to wrap socket in SSL '''

        super().open(host, port, timeout)

        if self._usessl:
            sock = super().get_socket()
            self.sock = self._sslcontext.wrap_socket(sock, server_hostname=host)

        # self.set_debuglevel(100)
        super().set_option_negotiation_callback(negcallback)

        if self._usessl:
            logging.debug("Cipher Chosen:" + str(self.sock.cipher())
                          )  # pylint: disable=no-member

    def read(self):
        ''' do a telnet read with a proper timeout '''

        with selectors.DefaultSelector() as selector:
            selector.register(self, selectors.EVENT_READ)
            x = selector.select(0.005)
            if x:
                self.sock.settimeout(0)
                while not self.eof and len(self.cookedq) < 5000:
                    buf = b''
                    try:
                        buf = self.sock.recv(4096)
                        # print(buf)
                    except EOFError:
                        self.eof = True
                    except BrokenPipeError:
                        # unix error when socket goes away
                        self.eof = True
                    except ssl.SSLWantReadError:
                        # windows ssl error when socket goes away
                        pass
                    except socket.timeout:
                        pass
                    except ssl.SSLError:
                        pass
                    while buf:
                        if self._openhostpacket:
                            # Look for the end of an open packet
                            packetend = buf.find(bytes([3]))
                            if packetend > -1:
                                # Found the end, put the rest of the packet in cooked,
                                # then continue processing
                                self._openhostpacket = False
                                self.cookedq = self.cookedq + buf[:packetend + 1]
                                buf = buf[packetend + 1:]
                            else:
                                # All packet data, place on cooked
                                self.cookedq = self.cookedq + buf
                                break
                        else:
                            # Look for the start of a packet
                            packetstart = buf.find(bytes([2]))
                            if packetstart > -1:
                                # Found start of packet, process preceeding data, if any, as raw
                                # then continue processing
                                self._openhostpacket = True
                                beforepacket = buf[:packetstart]
                                buf = buf[packetstart:]
                                if beforepacket:
                                    self.rawq = beforepacket
                                    self.process_rawq()
                            else:
                                # No packets, process as raw
                                self.rawq = buf
                                self.process_rawq()
                                break
                        self._lastread = time.time()
                    if (time.time() - self._lastread) > 1:
                        # test to see if we are still connected
                        try:
                            self.sock.sendall(telnetlib.IAC + telnetlib.NOP)
                        except BrokenPipeError:
                            # unix death
                            self.eof = True
                        self._lastread = time.time()
                    if not buf or self.eof:
                        break
        # return as a string
        return self.read_very_lazy().decode("ISO-8859-1")


def negcallback(sock, command, option):
    ''' handle negotiations '''
    # print("negotiation callback!", command, option)
    if option in [telnetlib.ECHO, telnetlib.SGA]:
        if command in [telnetlib.DO]:
            sock.sendall(telnetlib.IAC + telnetlib.WILL + option)
        elif command in [telnetlib.DONT]:
            sock.sendall(telnetlib.IAC + telnetlib.WONT + option)
        elif command in [telnetlib.WILL]:
            sock.sendall(telnetlib.IAC + telnetlib.DO + option)
        elif command in [telnetlib.WONT]:
            sock.sendall(telnetlib.IAC + telnetlib.DONT + option)
    else:
        if command in [telnetlib.DO, telnetlib.DONT]:
            sock.sendall(telnetlib.IAC + telnetlib.WONT + option)
        elif command in [telnetlib.WILL, telnetlib.WONT]:
            sock.sendall(telnetlib.IAC + telnetlib.DONT + option)
