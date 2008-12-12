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
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
import time

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
    
    return res, withOutAssert

def run_script( scriptName ):
    '''
    Actually run the script.
    '''

    start_time = time.time()

    om.out.information('Running: ' + scriptName + ' ...', newLine=False )
    try:
        output = commands.getoutput('python w3af_console -s ' + scriptName)
    except KeyboardInterrupt, k:
        output = ''
        msg = 'User cancelled the script. Hit Ctrl+C again to cancel all the test or wait two'
        msg += ' seconds to continue with the next script.'
        om.out.information( msg )
        try:
            time.sleep(2)
        except:
            om.out.information('User cancelled the WHOLE test.')
            raise k
        else:
            om.out.information('Continuing with the next script..., please wait.')
            return output

    end_time = time.time()
    om.out.information(' Run took ' + str(end_time-start_time) + ' seconds.')
            
    return output
    
def analyzeResult( resultString ):
    lines = resultString.split('\n')
    error = False
    for line in lines:
        if 'Assert **FAILED**' in line:
            om.out.error( line )
            error = True
        elif 'Traceback (most recent call last):' in line:
            om.out.error( 'An unhandled exception was raised during the execution of this script!' )
            error = True
    
    if error:
        raise w3afException('Error found in unit test.')
    
def w3afTest():
    '''
    Test all scripts that have an assert call.
    '''
    assertScriptList, scriptsWithoutAssert = getScripts()
    badCount = okCount = 0
    
    om.out.console( 'Going to test '+ str(len(assertScriptList)) + ' scripts.' )
    
    for assertScript in assertScriptList:
        try:
            result = run_script( assertScript )
            analyzeResult( result )
        except KeyboardInterrupt:
            break
        except w3afException:
            badCount += 1
        else:
            okCount += 1
    
    om.out.console( '')
    om.out.console( 'Results:')
    om.out.console( '========')
    om.out.console( '- ' + str(okCount + badCount) + '/ ', newLine=False)
    om.out.console( str(len(assertScriptList)) + ' scripts have been tested.')
    om.out.console( '- ' + str(okCount) + ' OK.')
    om.out.console( '- ' + str(badCount) + ' Failed.')
    om.out.console( '- ' + str(len(scriptsWithoutAssert)) + ' scripts don\'t have', newLine=False)
    om.out.console( ' assert statements. This is the list of scripts without assert statements:')
    scriptsWithoutAssert.sort()
    om.out.console( '- ' + ' , '.join(scriptsWithoutAssert) )
