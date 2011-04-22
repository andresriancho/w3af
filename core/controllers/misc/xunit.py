'''
xunit.py

Copyright 2011 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''
from __future__ import with_statement
import os
from xml.sax import saxutils

import core.controllers.outputManager as om

# Result constants
SUCC = 0
FAIL = 1
ERROR = 3
SKIP = 4

class XunitGen(object):
    '''
    Generate an Xunit XML output file for w3af test scripts. 
    Tools like Hudson will be able to parse the gen xunit files and display 
    useful data to the user.
    '''
    
    outputfile = 'w3aftestscripts.xml'
    sep = os.path.sep
    
    def __init__(self, outputfile=None):
        if outputfile:
            self.outputfile = outputfile
        self._stats = {'error': 0,
                       'skip':0,
                       'pass': 0,
                       'fail': 0}
        self.results = []
        
    
    def genfile(self):
        '''
        Writes the Xunit file.
        '''
        self._stats['total'] = (self._stats['error'] + self._stats['fail']
                               + self._stats['pass'] + self._stats['skip'])
        with open(self.outputfile, 'w') as output:
            output.write(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<testsuite name="w3aftestscripts" tests="%(total)d" '
                'errors="%(error)d" failures="%(fail)d" skip="%(skip)d">'
                % self._stats)
            output.write(''.join(self.results))
            output.write('</testsuite>')
        om.out.information('XML output file was successfuly generated: %s'
                           % self.outputfile)

    def add_failure(self, test, fail, took):
        '''
        @param test: Qualified name for test case. 
            Should have next format:
                {packagename}.{path.to.class.in.module}.{testcase}.
            Examples:
                scripts.script-afd.test_afd
                core.controllers.auto_update.tests.test_autoupd.TesVMgr.testXXX
        @param fail: Failure string
        @param took: Time that took the test to run.
        '''

        self._stats['fail'] += 1
        faillines = fail.split('\n')
        quoteattr = saxutils.quoteattr
        pkg, _, id = test.rpartition('.')
        
        self.results.append(
            '<testcase classname=%(pkg)s name=%(name)s time="%(took)d">'
            '<failure type=%(errtype)s message="">'
            '<![CDATA[%(fail)s]]></failure>'
            '</testcase>' %
            {'name': quoteattr(id),
             'pkg': quoteattr(pkg),
             'took': took,
             'errtype': quoteattr(faillines[-1]),
             'fail': '\n'.join(faillines[:-1]),
             })
    
    def add_error(self, test, err, took, skipped=False):
        '''
        @param test: Qualified name for test case. 
            Should have next format:
                {packagename}.{path.to.class.in.module}.{testcase}.
            Examples:
                scripts.script-afd.test_afd
                core.controllers.auto_update.tests.test_autoupd.TesVMgr.testXXX
        @param err: Error string
        @param took: Time that took the test to run.
        '''
        if skipped:
            self._stats['skip'] += 1
        else:
            self._stats['error'] += 1
        quoteattr = saxutils.quoteattr
        errlinedets = err.split('\n')[-1].split(':', 1)
        pkg, _, id = test.rpartition('.')

        self.results.append(
            '<testcase classname=%(pkg)s name=%(name)s time="%(took)d">'
            '<error type=%(errtype)s message=%(message)s><![CDATA[%(tb)s]]>'
            '</error></testcase>' %
            {'name': quoteattr(id),
             'pkg': quoteattr(pkg),
             'took': took,
             'errtype': quoteattr(errlinedets[0]),
             'message': quoteattr(errlinedets[-1]),
             'tb': err,
             })
    
    def add_success(self, test, took):
        '''
        @param test: Qualified name for test case. 
            Should have next format:
                {packagename}.{path.to.class.in.module}.{testcase}.
            Examples:
                scripts.script-afd.test_afd
                core.controllers.auto_update.tests.test_autoupd.TesVMgr.testXXX
        @param took: Time that took the test to run.
        '''
        self._stats['pass'] += 1
        quoteattr = saxutils.quoteattr
        pkg, _, id = test.rpartition('.')
        self.results.append('<testcase classname=%s name=%s time="%d" />'
                              % (quoteattr(pkg), quoteattr(id), took))
    
