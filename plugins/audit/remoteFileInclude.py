'''
remoteFileInclude.py

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


from core.data.fuzzer.fuzzer import createMutants, createRandAlNum
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
import core.data.kb.knowledgeBase as kb
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException
import os, time
from core.controllers.daemons.webserver import webserver
import core.data.kb.vuln as vuln
import core.data.constants.w3afPorts as w3afPorts
import core.data.constants.severity as severity

class remoteFileInclude(baseAuditPlugin):
    '''
    Find remote file inclusion vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        self._rfiUrl = ''
        self._rfiResult = ''
        self._run = True
        self._listenPort = w3afPorts.REMOTEFILEINCLUDE
        self._listenAddress = ''
        self._wS = None
        self._usew3afSite = True
        
    def _fuzzRequests(self, freq ):
        '''
        Tests an URL for remote file inclusion vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        if self._run:
            om.out.debug( 'remoteFileInclude plugin is testing: ' + freq.getURL() )
            vulnerable = []
            if self._listenAddress == '':
                self._run = False
                raise w3afException('remoteFileInclude plugin has to be correctly configured to use.')
            else:
                # Everything is ok ! , go on with the rfi tests.
                if not self._usew3afSite:
                    om.out.information('w3af is running a webserver to include remote files on the server.')
                    self._startServer()             
                
                self._check( freq )
                
                if not self._usew3afSite:
                    self._stopServer()
                # Wait for threads to finish
                self._tm.join( self )
                    
    def _getRfiUrl( self ):
        '''
        With setOptions the user entered a URL that is the one to be included.
        This method returns that URL.
        
        @return: A string, see above.
        '''
        return self._rfiUrl
        
    def _getRfiResult( self ):
        '''
        With setOptions the user entered the expected result of the inclusion.
        For example, at RfiUrl the user entered :
        http://foo/toBeIncluded.txt
        With the following contents :
        $a = 'mfsa09';
        $b = 'a059mu2';
        echo $a . $b;
        
        The expected result for the remote file inclusion would be the following string:
        mfsa09a059mu2
        
        This method returns that expected result.
        
        @return: A string, see above.
        '''
        return self._rfiResult

    def _check( self, freq ):
        '''
        Checks a fuzzableRequest for remote file inclusion bugs.
        
        @return: None
        '''
        rfiUrlList = [ self._getRfiUrl() ]
        mutants = createMutants( freq, rfiUrlList )
        
        for mutant in mutants:
            if self._hasNoBug( 'remoteFileInclude','remoteFileInclude',mutant.getURL() , mutant.getVar() ):
                # Only spawn a thread if the mutant has a modified variable
                # that has no reported bugs in the kb
                targs = (mutant,)
                self._tm.startFunction( target=self._sendMutant, args=targs , ownerObj=self )
                
    def _analyzeResult( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method.
        '''
        # Remember that httpResponse objects have a faster "__in__" than
        # the one in strings; so string in response.getBody() is slower than
        # string in response        
        if self._getRfiResult() in response:
            v = vuln.vuln( mutant )
            v.setId( response.id )
            v.setSeverity(severity.HIGH)
            v.setName( 'Remote file inclusion vulnerability' )
            v.setDesc( 'Remote file inclusion was found at: ' + mutant.foundAt() )
            kb.kb.append( self, 'remoteFileInclude', v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'remoteFileInclude', 'remoteFileInclude' ), 'VAR' )

    def _startServer(self):
        '''
        Starts a webserver for including files. 
        '''
        # First, generate the php file to be included.
        rand1 = createRandAlNum( 9 )
        rand2 = createRandAlNum( 9 )
        filename = createRandAlNum()
        phpStr = '<? \n echo "'
        phpStr += rand1 + '";\n'
        phpStr += ' echo "'
        phpStr += rand2 + '";\n'
        phpStr += ' ?>'
        
        # Write the php to the webroot
        f = open( os.path.join('webroot' + os.path.sep, filename ) , 'w')
        f.write( phpStr )
        f.close()
        
        # Define the required parameters
        self._rfiUrl = 'http://' + self._listenAddress +':' + str(self._listenPort) +'/' + filename
        self._rfiResult = rand1 + rand2
        
        self._wS = webserver( self._listenAddress, self._listenPort , 'webroot' + os.path.sep)
        self._wS.start2()
        time.sleep( 0.2 )
        
    def _stopServer( self ):

        if self._wS != None:
            self._wS.stop()
            # Remove the file
            filename = self._rfiUrl[self._rfiUrl.rfind(os.path.sep)+1:]
            os.remove( os.path.join('webroot' + os.path.sep, filename ) )
            self._wS = None

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Remote URL to include when testing for remote file inclusion.'
        o1 = option('rfiUrl', self._rfiUrl, d1, 'string')
        
        d2 = 'Expected result of inclusion'
        h2 = 'For example, at RfiUrl the user entered :\
          http://foo/toBeIncluded.txt\
          With the following content :\
          \
          $a = \'mfsa09\';\
          $b = \'a059mu2\';\
          echo $a . $b;\
          \
         The rfiResult for the remote file inclusion would be the following string:\
         mfsa09a059mu2'
        o2 = option('rfiResult', self._rfiResult, d2, 'string', help=h2)
        
        d3 = 'IP address that the webserver will use to receive requests'
        h3 = 'When the two previous settings are left unconfigured, w3af runs a webserver\
          to serve the files to the target web app when doing remote file inclusions. This \
          setting configures where the webserver is going to listen.'
        o3 = option('listenAddress', self._listenAddress, d3, 'string', help=h3)

        d4 = 'Port that the webserver will use to receive requests'
        o4 = option('listenPort', self._listenPort, d4, 'integer')

        d5 = 'Use w3af site to test remote file inclusion. If set to True this will override all other options.'
        o5 = option('usew3afSite', self._usew3afSite, d5, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        ol.add(o5)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._listenAddress = optionsMap['listenAddress'].getValue()
        self._listenPort = optionsMap['listenPort'].getValue()
        
        if optionsMap['usew3afSite'].getValue():
            self._usew3afSite = True
            self._rfiUrl = 'http://w3af.sourceforge.net/w3af/remoteFileInclude.html'
            self._rfiResult = 'w3af is goood!'
            self._listenPort = 'notUsed'
            self._listenAddress = 'notUsed'
                
        if self._listenAddress == '':
            raise w3afException('remoteFileInclude plugin has to be correctly configured to use.')

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin will find remote file inclusion vulnerabilities.
        
        Five configurable parameters exist:
            - rfiUrl
            - rfiResult
            - listenAddress
            - listenPort
            - usew3afSite
        
        This plugin will send the value of "rfiUrl" to each injctable parameter, and search for "rfiResult" in the response.
        There are two ways of running this plugin, one is the most common one, by using the w3af site ( w3af.sf.net ) as
        the place from where the web application will fetch the remote file. The other way to test for inclusion is to run a 
        webserver on the machine that is sending the tests, this is configured using the "listenAddress" and "listenPort" 
        parameters.
        
        Configuring True in "usew3afSite" will automatically configure all the other variables.
        '''
