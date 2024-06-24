'''
Created on Oct 13, 2016

@author: bouchcla
'''
from abc import ABCMeta, abstractmethod

from connector.wingempacket import WinGemPacket


class BaseWDObject(metaclass=ABCMeta):
    '''
    Generic, abstract packet
    Cannot use directly, but useful to inherit from
    '''

    def __init__(self, packettype: str):
        ''' Constructor '''
        # Defaults
        self._type = packettype
        self._cacheable = False
        self._complete = False

    def gettype(self):
        '''
        return type of packet
        (WG packet identifier)
        '''
        return self._type

    def getid(self):
        ''' return the id if we have one '''
        return ""

    def iscacheable(self):
        '''
        is object cacheable
        currently unused
        '''
        return self._cacheable

    def iscomplete(self):
        ''' determine if object is complete '''
        return self._complete

    @abstractmethod
    def addpacket(self, packet: WinGemPacket, **extras):
        '''
        Add packet to WebDirect Object
        returns a tuple
        ( processed, hostdata, returnobj )
        processed is true if packet consumed, false otherwise
        hostdata is any data that needs to be returned through
            the telnet channel - None if no data is to be returned
        returnobj is an item to be returned to the WebDirect Client
        This is an abstract method and must be implemented by the
            actual webdirect object
        '''
