############################################################################
# Joshua R. Boverhof, David W. Robertson, LBNL
# See LBNLCopyright for copyright notice!
###########################################################################
import unittest
import test_wsdl
import utils

def makeTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(test_wsdl.makeTestSuite("services_by_file"))
    return suite

def main():
    loader = utils.MatchTestLoader(True, None, "makeTestSuite")
    unittest.main(defaultTest="makeTestSuite", testLoader=loader)

if __name__ == "__main__" : main()
    

