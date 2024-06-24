'''
Created on Oct 17, 2016

@author: bouchcla
'''


class TCLData(object):
    ''' Simple representation of TCL data '''

    def __init__(self, tcldata: str = ""):
        ''' Constructor '''
        # we should call the internal add in case we want to add some logic
        self.data = ""
        if tcldata:
            self.adddata(tcldata)

    def gettype(self):
        ''' return type of packet '''
        return "TCL"

    def getdata(self):
        ''' Return TCL data '''
        return self.data

    def adddata(self, data:str ):
        ''' Add more data to TCL string '''
        self.data += data

    def hasdata(self):
        ''' returns true if we have data '''
        return len(self.data) > 0
