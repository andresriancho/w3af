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

import os
import commands
import time
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from .xunit import XunitGen, ERROR, SKIP, SUCC, FAIL


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
        output = commands.getoutput('python w3af_console -n -s ' + scriptName)
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
            # Get qualified name for test case
            sep = os.path.sep
            test_script = (assert_script.split(sep)[-1]).replace('.w3af', '')
            test_qname = '.'.join([SCRIPT_DIR[:-1].replace(sep, '.'), test_script,
                                   'test_' + test_script.split('-')[-1]])

            if res_code == SUCC:
                ok_list.append(assert_script)
                xunit_gen.add_success(test_qname, took)
                
            elif res_code == FAIL:
                bad_list.append(assert_script)
                xunit_gen.add_failure(test_qname, msg, took)
                
            elif res_code in (ERROR, SKIP):
                bad_list.append(assert_script)
                xunit_gen.add_error(test_qname, msg, took, 
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
