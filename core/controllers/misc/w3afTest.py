'''
w3afTest.py.py

Copyright 2006 Andres Riancho

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
import commands
import time
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException


SCRIPT_DIR = 'scripts/'


def getScripts():
    res = []
    withOutAssert = []
    for f in os.listdir(SCRIPT_DIR):
        if f.endswith('.w3af'):
            content = file( SCRIPT_DIR + f ).read()
            if 'assert' in content:
                res.append( SCRIPT_DIR + f )
            else:
                withOutAssert.append( f )
    
    res.sort()
    withOutAssert.sort()
    
    return (res, withOutAssert)


def run_script( scriptName ):
    '''
    Actually run the script.
    '''

    start_time = time.time()

    om.out.information('Running: ' + scriptName + ' ...', newLine=False )
    try:
        output = commands.getoutput('python w3af_console -s ' + scriptName)
    except KeyboardInterrupt, k:
        msg = ('User cancelled the script. Hit Ctrl+C again to cancel all '
           'the test or wait two seconds to continue with the next script.')
        om.out.information( msg )
        try:
            time.sleep(2)
        except:
            om.out.information('User cancelled the WHOLE test.')
            raise k
        else:
            om.out.information('Continuing with the next script..., please wait.')
            return (None, time.time() - start_time)

    end_time = time.time()
    took = end_time - start_time
    
    if took > 9:
        om.out.information(' Run took ' + str(took) + ' seconds!')
    else:
        om.out.information('')
            
    return (output, took)

    
def analyze_result(resultString):
    
    if resultString is None:
        res_code = SKIP
        msg = "Skipped by user.\nKeyboardInterrupt"
    else:
        res_code = SUCC
        msg = ""
    lines = resultString.split('\n') if resultString else []

    for num, line in enumerate(lines):
        if 'Traceback (most recent call last):' in line:
            om.out.error('An unhandled exception was raised during the '
                         'execution of this script!')
            res_code = ERROR
            msg = "\n".join(lines[num:])
            break        
        elif 'Assert **FAILED**' in line:
            om.out.error(line)
            res_code = FAIL
            msg = "Assert failed:\n%s\nAssertionError" % (line)
            break

    return (res_code, msg)
    
def w3afTest():
    '''
    Test all scripts that have an assert call.
    '''
    assert_script_list, scriptsWithoutAssert = getScripts()
    xunit_gen = XunitGen()
    bad_list = []
    ok_list = []
    
    om.out.console('Going to test %s scripts.' % len(assert_script_list))
    
    for assert_script in assert_script_list:
        try:
            result, took = run_script(assert_script)
            res_code, msg = analyze_result(result)

            if res_code == SUCC:
                ok_list.append(assert_script)
                xunit_gen.add_success(assert_script, took)
                
            elif res_code == FAIL:
                bad_list.append(assert_script)
                xunit_gen.add_failure(assert_script, msg, took)
                
            elif res_code in (ERROR, SKIP):
                bad_list.append(assert_script)
                xunit_gen.add_error(assert_script, msg, took, 
                                    skipped=(res_code==SKIP))

        except KeyboardInterrupt:
            break
    
    # Generate xunit file
    xunit_gen.genfile()
    
    om.out.console( '')
    om.out.console( 'Results:')
    om.out.console( '========')
    
    # Summary
    msg = '- ' + str(len(ok_list) + len(bad_list)) + ' / ' 
    msg += str(len(assert_script_list)) + ' scripts have been tested.'
    om.out.console( msg )
    
    # Ok
    om.out.console( '- ' + str(len(ok_list)) + ' OK.')
    
    # Without assert
    scriptsWithoutAssert.sort()
    msg = '- ' + str(len(scriptsWithoutAssert)) + ' scripts don\'t have'
    msg += ' assert statements. This is the list of scripts without assert statements:\n    - '
    msg += '\n    - '.join(scriptsWithoutAssert)
    om.out.console( msg )

    # Failed
    bad_list.sort()
    om.out.console( '- ' + str(len(bad_list)) + ' Failed', newLine=False)
    if not bad_list:
        om.out.console('')
    else:
        om.out.console(':\n    - ' + '\n    - '.join(bad_list))


from xml.sax import saxutils

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
        @param test: Name of the script test file
        @param fail: Failure string
        @param took: Time that took the test to run.
        '''

        self._stats['fail'] += 1
        faillines = fail.split('\n')
        quoteattr = saxutils.quoteattr
        
        self.results.append(
            '<testcase name=%(name)s time="%(took)d">'
            '<failure type=%(errtype)s message="">'
            '<![CDATA[%(fail)s]]></failure>'
            '</testcase>' %
            {'name': quoteattr(test),
             'took': took,
             'errtype': quoteattr(faillines[-1]),
             'fail': '\n'.join(faillines[:-1]),
             })
    
    def add_error(self, test, err, took, skipped=False):
        '''
        @param test: Name of the script test file
        @param err: Error string
        @param took: Time that took the test to run.
        '''
        if skipped:
            self._stats['skip'] += 1
        else:
            self._stats['error'] += 1
        quoteattr = saxutils.quoteattr
        errlinedets = err.split('\n')[-1].split(':', 1)

        self.results.append(
            '<testcase name=%(name)s time="%(took)d">'
            '<error type=%(errtype)s message=%(message)s><![CDATA[%(tb)s]]>'
            '</error></testcase>' %
            {'name': quoteattr(test),
             'took': took,
             'errtype': quoteattr(errlinedets[0]),
             'message': quoteattr(errlinedets[-1]),
             'tb': err,
             })
    
    def add_success(self, test, took):
        '''
        @param test: Name of the script test file
        @param took: Time that took the test to run.
        '''
        self._stats['pass'] += 1
        self.results.append('<testcase name=%s time="%d" />'
                              % (saxutils.quoteattr(test), took))
    
