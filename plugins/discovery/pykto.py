'''
pykto.py

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

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.parsers.urlParser as urlParser
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afException
from core.controllers.w3afException import w3afRunOnce
import os.path
import re
from core.data.fuzzer.fuzzer import *
import core.data.constants.severity as severity

class pykto(baseDiscoveryPlugin):
    '''
    A nikto port to python. 
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._exec = True
        self._cgiDirs = ['/cgi-bin/']
        self._adminDirs = ['/admin/','/adm/'] 
        self._users = ['adm','bin','daemon','ftp','guest','listen','lp',
        'mysql','noaccess','nobody','nobody4','nuucp','operator',
        'root','smmsp','smtp','sshd','sys','test','unknown']                  
        self._nuke = ['/','/postnuke/','/postnuke/html/','/modules/','/phpBB/','/forum/']

        self._dbFile = 'plugins' + os.path.sep + 'discovery' + os.path.sep + 'pykto' + os.path.sep + 'scan_database.db'
        self._mutateTests = False
        self._genericScan = False
        self._updateScandb = False
        self._alreadyVisited = []
        self._lastCodes = []
        self._firstTime = True
        self._source = ''
        
    def discover(self, fuzzableRequest ):
        '''
        Runs pykto to the site.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        self._fuzzableRequests = []
        
        if not self._exec:
            # dont run anymore
            raise w3afRunOnce()
            
        else:
            # run!

            if self._updateScandb:
                self._updateDb()
            
            self.is404 = kb.kb.getData( 'error404page', '404' )
            
            # Give me the base URL
            if not self._mutateTests:
                url = urlParser.baseUrl( fuzzableRequest.getURL() )
                # This plugin returns always the same value if called without mutateTests , so 
                # running it more times is useless
                self._exec = False
                self.__run( url )
            else:
                # Tests are to be mutated
                url = urlParser.getDomainPath( fuzzableRequest.getURL() )
                if url not in self._alreadyVisited:
                    # Save the directories I already have tested
                    self._alreadyVisited.append( url )
                    self.__run( url )

        return self._fuzzableRequests
                
    def __run( self, url ):
        '''
        Really run the plugin.
        '''
        # read the nikto database.
        try:
            f = open(self._dbFile, "r")
        except:
            raise w3afException('Could not open nikto scan database.')
        else:
            # pykto that site !
            self._pykto( url , f )
            f.close()
        
    def _updateDb( self ):
        '''
        This method updates the scandatabase from cirt.net .
        '''
        # Only update once
        self._updateScandb = False
        self._versionFile = 'plugins' + os.path.sep + 'discovery' + os.path.sep + 'pykto' + os.path.sep + 'versions.txt'
        
        try:
            fd = file( self._versionFile )
        except:
            raise w3afException('Could not open: ' + self._versionFile + ' while updating pykto scandatabase.' )
        
        try:
            for line in fd:
                if line.count('scan_database.db'):
                    name, localVersion = line.strip().split(',')
                    break
        except:
            raise w3afException('Format error in file: ' + self._versionFile + ' while updating pykto scandatabase.' )
        
        fd.close()
        om.out.debug('Local version of pykto scandatabase.db is: ' + localVersion)
        
        # fetching remote version
        resVersion = self._urlOpener.GET('http://www.cirt.net/nikto/UPDATES/1.35/versions.txt')
        
        fetchedVersion = False
        for line in resVersion.getBody().split():
            if line.count('scan_database.db'):
                name, remoteVersion = line.strip().split(',')
                fetchedVersion = True
        
        if not fetchedVersion:
            om.out.error('pykto can\'t update the scan database, an error ocurred while fetching the versions.txt file from cirt.net .')
        else:
            om.out.debug('Remote version of nikto scandatabase.db is: ' + remoteVersion)
            
            localVersion = float( localVersion )
            remoteVersion = float( remoteVersion )
            
            if localVersion == remoteVersion:
                om.out.information('Local and Remote version of nikto scandatabase.db match, no update needed.')
            elif localVersion > remoteVersion:
                om.out.information('Local version of scandatabase.db is grater than remote version... this is odd... check this.')
            else:
                om.out.information('Updating to scandatabase version: ' + str(remoteVersion) )
                res = self._urlOpener.GET('http://www.cirt.net/nikto/UPDATES/1.35/scan_database.db')
                try:
                    # Write new scandatabase
                    os.unlink( self._dbFile )
                    fdNewDb = file( self._dbFile , 'w')
                    fdNewDb.write( res.getBody() )
                    fdNewDb.close()
                    
                    # Write new version file
                    os.unlink( self._versionFile )
                    fdNewVersion = file( self._versionFile , 'w')
                    fdNewVersion.write( resVersion.getBody() )
                    fdNewVersion.close()
                    
                    om.out.information('Successfully updated scandatabase.db to version: ' + str(remoteVersion) )
                    
                except:
                    raise w3afException('There was an error while writing the new scandatabase.db file to disk.')
                
    
    def _pykto(self, url , scanDbHandle ):
        '''
        This method does all the real work. Writes vulns to the KB.
        
        @return: A list with new url's found.
        '''
        toReturn = []
        lines = 0
        linesSent = 0
        for line in scanDbHandle:
            #om.out.debug( 'Read scan_database: '+ line[:len(line)-1] )
            if not self._isComment( line ):
                # This is a sample scan_database.db line :
                # "apache","/docs/","200","GET","May give list of installed software"
                toSend = self._parse( line )
                
                lines += 1
                
                # A line could generate more than one request... 
                # (think about @CGIDIRS)
                for parameters in toSend:
                    (server, query , expectedResponse, method , desc) = parameters
                    
                    if self._genericScan or self._serverMatch( server ):
                        
                        if self._mutateTests and query[0] == '/':
                            '''
                            This will guarantee that the urlJoin will mutate...
                            Example without this:
                                query = '/bin.out'
                                url = 'http://a.com/f00/'
                                joined = 'http://a.com/bin.out'
                            Example with this:
                                query = '/bin.out'      --->        'bin.out'
                                url = 'http://a.com/f00/'
                                joined = 'http://a.com/f00/bin.out'
                            '''
                            query = query[1:]
                            
                        finalUrl = urlParser.urlJoin( url , query)
                        
                        response = False
                        linesSent += len( toSend )
                        
                        # Send the request to the remote server and check the response.
                        targs = (finalUrl, parameters)
                        try:
                            self._tm.startFunction( target=self._sendAndCheck, args=targs, ownerObj=self )
                        except w3afException, e:
                            om.out.information( str(e) )
                            return
                        except KeyboardInterrupt,e:
                            raise e
                
                self._tm.join( self )
        
        om.out.debug('Read ' + str(lines) + ' from file.' )
        om.out.debug('Sent ' + str(linesSent) + ' requests to remote webserver.' )
        
    def _serverMatch( self, server ):
        '''
        Reads the kb and compares the server parameter with the kb value.
        If they match true is returned.
        
        '''
        # Try to get the server type from hmap
        # it is the most accurate way to do it but hmap plugin
        if kb.kb.getData( 'hmap' , 'server' ) != []:
            kbServer = kb.kb.getData( 'hmap' , 'server' )
            self._source = 'hmap'
        elif kb.kb.getData( 'serverHeader' , 'server' ) != []:
            # Get the server type from the serverHeader plugin. It gets this info
            # by reading the "server" header of request responses.
            kbServer = kb.kb.getData( 'serverHeader' , 'server' )
            self._source = 'serverHeader'
        else:
            self._source = 'not available'
            kbServer = 'not available'
        
        if self._firstTime:
            om.out.information('pykto plugin is using "' + kbServer + '" as the remote server type.'\
            ' This information was obtained by ' + self._source + ' plugin.')
            self._firstTime = False
            
        if kbServer.upper().count( server.upper() ) or server.upper() == 'GENERIC':
            return True
        else:
            return False
        
    def _isComment( self ,line ):
        '''
        The simplest method ever.
        
        @return: Returns if a line is a comment or not.
        '''
        if line[0] == '"':
            return False
        return True
    
    def _parse( self, line ):
        '''
        This method parses a line from the database file
        
        @ return: A a list of tuples where each tuple has the following data
            1. server
            2. query
            3. expectedResponse
            4. method
            5. desc
        '''
        splittedLine = line.split('","')
        
        server = splittedLine[0].replace('"','')
        originalQuery = splittedLine[1].replace('"','')
        expectedResponse = splittedLine[2].replace('"','')
        method = splittedLine[3].replace('"','').upper()
        desc = splittedLine[4].replace('"','')
        desc = desc.replace('\\n', '')
        desc = desc.replace('\\r', '')
        
        if originalQuery.count(' '):
            return []
        else:
            # Now i should replace the @CGIDIRS variable with the user settings
            # The same goes for every @* variable.
            toSend = []
            toSend.append ( (server, originalQuery, expectedResponse, method , desc) )
            
            toMutate = []
            toMutate.append( originalQuery )
            if originalQuery.count( '@CGIDIRS' ):
                for cgiDir in self._cgiDirs:
                    query2 = originalQuery.replace('@CGIDIRS' , cgiDir )
                    toSend.append ( (server, query2, expectedResponse, method , desc) )
                    toMutate.append( query2 )
                toMutate.remove( originalQuery )
                toSend.remove ( (server, originalQuery, expectedResponse, method , desc) )
                
            
            toMutate2 = []
            for query in toMutate:
                res = re.findall( 'JUNK\((.*?)\)', query )
                if res:
                    query2 = re.sub( 'JUNK\((.*?)\)', createRandAlNum( int(res[0]) ), query )
                    toSend.append ( (server, query2, expectedResponse, method , desc) )
                    toMutate2.append( query2 )
                    toSend.remove ( (server, query, expectedResponse, method , desc) )
                    toMutate.remove( query )
            toMutate.extend( toMutate2 )
            
            toMutate2 = []
            for query in toMutate:
                if query.count( '@ADMINDIRS' ):
                    for adminDir in self._adminDirs:
                        query2 = query.replace('@ADMINDIRS' , adminDir )
                        toSend.append ( (server, query2, expectedResponse, method , desc) )
                        toMutate2.append( query2 )
                    toMutate.remove( query )
                    toSend.remove ( (server, query, expectedResponse, method , desc) )
            toMutate.extend( toMutate2 )
            
            toMutate2 = []
            for query in toMutate:
                if query.count( '@NUKE' ):
                    for nuke in self._nuke:
                        query2 = query.replace('@NUKE' , nuke )
                        toSend.append ( (server, query2, expectedResponse, method , desc) )
                        toMutate2.append( query2 )
                    toMutate.remove( query )
                    toSend.remove ( (server, query, expectedResponse, method , desc) )
            toMutate.extend( toMutate2 )
            
            for query in toMutate:
                if query.count( '@USERS' ):         
                    for user in self._users:
                        query2 = query.replace('@USERS' , user )
                        toSend.append ( (server, query2, expectedResponse, method , desc) )
                    toMutate.remove( query )
                    toSend.remove ( (server, query, expectedResponse, method , desc) )

            return toSend
        
    def _sendAndCheck( self , url , parameters ):
        '''
        This method sends the request to the server.
        
        @return: True if the requested uri responded as expected.
        '''
        (server, query , expectedResponse, method , desc) = parameters

        functionReference = getattr( self._urlOpener , method )
        try:
            response = functionReference( url, getSize=False )
        except KeyboardInterrupt,e:
            raise e
        except Exception,e:
            om.out.error( 'Error when requesting: '+ url )
            om.out.error('Error: ' + str(e) )
            return False
        
        if self._analyzeResult( response, expectedResponse, parameters, url ):
            kb.kb.append( self, 'url', response.getURL() )
            
            v = vuln.vuln()
            v.setURI( response.getURI() )
            v.setMethod( method )
            v.setDesc( 'pykto plugin found a vulnerability at URL: ' + v.getURL() + ' . Vulnerability description: ' + desc.strip() )
            v.setId( response.id )
            v.setName( 'Insecure file' )
            v.setSeverity(severity.LOW)

            kb.kb.append( self, 'vuln', v )
            om.out.vulnerability( v.getDesc() )
            
            self._fuzzableRequests.extend( self._createFuzzableRequests( response ) )
        
    def _analyzeResult( self , response , expectedResponse, parameters, uri ):
        '''
        Analyzes the result of a _send()
        
        @return: True if vuln is found
        '''
        if expectedResponse.isdigit():
            intER = int( expectedResponse )
            # This is used when expectedResponse is 200 , 401, 403, etc.
            if response.getCode() == intER and not self.is404( response ):
                # v1: If the file exists, then we have a vuln.
                
                # v2: Not so fast there cowboy! ;)
                # sometimes the response is always a "200", and the final part of the url doesnt even is evaluated
                # by the server... so I'm adding this test.
                if not self._returnWithoutEval( parameters, uri ):
                    return True
        
        elif not self.is404( response ) and response.getBody().count( expectedResponse ):
            # If the content is found, and it's not in a 404 page, then we have a vuln.
            return True
        
        return False
    
    def _returnWithoutEval( self, parameters, uri ):
        if urlParser.getDomainPath( uri ) == uri:
            return False
        
        (server, query , expectedResponse, method , desc) = parameters
        functionReference = getattr( self._urlOpener , method )
        
        url = urlParser.uri2url( uri )
        url += createRandAlNum( 7 )
        if urlParser.getQueryString( query ):
            url = url + '?' + str( urlParser.getQueryString( query ) )
            
        try:
            response = functionReference( url )
        except KeyboardInterrupt,e:
            raise e
        except Exception,e:
            om.out.error( 'Error when requesting: '+ url )
            om.out.error('Error: ' + str(e) )
        else:
            if not self.is404( response ):
                return True
        return False
    
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/ui/userInterface.dtd
        
        @return: XML with the plugin options.
        ''' 
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
            <Option name="cgiDirs">\
                <default>'+','.join(self._cgiDirs)+'</default>\
                <desc>CGI-BIN dirs where to search for vulnerable scripts.</desc>\
                <type>list</type>\
                <help>Pykto will search for vulnerable scripts in many places, one of them is inside cgi-bin directory.\
                The cgi-bin directory can be anything and change from install to install, so its a good idea to make this a\
                user setting. The directories should be supplied comma separated and with a / at the \
                beggining and one at the end. Example: "/cgi/,/cgibin/,/bin/"</help>\
            </Option>\
            <Option name="adminDirs">\
                <default>'+','.join(self._adminDirs)+'</default>\
                <desc>Admin directories where to search for vulnerable scripts.</desc>\
                <type>list</type>\
                <help>Pykto will search for vulnerable scripts in many places, one of them is inside administration directories.\
                The admin directory can be anything and change from install to install, so its a good idea to make this a\
                user setting. The directories should be supplied comma separated and with a / at the \
                beggining and one at the end. Example: "/admin/,/adm/"</help>\
            </Option>\
            <Option name="nukeDirs">\
                <default>'+','.join(self._nuke)+'</default>\
                <desc>PostNuke directories where to search for vulnerable scripts.</desc>\
                <type>list</type>\
                <help>The directories should be supplied comma separated and with a / at the \
                beggining and one at the end. Example: "/forum/,/nuke/"</help>\
            </Option>\
            <Option name="dbFile">\
                <default>'+self._dbFile+'</default>\
                <desc>The path to the nikto scan_databse.db file.</desc>\
                <type>string</type>\
                <help>The default is ok in most cases.</help>\
            </Option>\
            <Option name="mutateTests">\
                <default>'+str(self._mutateTests)+'</default>\
                <desc>Test all files with all root directories</desc>\
                <type>boolean</type>\
                <help>Define if we will test all files with all root directories.</help>\
            </Option>\
            <Option name="updateScandb">\
                <default>'+str(self._updateScandb)+'</default>\
                <desc>Verify that pykto is using the latest scandatabase from cirt.net.</desc>\
                <type>boolean</type>\
                <help></help>\
            </Option>\
            <Option name="genericScan">\
                <default>'+str(self._genericScan)+'</default>\
                <desc>If generic scan is enabled all tests are sent to the remote server without checking the server type.</desc>\
                <type>boolean</type>\
                <help>Pykto will send all tests to the server if generic Scan is enabled.\
                For example, if a test in the database is marked as "apache" and the remote \
                server reported "iis" then the test is sent anyway.</help>\
            </Option>\
        </OptionList>\
        '

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._updateScandb = optionsMap['updateScandb']
        self._cgiDirs = optionsMap['cgiDirs']
        self._adminDirs = optionsMap['adminDirs']
        self._nuke = optionsMap['nukeDirs']
        self._dbFile = optionsMap['dbFile']
        self._mutateTests = optionsMap['mutateTests']
        self._genericScan = optionsMap['genericScan']

        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['discovery.serverHeader','discovery.error404page']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin is a nikto port to python.
        It uses the scandatabase file from nikto to search for new and vulnerable URL's.
        
        Seven configurable parameters exist:
            - updateScandb
            - cgiDirs
            - adminDirs
            - nukeDirs
            - dbFile
            - mutateTests
            - genericScan
        
        This plugin reads every line in the scandatabase and based on the configuration ( "cgiDirs", "adminDirs" , 
        "nukeDirs" and "genericScan" ) it does requests to the remote server searching for common files that may
        introduce vulnerabilities.
        '''
