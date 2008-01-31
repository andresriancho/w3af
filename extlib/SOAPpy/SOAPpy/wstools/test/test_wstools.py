#!/usr/bin/env python

############################################################################
# Joshua R. Boverhof, David W. Robertson, LBNL
# See LBNLCopyright for copyright notice!
###########################################################################

import unittest, tarfile, os, ConfigParser
import test_wsdl


SECTION='files'
CONFIG_FILE = 'config.txt'

def extractFiles(section, option):
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)
    archives = config.get(section, option)
    archives = eval(archives)
    for file in archives:
        tar = tarfile.open(file)
        if not os.access(tar.membernames[0], os.R_OK):
            for i in tar.getnames(): 
                tar.extract(i)

def makeTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(test_wsdl.makeTestSuite("services_by_file"))
    return suite

def main():
    extractFiles(SECTION, 'archives')
    unittest.main(defaultTest="makeTestSuite")

if __name__ == "__main__" : main()
    

