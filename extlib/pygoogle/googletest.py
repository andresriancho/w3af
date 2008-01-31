"""Unit test for google.py"""

__author__ = "Mark Pilgrim (f8dy@diveintomark.org)"
__version__ = "$Revision: 1.4 $"
__date__ = "$Date: 2004/02/06 21:00:53 $"
__copyright__ = "Copyright (c) 2002 Mark Pilgrim"
__license__ = "Python"

import google
import unittest
import sys, os
import GoogleSOAPFacade
from StringIO import StringIO

class BaseClass(unittest.TestCase):
    q = "python unit testing"
    url = "http://www.python.org/"
    phrase = "ptyhon"
    searchparams = {"func":"doGoogleSearch"}
    luckyparams = {}
    luckyparams.update(searchparams)
    luckyparams.update({"feelingLucky":1})
    metaparams = {}
    metaparams.update(searchparams)
    metaparams.update({"showMeta":1})
    reverseparams = {}
    reverseparams.update(searchparams)
    reverseparams.update({"reverseOrder":1})
    cacheparams = {"func":"doGetCachedPage"}
    spellingparams = {"func":"doSpellingSuggestion"}
    envkey = "GOOGLE_LICENSE_KEY"
    badkey = "a"
    
class Redirector(BaseClass):
    def setUp(self):
        self.savestdout = sys.stdout
        self.output = StringIO()
        sys.stdout = self.output

    def tearDown(self):
        sys.stdout = self.savestdout

class CommandLineTest(Redirector):
    def lastOutput(self):
        self.output.seek(0)
        rc = self.output.read()
        self.output.seek(0)
        return rc

    def testVersion(self):
        """-v should print version"""
        google.main(["-v"])
        commandLineAnswer = self.lastOutput()
        google._version()
        self.assertEqual(commandLineAnswer, self.lastOutput())
    
    def testVersionLong(self):
        """--version should print version"""
        google.main(["--version"])
        commandLineAnswer = self.lastOutput()
        google._version()
        self.assertEqual(commandLineAnswer, self.lastOutput())
    
    def testHelp(self):
        """-h should print usage"""
        google.main(["-h"])
        commandLineAnswer = self.lastOutput()
        google._usage()
        self.assertEqual(commandLineAnswer, self.lastOutput())
    
    def testHelpLong(self):
        """--help should print usage"""
        google.main(["--help"])
        commandLineAnswer = self.lastOutput()
        google._usage()
        self.assertEqual(commandLineAnswer, self.lastOutput())
    
    def testSearch(self):
        """-s should search"""
        google.main(["-s %s" % self.q])
        commandLineAnswer = self.lastOutput()
        google._output(google.doGoogleSearch(self.q), self.searchparams)
        self.assertEqual(commandLineAnswer, self.lastOutput())

    def testSearchLong(self):
        """--search should search"""
        google.main(["--search", self.q])
        commandLineAnswer = self.lastOutput()
        google._output(google.doGoogleSearch(self.q), self.searchparams)
        self.assertEqual(commandLineAnswer, self.lastOutput())

    def testSearchDefault(self):
        """no options + search phrase should search"""
        google.main([self.q])
        commandLineAnswer = self.lastOutput()
        google._output(google.doGoogleSearch(self.q), self.searchparams)
        self.assertEqual(commandLineAnswer, self.lastOutput())

    def testNoOptions(self):
        """no options at all should print usage"""
        google.main([])
        commandLineAnswer = self.lastOutput()
        google._usage()
        self.assertEqual(commandLineAnswer, self.lastOutput())

    def testCache(self):
        """-c should retrieve cache"""
        google.main(["-c", self.url])
        commandLineAnswer = self.lastOutput()
        google._output(google.doGetCachedPage(self.url), self.cacheparams)
        self.assertEqual(commandLineAnswer, self.lastOutput())

    def testCacheLong(self):
        """--cache should retrieve cache"""
        google.main(["--cache", self.url])
        commandLineAnswer = self.lastOutput()
        google._output(google.doGetCachedPage(self.url), self.cacheparams)
        self.assertEqual(commandLineAnswer, self.lastOutput())

    def testSpelling(self):
        """-p should check spelling"""
        google.main(["-p", self.phrase])
        commandLineAnswer = self.lastOutput()
        google._output(google.doSpellingSuggestion(self.phrase), self.spellingparams)
        self.assertEqual(commandLineAnswer, self.lastOutput())

    def testSpellingLong(self):
        """--spelling should check spelling"""
        google.main(["--spelling", self.phrase])
        commandLineAnswer = self.lastOutput()
        google._output(google.doSpellingSuggestion(self.phrase), self.spellingparams)
        self.assertEqual(commandLineAnswer, self.lastOutput())

    def testLucky(self):
        """-l should return only first result"""
        google.main(["-l", "-s", self.q])
        commandLineAnswer = self.lastOutput()
        google._output(google.doGoogleSearch(self.q), self.luckyparams)
        self.assertEqual(commandLineAnswer, self.lastOutput())

    def testLucky1(self):
        """-1 should return only first result"""
        google.main(["-1", "-s", self.q])
        commandLineAnswer = self.lastOutput()
        google._output(google.doGoogleSearch(self.q), self.luckyparams)
        self.assertEqual(commandLineAnswer, self.lastOutput())
    
    def testLuckyLong(self):
        """--lucky should return only first result"""
        google.main(["--lucky", "-s", self.q])
        commandLineAnswer = self.lastOutput()
        google._output(google.doGoogleSearch(self.q), self.luckyparams)
        self.assertEqual(commandLineAnswer, self.lastOutput())

    def testMeta(self):
        """-m should return meta information"""
        google.main(["-m", "-s", self.q])
        commandLineAnswer = self.lastOutput()
        commandLineAnswer = commandLineAnswer[:commandLineAnswer.index('searchTime')]
        google._output(google.doGoogleSearch(self.q), self.metaparams)
        realAnswer = self.lastOutput()
        realAnswer = realAnswer[:realAnswer.index('searchTime')]
        self.assertEqual(commandLineAnswer, realAnswer)
    
    def testMetaLong(self):
        """--meta should return meta information"""
        google.main(["--meta", "-s", self.q])
        commandLineAnswer = self.lastOutput()
        commandLineAnswer = commandLineAnswer[:commandLineAnswer.index('searchTime')]
        google._output(google.doGoogleSearch(self.q), self.metaparams)
        realAnswer = self.lastOutput()
        realAnswer = realAnswer[:realAnswer.index('searchTime')]
        self.assertEqual(commandLineAnswer, realAnswer)

    def testReverse(self):
        """-r should reverse results"""
        google.main(["-r", "-s", self.q])
        commandLineAnswer = self.lastOutput()
        google._output(google.doGoogleSearch(self.q), self.reverseparams)
        self.assertEqual(commandLineAnswer, self.lastOutput())
    
    def testReverseLong(self):
        """--reverse should reverse results"""
        google.main(["--reverse", "-s", self.q])
        commandLineAnswer = self.lastOutput()
        google._output(google.doGoogleSearch(self.q), self.reverseparams)
        self.assertEqual(commandLineAnswer, self.lastOutput())

