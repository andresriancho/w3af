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
import shlex
import time

from subprocess import Popen, PIPE, STDOUT

import core.controllers.outputManager as om

from core.controllers.misc.xunit import XunitGen

SCRIPT_DIR = 'scripts/'
ERROR, SKIP, SUCC, FAIL = 'ERROR SKIP OK FAIL'.split()


def getScripts():
    res = []
    withOutAssert = []
    for f in os.listdir(SCRIPT_DIR):
        if f.endswith('.w3af'):
            content = file(SCRIPT_DIR + f).read()
            if 'assert' in content:
                res.append(SCRIPT_DIR + f)
            else:
                withOutAssert.append(f)
    
    res.sort()
    withOutAssert.sort()
    
    return (res, withOutAssert)

def run_script(scriptName):
    '''
    Actually run the script.
    '''
    now = lambda: time.time()
    start_time = now()
    try:
        args = shlex.split('python w3af_console -n -s %s' % scriptName)
        output = Popen(args, stdout=PIPE, stderr=STDOUT).communicate()[0]
    except KeyboardInterrupt, k:
        msg = ('User cancelled the script. Hit Ctrl+C again to cancel all '
           'the test or wait two seconds to continue with the next script.')
        om.out.information(msg)
        try:
            time.sleep(2)
        except:
            om.out.information('User cancelled the WHOLE test.')
            raise k
        else:
            om.out.information(
                        'Continuing with the next script... please wait.')
            return (None, now() - start_time)

    took = now() - start_time
    return (output, took)
    
def analyze_result(res_str):
    
    if res_str is None:
        res_code = SKIP
        msg = "Skipped by user: KeyboardInterrupt"
    else:
        res_code = SUCC
        msg = ""
    
    lines = res_str.split('\n') if res_str else []
    for num, line in enumerate(lines):
        if 'Traceback (most recent call last):' in line:
            res_code = ERROR
            msg = "\n".join(lines[num:])
            break        
        elif 'Assert **FAILED**' in line:
            res_code = FAIL
            msg = "Assert failed:\n%s\nAssertionError" % (line)
            break

    return (res_code, msg)
    
def w3afTest():
    '''
    Test all scripts that have an assert call.
    '''
    with_assert, without_assert = getScripts()
    xunit_gen = XunitGen()
    bad_list = []
    ok_list = []
    
    om.out.console('Going to test %s scripts.' % len(with_assert))
    
    for script in with_assert:
        try:
            sep = os.path.sep
            short_script = script.split(sep)[-1].replace('.w3af', '')
            om.out.information(short_script + '...', newLine=False)
            result, took = run_script(script)
            res_code, msg = analyze_result(result)
            
            # Notify the user
            output_msg = ' %s' % res_code
            if res_code == SUCC and took > 10:
                output_msg += ' (Took %.2f seconds!)' % took
            om.out.information(output_msg)
            
            # Get qualified name for test case
            test_qname = '.'.join([
                               SCRIPT_DIR[:-1].replace(sep, '.'),
                               short_script,
                               'test_' + short_script.split('-')[-1]
                               ])

            if res_code == SUCC:
                ok_list.append(script)
                xunit_gen.add_success(test_qname, took)
                
            elif res_code == FAIL:
                bad_list.append(script)
                xunit_gen.add_failure(test_qname, msg, took)
                
            elif res_code in (ERROR, SKIP):
                bad_list.append(script)
                xunit_gen.add_error(test_qname, msg, took,
                                    skipped=(res_code==SKIP))

        except KeyboardInterrupt:
            break
    
    # Generate xunit file
    xunit_gen.genfile()
    
    om.out.console('')
    om.out.console('Results:')
    om.out.console('========')
    
    # Summary
    msg = '- ' + str(len(ok_list) + len(bad_list)) + ' / ' 
    msg += str(len(with_assert)) + ' scripts have been tested.'
    om.out.console(msg)
    
    # Ok
    om.out.console('- ' + str(len(ok_list)) + ' OK.')
    
    # Without assert
    without_assert.sort()
    msg = '- ' + str(len(without_assert)) + ' scripts don\'t have'
    msg += ' assert statements. This is the list of scripts without assert statements:\n    - '
    msg += '\n    - '.join(without_assert)   
    
    om.out.console(msg)

    # Failed
    bad_list.sort()
    om.out.console('- ' + str(len(bad_list)) + ' Failed', newLine=False)
    if not bad_list:
        om.out.console('')
    else:
        om.out.console(':\n    - ' + '\n    - '.join(bad_list))