'''
Created on Jan 24, 2017

@author: cartiaar
'''
import unittest
from connector import utility


class TestUtility(unittest.TestCase):
    ''' Testing Utility '''

    def testextractfromdelimiter(self):
        self.assertEqual(utility.extractfromdelimiter("Test 1|Test 2|Test 3", 2, "|"), "Test 2")
        self.assertEqual(utility.extractfromdelimiter("Test 1|Test 2|Test 3", 4, "|"), "")
        self.assertEqual(utility.extractfromdelimiter("Test 1|Test 2|Test 3\\Test 4|Test 5|Test 6", 2, "\\"), "Test 4|Test 5|Test 6")

if __name__ == "__main__":
    unittest.main()