class LicenseKeyTest(Redirector):
    licensefile = "googlekey.txt"
    licensebackup = "googlekey.txt.bak"
    
    def safeRename(self, dirname, old, new):
        if dirname:
            old = os.path.join(dirname, old)
            new = os.path.join(dirname, new)
        try:
            os.rename(old, new)
        except OSError:
            pass
        
    def safeDelete(self, dirname, filename):
        if dirname:
            filename = os.path.join(dirname, filename)
        try:
            os.remove(filename)
        except OSError:
            pass
    
    def createfile(self, dirname, filename, content):
        if dirname:
            filename = os.path.join(dirname, filename)
        fsock = open(filename, "w")
        fsock.write(content)
        fsock.close()
        
    def rememberKeys(self):
        self.moduleLicenseKey = google.LICENSE_KEY
        self.envLicenseKey = os.environ.get(self.envkey, None)
        self.safeRename(os.environ["HOME"], self.licensefile, self.licensebackup)
        self.safeRename("", self.licensefile, self.licensebackup)
        self.safeRename(google._getScriptDir(), self.licensefile, self.licensebackup)

    def restoreKeys(self):
        google.LICENSE_KEY = self.moduleLicenseKey
        if self.envLicenseKey:
            os.environ[self.envkey] = self.envLicenseKey
        self.safeDelete(os.environ["HOME"], self.licensefile)
        self.safeRename(os.environ["HOME"], self.licensebackup, self.licensefile)
        self.safeDelete("", self.licensefile)
        self.safeRename("", self.licensebackup, self.licensefile)
        self.safeDelete(google._getScriptDir(), self.licensefile)
        self.safeRename(google._getScriptDir(), self.licensebackup, self.licensefile)

    def clearKeys(self):
        google.setLicense(None)
        if os.environ.get(self.envkey):
            del os.environ[self.envkey]
    
    def setUp(self):
        Redirector.setUp(self)
        self.rememberKeys()
        self.clearKeys()
        
    def tearDown(self):
        Redirector.tearDown(self)
        self.clearKeys()
        self.restoreKeys()

    def testNoKey(self):
        """having no license key should raise google.NoLicenseKey"""
        self.assertRaises(google.NoLicenseKey, google.doGoogleSearch, q=self.q)
        
    def testPassInvalidKey(self):
        """passing invalid license key should fail with faultType"""
        
        self.assertRaises(GoogleSOAPFacade.faultType, google.doGoogleSearch, q=self.q, license_key=self.badkey)
            
    def testSetInvalidKey(self):
        """setting invalid module-level license key should fail with faultType"""
        google.setLicense(self.badkey)
        
        self.assertRaises(GoogleSOAPFacade.faultType, google.doGoogleSearch, q=self.q)
    
    def testEnvInvalidKey(self):
        """invalid environment variable license key should fail with faultType"""
        os.environ[self.envkey] = self.badkey
        
        self.assertRaises(GoogleSOAPFacade.faultType, google.doGoogleSearch, q=self.q)
    
    def testHomeDirKey(self):
        """invalid license key in home directory should fail with faultType"""
        self.createfile(os.environ["HOME"], self.licensefile, self.badkey)
        
        self.assertRaises(GoogleSOAPFacade.faultType, google.doGoogleSearch, q=self.q)

    def testCurDirKey(self):
        """invalid license key in current directory should fail with faultType"""
        self.createfile("", self.licensefile, self.badkey)
        
        self.assertRaises(GoogleSOAPFacade.faultType, google.doGoogleSearch, q=self.q)

    def testScriptDirKey(self):
        """invalid license key in script directory should fail with faultType"""
        self.createfile(google._getScriptDir(), self.licensefile, self.badkey)
        
        self.assertRaises(GoogleSOAPFacade.faultType, google.doGoogleSearch, q=self.q)

if __name__ == "__main__":
    unittest.main()
