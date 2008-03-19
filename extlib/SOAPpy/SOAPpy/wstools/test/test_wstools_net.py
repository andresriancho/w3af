#!/usr/bin/env python

############################################################################
# Joshua R. Boverhof, David W. Robertson, LBNL
# See LBNLCopyright for copyright notice!
###########################################################################
import unittest
import test_wsdl

def makeTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(test_wsdl.makeTestSuite("services_by_http"))
    return suite

def main():
    unittest.main(defaultTest="makeTestSuite")

if __name__ == "__main__" : main()
    

