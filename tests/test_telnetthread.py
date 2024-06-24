'''
Created on Mar 13, 2017

@author: holthjef
'''
import unittest
from components.command import Command  # pylint:disable=unused-import
from connector.configuration import CONFIG
from telnet.telnetthread import TelnetThread, CommDataSet

# pylint: disable=protected-access
class TestTelnetThread(unittest.TestCase):
    ''' Testing telnetthread '''

    def setUp(self):
        ''' setUp '''
        pass

    def tearDown(self):
        ''' tearDown '''
        pass

    def testinit_compoundhost(self):
        ''' test initialization '''
        host = "myhost"
        port = 9876
        server = host + ":" + str(port)
        ssl = False
        user = "myuser"
        password = "mypassword"
        account = "myaccount"
        self.genericinittest(server, host, port, ssl, user, password, account)

    def testinit_ssl(self):
        ''' test initialization '''
        host = "myhost"
        port = 992
        server = host
        ssl = True
        user = "myuser"
        password = "mypassword"
        account = "myaccount"

        oldfreeform = CONFIG["ALLOWFREEFORMLOGIN"]
        CONFIG["ALLOWFREEFORMLOGIN"] = True  # Otherwise ssl parm is ignored
        self.genericinittest(server, host, port, ssl, user, password, account)
        CONFIG["ALLOWFREEFORMLOGIN"] = oldfreeform  # Reset

    def testinit_nonssl(self):
        ''' test initialization '''
        host = "myhost"
        port = 23
        server = host
        ssl = False
        user = "myuser"
        password = "mypassword"
        account = "myaccount"

        oldfreeform = CONFIG["ALLOWFREEFORMLOGIN"]
        CONFIG["ALLOWFREEFORMLOGIN"] = True  # Otherwise ssl parm is ignored
        self.genericinittest(server, host, port, ssl, user, password, account)
        CONFIG["ALLOWFREEFORMLOGIN"] = oldfreeform  # Reset

    def genericinittest(self, server: str, host: str, port: str, ssl: bool,
                        user: str=None, password: str=None,
                        account: str=None):
        ''' Helper function '''
        oldfreeform = CONFIG["ALLOWFREEFORMLOGIN"]
        CONFIG["ALLOWFREEFORMLOGIN"] = True  # Otherwise ssl parm is ignored
        telnetthread = TelnetThread(server, ssl, user, password, account)
        CONFIG["ALLOWFREEFORMLOGIN"] = oldfreeform  # Reset
        self.assertEqual(telnetthread._ssl, ssl)
        self.assertEqual(telnetthread._port, port)
        self.assertEqual(telnetthread._host, host)
        self.assertEqual(telnetthread._user, user)
        self.assertEqual(telnetthread._password, password)
        self.assertEqual(telnetthread._account, account)

        return telnetthread

    def test_processscript(self):
        ''' test _processscript '''
        host = "myhost"
        port = 9876
        server = host + ":" + str(port)
        ssl = False
        user = "myuser"
        password = "mypassword"
        account = "myaccount"

        tnthread = self.genericinittest(server, host, port, ssl, user, password, account)

        connectionopen = True
        tnthread._dataset = CommDataSet()

        # Check for Your VOC is out of date... before it should be allowed
        tnthread._dataset.inputq.clear()
        tnthread._dataset.outputq.clear()
        tnthread._processscript("Your VOC is out of date. Update to current release (Y/N)? Do you feel lucky?",
                                connectionopen)
        self.assertEqual(len(tnthread._dataset.outputq), 0)
        self.assertEqual(len(tnthread._dataset.inputq), 0)

        # Check for name
        tnthread._dataset.inputq.clear()
        tnthread._dataset.outputq.clear()
        tnthread._processscript("Name", connectionopen)
        self.assertEqual(len(tnthread._dataset.outputq), 0)
        self.assertEqual(len(tnthread._dataset.inputq), 1)
        self.assertEqual(tnthread._dataset.inputq[0], user + "\r")

        # Check for password
        tnthread._dataset.inputq.clear()
        tnthread._dataset.outputq.clear()
        tnthread._processscript("password", connectionopen)
        self.assertEqual(len(tnthread._dataset.outputq), 0)
        self.assertEqual(len(tnthread._dataset.inputq), 1)
        self.assertEqual(tnthread._dataset.inputq[0], password + "\r")

        # Check for account
        tnthread._dataset.inputq.clear()
        tnthread._dataset.outputq.clear()
        tnthread._processscript("what account you want?", connectionopen)
        self.assertEqual(len(tnthread._dataset.outputq), 0)
        self.assertEqual(len(tnthread._dataset.inputq), 1)
        self.assertEqual(tnthread._dataset.inputq[0], account + "\r")

        # Check for TERM =
        tnthread._dataset.inputq.clear()
        tnthread._dataset.outputq.clear()
        tnthread._processscript("how about that TERM =, eh?", connectionopen)
        self.assertEqual(len(tnthread._dataset.outputq), 0)
        self.assertEqual(len(tnthread._dataset.inputq), 1)
        self.assertEqual(tnthread._dataset.inputq[0], "\r")

        # Check for UniVerse Command Language
        tnthread._dataset.inputq.clear()
        tnthread._dataset.outputq.clear()
        tnthread._processscript("Look at that UniVerse Command Language go!", connectionopen)
        self.assertEqual(tnthread._osoruv, "uv")
        self.assertEqual(len(tnthread._dataset.outputq), 0)
        self.assertEqual(len(tnthread._dataset.inputq), 0)

        # Check for Your VOC is out of date...
        tnthread._dataset.inputq.clear()
        tnthread._dataset.outputq.clear()
        tnthread._processscript("Your VOC is out of date. Update to current release (Y/N)? Do you feel lucky?",
                                connectionopen)
        self.assertEqual(len(tnthread._dataset.outputq), 0)
        self.assertEqual(len(tnthread._dataset.inputq), 1)
        self.assertEqual(tnthread._dataset.inputq[0], "Y\r")

        # Check for Y>
        tnthread._dataset.inputq.clear()
        tnthread._dataset.outputq.clear()
        tnthread._processscript("Y> 'cuz, prompting", connectionopen)
        self.assertEqual(len(tnthread._dataset.outputq), 0)
        self.assertEqual(len(tnthread._dataset.inputq), 0)

        # Check for > before Teriminal Type check
        tnthread._dataset.inputq.clear()
        tnthread._dataset.outputq.clear()
        tnthread._processscript("TCL, bro>", connectionopen)
        self.assertEqual(len(tnthread._dataset.outputq), 0)
        self.assertEqual(len(tnthread._dataset.inputq), 1)
        self.assertEqual(tnthread._dataset.inputq[0], "ASK.TERM" + chr(13))
        self.assertEqual(tnthread._scriptfinished, False)

        # Check for Terminal Type
        tnthread._dataset.inputq.clear()
        tnthread._dataset.outputq.clear()
        tnthread._processscript("That is some Terminal Type ya got there", connectionopen)
        self.assertEqual(len(tnthread._dataset.outputq), 0)
        self.assertEqual(len(tnthread._dataset.inputq), 0)
        self.assertEqual(tnthread._foundtermtypeprompt, True)

        # Check for TYPE TERMINAL
        tnthread._dataset.inputq.clear()
        tnthread._dataset.outputq.clear()
        tnthread._foundtermtypeprompt = False
        tnthread._processscript("TYPE TERMINAL", connectionopen)
        self.assertEqual(len(tnthread._dataset.outputq), 0)
        self.assertEqual(len(tnthread._dataset.inputq), 0)
        self.assertEqual(tnthread._foundtermtypeprompt, True)

        # Check for > after Terminal Type check
        tnthread._dataset.inputq.clear()
        tnthread._dataset.outputq.clear()
        tnthread._processscript("TCL, bro>", connectionopen)
        self.assertEqual(len(tnthread._dataset.outputq), 2)
        self.assertEqual(len(tnthread._dataset.inputq), 0)
        self.assertEqual(tnthread._scriptfinished, True)

        # self.assertEqual(len(tnthread._dataset.outputq), 0)
        # self.assertEqual(len(tnthread._dataset.inputq), 0)
        self.assertEqual(len(tnthread._dataset.renderq), 0)
        self.assertEqual(len(tnthread._dataset.screenstack), 0)
        self.assertEqual(tnthread._dataset.lasttouch, 0)

    def test_exceptionnourlnotlocal(self):
        ''' test _processscriptexception without external URL but with external error'''
        host = "myhost"
        port = 9876
        server = host + ":" + str(port)
        ssl = False
        user = "myuser"
        password = "mypassword"
        account = "myaccount"

        tnthread = self.genericinittest(server, host, port, ssl, user, password, account)

        msg = "  ".join(("The maximum number of users are already logged on the system.",
                         "Please try again later. (WDERR-SCRIPT-005)"))
        CONFIG["LOGINEXCEPTIONURL"] = ""
        connectionopen = True
        tnthread._dataset = CommDataSet()
        tnthread._processscript("UniVerse user limit has been reached", connectionopen)
        self.assertEqual(len(tnthread._dataset.outputq), 1)
        self.assertEqual(tnthread._dataset.outputq[0]._command["type"], "LOGOUT")
        self.assertEqual(tnthread._dataset.outputq[0]._command["msgtype"], "ERROR")
        self.assertEqual(tnthread._dataset.outputq[0]._command["msg"], msg)

        self.assertEqual(len(tnthread._dataset.inputq), 0)
        self.assertEqual(len(tnthread._dataset.renderq), 0)
        self.assertEqual(len(tnthread._dataset.screenstack), 0)
        self.assertEqual(tnthread._dataset.lasttouch, 0)

    def test_exceptionurlnotlocal(self):
        ''' test _processscriptexception with external URL and external error '''
        host = "myhost"
        port = 9876
        server = host + ":" + str(port)
        ssl = False
        user = "myuser"
        password = "mypassword"
        account = "myaccount"

        tnthread = self.genericinittest(server, host, port, ssl, user, password, account)

        CONFIG["LOGINEXCEPTIONURL"] = "bobserrormessages.com"
        connectionopen = True
        tnthread._dataset = CommDataSet()
        tnthread._processscriptexception("UniVerse user limit has been reached", connectionopen)

        self.assertEqual(len(tnthread._dataset.outputq), 2)
        self.assertEqual(tnthread._dataset.outputq[0]._command["type"], "LOGOUT")
        self.assertEqual(tnthread._dataset.outputq[0]._command["msg"], "Logged out")
        self.assertEqual(tnthread._dataset.outputq[1]._command["type"], "NAVEXT")
        self.assertEqual(tnthread._dataset.outputq[1]._command["exturl"],
                         "http:///bobserrormessages.com?err=WDERR-SCRIPT-005")
        self.assertEqual(len(tnthread._dataset.inputq), 0)
        self.assertEqual(len(tnthread._dataset.renderq), 0)
        self.assertEqual(len(tnthread._dataset.screenstack), 0)
        self.assertEqual(tnthread._dataset.lasttouch, 0)

    def test_exceptionurllocal(self):
        ''' test _processscriptexception with external URL, but local error '''
        host = "myhost"
        port = 9876
        server = host + ":" + str(port)
        ssl = False
        user = "myuser"
        password = "mypassword"
        account = "myaccount"

        tnthread = self.genericinittest(server, host, port, ssl, user, password, account)

        CONFIG["LOGINEXCEPTIONURL"] = "bobserrormessages.com"
        msg = "User ID or Password failed. (WDERR-SCRIPT-002)"
        connectionopen = True
        tnthread._dataset = CommDataSet()
        tnthread._processscriptexception("ncorrect", connectionopen)
        self.assertEqual(len(tnthread._dataset.outputq), 1)
        self.assertEqual(tnthread._dataset.outputq[0]._command["type"], "LOGOUT")
        self.assertEqual(tnthread._dataset.outputq[0]._command["msg"], msg)
        self.assertEqual(tnthread._dataset.outputq[0]._command["msgtype"], "ERROR")

        self.assertEqual(len(tnthread._dataset.inputq), 0)
        self.assertEqual(len(tnthread._dataset.renderq), 0)
        self.assertEqual(len(tnthread._dataset.screenstack), 0)
        self.assertEqual(tnthread._dataset.lasttouch, 0)


    def test_scriptend(self):
        ''' test _checkforscriptend '''
        host = "myhost"
        port = 9876
        server = host + ":" + str(port)
        ssl = False
        user = "myuser"
        password = "mypassword"
        account = "myaccount"

        tnthread = self.genericinittest(server, host, port, ssl, user, password, account)
        tnthread._dataset = CommDataSet()
        promptingpackets = ["WPD", "WPN", "WPP"]

        # Match prompting packets
        for pkt in promptingpackets:
            tnthread._scriptfinished = False
            tnthread._checkforscriptend("Whenever life gets you down," +
                                        chr(2) + pkt + "Mrs. Brown")
            self.assertEqual(tnthread._scriptfinished, True)

        # Reset outputq
        tnthread._dataset.outputq.clear()

        # No match, because doesn't have a prompting packet
        tnthread._scriptfinished = False
        tnthread._checkforscriptend(
            "Just remember that you're standing on a planet that's evolving") 
        self.assertEqual(tnthread._scriptfinished, False)

        self.assertEqual(len(tnthread._dataset.outputq), 0)
        self.assertEqual(len(tnthread._dataset.inputq), 0)
        self.assertEqual(len(tnthread._dataset.renderq), 0)
        self.assertEqual(len(tnthread._dataset.screenstack), 0)
        self.assertEqual(tnthread._dataset.lasttouch, 0)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
