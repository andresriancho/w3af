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

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.data.fuzzer.fuzzer import createRandAlNum
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException
from core.controllers.w3afException import w3afRunOnce

from core.data.bloomfilter.pybloom import ScalableBloomFilter
from core.controllers.coreHelpers.fingerprint_404 import is_404

import os.path
import re


class pykto(baseDiscoveryPlugin):
    '''
    A nikto port to python. 
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # internal variables
        self._exec = True
        self._already_visited = ScalableBloomFilter()
        self._first_time = True
        self._show_remote_server = True
        
        # User configured parameters
        self._db_file = 'plugins' + os.path.sep + 'discovery' + os.path.sep + 'pykto'
        self._db_file += os.path.sep + 'scan_database.db'
        
        self._extra_db_file = 'plugins' + os.path.sep + 'discovery' + os.path.sep
        self._extra_db_file += 'pykto' + os.path.sep + 'w3af_scan_database.db'
        
        self._cgi_dirs = ['/cgi-bin/']
        self._admin_dirs = ['/admin/', '/adm/'] 
        self._users = ['adm', 'bin', 'daemon', 'ftp', 'guest', 'listen', 'lp',
        'mysql', 'noaccess', 'nobody', 'nobody4', 'nuucp', 'operator',
        'root', 'smmsp', 'smtp', 'sshd', 'sys', 'test', 'unknown']                  
        self._nuke = ['/', '/postnuke/', '/postnuke/html/', '/modules/', '/phpBB/', '/forum/']

        self._mutate_tests = False
        self._generic_scan = False
        self._update_scandb = False
        self._source = ''
        
    def discover(self, fuzzableRequest ):
        '''
        Runs pykto to the site.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                                      (among other things) the URL to test.
        '''
        self._new_fuzzable_requests = []
        
        if not self._exec:
            # dont run anymore
            raise w3afRunOnce()
            
        else:
            # run!
            if self._update_scandb:
                self._update_db()
            
            # Run the basic scan (only once)
            if self._first_time:
                self._first_time = False
                url = urlParser.baseUrl( fuzzableRequest.getURL() )
                self._exec = False
                self.__run( url )
            
            # And now mutate if the user configured it...
            if self._mutate_tests:
                
                # If mutations are enabled, I should keep running
                self._exec = True
                
                # Tests are to be mutated
                url = urlParser.getDomainPath( fuzzableRequest.getURL() )
                if url not in self._already_visited:
                    # Save the directories I already have tested
                    self._already_visited.add( url )
                    self.__run( url )

        return self._new_fuzzable_requests
                
    def __run( self, url ):
        '''
        Really run the plugin.
        
        @parameter url: The URL I have to test.
        '''
        try:
            # read the nikto database.
            db_file_1 = open(self._db_file, "r")
            # read the w3af scan database.
            db_file_2 = open(self._extra_db_file, "r")
        except Exception, e:
            raise w3afException('Failed to open the scan databases. Exception: "' + str(e) + '".')
        else:

            # Put all the tests in a list
            test_list = db_file_1.readlines()
            test_list.extend(db_file_2.readlines())
            # Close the files
            db_file_1.close()
            db_file_2.close()

            # pykto that site !
            self._pykto( url , test_list )
        
    def _update_db( self ):
        '''
        This method updates the scan_database from cirt.net .
        '''
        # Only update once
        self._update_scandb = False

        # Here we have the versions
        _version_file = 'plugins' + os.path.sep + 'discovery' + os.path.sep + 'pykto'
        _version_file += os.path.sep + 'versions.txt'
        
        try:
            version_file = file( _version_file )
        except Exception, e:
            msg = 'Could not open: "' + _version_file + '" while updating pykto scan_database.'
            msg += ' Exception message: "' + str(e) + '".'
            raise w3afException( msg )
        
        try:
            for line in version_file:
                if line.count('scan_database.db'):
                    _, local_version = line.strip().split(',')
                    break
        except:
            msg = 'Format error in file: ' + _version_file + ' while updating pykto scan_database.'
            raise w3afException( msg )
        
        version_file.close()
        om.out.debug('Local version of pykto scan_database.db is: ' + local_version)
        
        # fetching remote version
        res_version = self._urlOpener.GET('http://www.cirt.net/nikto/UPDATES/1.36/versions.txt')
        
        fetched_version = False
        for line in res_version.getBody().split():
            if line.count('scan_database.db'):
                _, remote_version = line.strip().split(',')
                fetched_version = True
        
        if not fetched_version:
            msg = 'pykto can\'t update the scan database, an error ocurred while fetching the'
            msg += ' versions.txt file from cirt.net .'
            om.out.error( msg )
        else:
            om.out.debug('Remote version of nikto scan_database.db is: "' + remote_version + '".')
            
            local_version = float( local_version )
            remote_version = float( remote_version )
            
            if local_version == remote_version:
                msg = 'Local and Remote version of nikto scan_database.db match, no update needed.'
                om.out.information( msg )
            elif local_version > remote_version:
                msg = 'Local version of scan_database.db is grater than remote version... this is'
                msg += ' odd... check this.'
                om.out.information()
            else:
                msg = 'Updating to scan_database version: "' + str(remote_version) + '".'
                om.out.information( msg )
                res = self._urlOpener.GET('http://www.cirt.net/nikto/UPDATES/1.36/scan_database.db')
                try:
                    # Write new scan_database
                    os.unlink( self._db_file )
                    fd_new_db = file( self._db_file , 'w')
                    fd_new_db.write( res.getBody() )
                    fd_new_db.close()
                    
                    # Write new version file
                    os.unlink( _version_file )
                    fd_new_version = file( _version_file , 'w')
                    fd_new_version.write( res_version.getBody() )
                    fd_new_version.close()
                    
                    msg = 'Successfully updated scan_database.db to version: ' + str(remote_version)
                    om.out.information( msg )
                    
                except Exception, e:
                    msg = 'There was an error while writing the new scan_database.db file to disk.'
                    msg += ' Exception message: "' + str(e) + '".'
                    raise w3afException( msg )
                
    
    def _pykto(self, url , test_list ):
        '''
        This method does all the real work and writes vulns to the KB.

        @parameter url: The base URL
        @parameter test_list: The list of all the tests that have to be performed        
        @return: A list with new url's found.
        '''
        lines = 0
        lines_sent = 0
        for line in test_list:
            #om.out.debug( 'Read scan_database: '+ line[:len(line)-1] )
            if not self._is_comment( line ):
                # This is a sample scan_database.db line :
                # "apache","/docs/","200","GET","May give list of installed software"
                to_send = self._parse( line )
                
                lines += 1
                
                # A line could generate more than one request... 
                # (think about @CGIDIRS)
                for parameters in to_send:
                    (server, query , expected_response, method , desc) = parameters
                    
                    if self._generic_scan or self._server_match( server ):
                        #
                        # Avoid some special cases
                        #
                        if url.endswith('/./') or url.endswith('/%2e/'):
                            # avoid directory self references
                            continue
                        #
                        # End of special cases
                        #
                        
                        om.out.debug('Testing pykto signature: "' + query + '".')

                        # I don't use urlJoin here because in some cases pykto needs to
                        # send something like http://abc/../../../../etc/passwd
                        # and after urlJoin the URL would be just http://abc/etc/passwd
                        
                        # But I do want is to avoid URLs like this one being generated:
                        # http://localhost//f00
                        # (please note the double //)
                        if query[0] == '/' == url[-1]:
                            query = query[1:]
                            
                        final_url = url + query
                        
                        lines_sent += len( to_send )
                        
                        # Send the request to the remote server and check the response.
                        targs = (final_url, parameters)
                        try:
                            # Performing this with different threads adds overhead, but works better now.
                            #   WithOUT threads:
                            #self._send_and_check(final_url, parameters)
                            
                            #   With threads:
                            #           Performed 3630 requests in 13 seconds (279.230769 req/sec)
                            self._tm.startFunction( target=self._send_and_check, args=targs , ownerObj=self )
                            
                        except w3afException, e:
                            om.out.information( str(e) )
                            return
                        except KeyboardInterrupt,e:
                            raise e
                
                self._tm.join( self )
        
        om.out.debug('Read ' + str(lines) + ' from file.' )
        om.out.debug('Sent ' + str(lines_sent) + ' requests to remote webserver.' )
        
    def _server_match( self, server ):
        '''
        Reads the kb and compares the server parameter with the kb value.
        If they match true is returned.
        
        @parameter server: A server name like "apache"
        '''
        # Try to get the server type from hmap
        # it is the most accurate way to do it but hmap plugin
        if kb.kb.getData( 'hmap' , 'serverString' ) != []:
            kb_server = kb.kb.getData( 'hmap' , 'serverString' )
            self._source = 'hmap'

        elif kb.kb.getData( 'serverHeader' , 'serverString' ) != []:
            # Get the server type from the serverHeader plugin. It gets this info
            # by reading the "server" header of request responses.
            kb_server = kb.kb.getData( 'serverHeader' , 'serverString' )
            self._source = 'serverHeader'

        else:
            self._source = 'not available'
            kb_server = 'not available'
        
        if self._show_remote_server:
            msg = 'pykto plugin is using "' + kb_server + '" as the remote server type.'
            msg += ' This information was obtained by ' + self._source + ' plugin.'
            om.out.information( msg )
            self._show_remote_server = False
            
        if kb_server.upper().count( server.upper() ) or server.upper() == 'GENERIC':
            return True
        else:
            return False
        
    def _is_comment( self, line ):
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
            3. expected_response
            4. method
            5. desc
        '''
        splitted_line = line.split('","')
        
        server = splitted_line[0].replace('"','')
        original_query = splitted_line[1].replace('"','')
        expected_response = splitted_line[2].replace('"','')
        method = splitted_line[3].replace('"','').upper()
        desc = splitted_line[4].replace('"','')
        desc = desc.replace('\\n', '')
        desc = desc.replace('\\r', '')
        
        if original_query.count(' '):
            return []
        else:
            # Now i should replace the @CGIDIRS variable with the user settings
            # The same goes for every @* variable.
            to_send = []
            to_send.append ( (server, original_query, expected_response, method , desc) )
            
            to_mutate = []
            to_mutate.append( original_query )
            if original_query.count( '@CGIDIRS' ):
                for cgiDir in self._cgi_dirs:
                    query2 = original_query.replace('@CGIDIRS' , cgiDir )
                    to_send.append ( (server, query2, expected_response, method , desc) )
                    to_mutate.append( query2 )
                to_mutate.remove( original_query )
                to_send.remove ( (server, original_query, expected_response, method , desc) )
                
            
            to_mutate2 = []
            for query in to_mutate:
                res = re.findall( 'JUNK\((.*?)\)', query )
                if res:
                    query2 = re.sub( 'JUNK\((.*?)\)', createRandAlNum( int(res[0]) ), query )
                    to_send.append ( (server, query2, expected_response, method , desc) )
                    to_mutate2.append( query2 )
                    to_send.remove ( (server, query, expected_response, method , desc) )
                    to_mutate.remove( query )
            to_mutate.extend( to_mutate2 )
            
            to_mutate2 = []
            for query in to_mutate:
                if query.count( '@ADMINDIRS' ):
                    for adminDir in self._admin_dirs:
                        query2 = query.replace('@ADMINDIRS' , adminDir )
                        to_send.append ( (server, query2, expected_response, method , desc) )
                        to_mutate2.append( query2 )
                    to_mutate.remove( query )
                    to_send.remove ( (server, query, expected_response, method , desc) )
            to_mutate.extend( to_mutate2 )
            
            to_mutate2 = []
            for query in to_mutate:
                if query.count( '@NUKE' ):
                    for nuke in self._nuke:
                        query2 = query.replace('@NUKE' , nuke )
                        to_send.append ( (server, query2, expected_response, method , desc) )
                        to_mutate2.append( query2 )
                    to_mutate.remove( query )
                    to_send.remove ( (server, query, expected_response, method , desc) )
            to_mutate.extend( to_mutate2 )
            
            for query in to_mutate:
                if query.count( '@USERS' ):         
                    for user in self._users:
                        query2 = query.replace('@USERS' , user )
                        to_send.append ( (server, query2, expected_response, method , desc) )
                    to_mutate.remove( query )
                    to_send.remove ( (server, query, expected_response, method , desc) )

            return to_send
        
    def _send_and_check( self , url , parameters ):
        '''
        This method sends the request to the server.
        
        @return: True if the requested uri responded as expected.
        '''
        (server, query , expected_response, method , desc) = parameters

        function_reference = getattr( self._urlOpener , method )
        try:
            response = function_reference( url )
        except KeyboardInterrupt,e:
            raise e
        except w3afException, e:
            msg = 'An exception was raised while requesting "'+url+'" , the error message is: '
            msg += str(e)
            om.out.error( msg )
            return False
        
        if self._analyzeResult( response, expected_response, parameters, url ):
            kb.kb.append( self, 'url', response.getURL() )
            
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setURI( response.getURI() )
            v.setMethod( method )
            vuln_desc = 'pykto plugin found a vulnerability at URL: "' + v.getURL() + '". '
            vuln_desc += 'Vulnerability description: "' + desc.strip() + '"'
            if not vuln_desc.endswith('.'):
                vuln_desc += '.'
            v.setDesc( vuln_desc )
            v.setId( response.id )

            if not urlParser.getPath(response.getURL()).endswith('/'):
                msg = 'Insecure file - ' + urlParser.getPath(response.getURL())
            else:
                msg = 'Insecure directory - ' + urlParser.getPath(response.getURL())
            v.setName( msg )
            v.setSeverity(severity.LOW)

            kb.kb.append( self, 'vuln', v )
            om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
            
            self._new_fuzzable_requests.extend( self._createFuzzableRequests( response ) )
        
    def _analyzeResult( self , response , expected_response, parameters, uri ):
        '''
        Analyzes the result of a _send()
        
        @return: True if vuln is found
        '''
        if expected_response.isdigit():
            int_er = int( expected_response )
            # This is used when expected_response is 200 , 401, 403, etc.
            if response.getCode() == int_er and not is_404( response ):
                return True
        
        elif expected_response in response and not is_404( response ):
            # If the content is found, and it's not in a 404 page, then we have a vuln.
            return True
        
        return False
    
    def _return_without_eval( self, parameters, uri ):
        if urlParser.getDomainPath( uri ) == uri:
            return False
        
        (server, query , expected_response, method , desc) = parameters
        function_reference = getattr( self._urlOpener , method )
        
        url = urlParser.uri2url( uri )
        url += createRandAlNum( 7 )
        if urlParser.getQueryString( query ):
            url = url + '?' + str( urlParser.getQueryString( query ) )
            
        try:
            response = function_reference( url )
        except KeyboardInterrupt,e:
            raise e
        except w3afException,e:
            msg = 'An exception was raised while requesting "'+url+'" , the error message is: '
            msg += str(e)
            om.out.error( msg )
        else:
            if not is_404( response ):
                return True
        return False

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'CGI-BIN dirs where to search for vulnerable scripts.'
        h1 = 'Pykto will search for vulnerable scripts in many places, one of them is inside'
        h1 += ' cgi-bin directory. The cgi-bin directory can be anything and change from install'
        h1 += ' to install, so its a good idea to make this a user setting. The directories should'
        h1 += ' be supplied comma separated and with a / at the beggining and one at the end.'
        h1 += ' Example: "/cgi/,/cgibin/,/bin/"'
        o1 = option('cgiDirs', self._cgi_dirs , d1, 'list', help=h1)
        
        d2 = 'Admin directories where to search for vulnerable scripts.'
        h2 = 'Pykto will search for vulnerable scripts in many places, one of them is inside'
        h2 += ' administration directories. The admin directory can be anything and change'
        h2 += ' from install to install, so its a good idea to make this a user setting. The'
        h2 += ' directories should be supplied comma separated and with a / at the beggining and'
        h2 += ' one at the end. Example: "/admin/,/adm/"'
        o2 = option('adminDirs', self._admin_dirs, d2, 'list', help=h2)
        
        d3 = 'PostNuke directories where to search for vulnerable scripts.'
        h3 = 'The directories should be supplied comma separated and with a / at the'
        h3 += ' beggining and one at the end. Example: "/forum/,/nuke/"'
        o3 = option('nukeDirs', self._nuke, d3, 'list', help=h3)

        d4 = 'The path to the nikto scan_databse.db file.'
        h4 = 'The default scan database file is ok in most cases.'
        o4 = option('dbFile', self._db_file, d4, 'string', help=h4)

        d5 = 'Test all files with all root directories'
        h5 = 'Define if we will test all files with all root directories.'
        o5 = option('mutateTests', self._mutate_tests, d5, 'boolean', help=h5)        

        d6 = 'Verify that pykto is using the latest scan_database from cirt.net.'
        o6 = option('updateScandb', self._update_scandb, d6, 'boolean')

        d7 = 'If generic scan is enabled all tests are sent to the remote server without'
        d7 += ' checking the server type.'
        h7 = 'Pykto will send all tests to the server if generic Scan is enabled. For example,'
        h7 += ' if a test in the database is marked as "apache" and the remote server reported'
        h7 += ' "iis" then the test is sent anyway.'
        o7 = option('genericScan', self._generic_scan, d7, 'boolean', help=h7)        

        d8 = 'The path to the w3af_scan_databse.db file.'
        h8 = 'This is a file which has some extra checks for files that are not present in the'
        h8 += ' nikto database.'
        o8 = option('extra_db_file', self._extra_db_file, d8, 'string', help=h8)

        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        ol.add(o8)  # Intentionally out of order
        ol.add(o5)
        ol.add(o6)
        ol.add(o7)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user int_erface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._update_scandb = optionsMap['updateScandb'].getValue()
        self._cgi_dirs = optionsMap['cgiDirs'].getValue()
        self._admin_dirs = optionsMap['adminDirs'].getValue()
        self._nuke = optionsMap['nukeDirs'].getValue()
        self._extra_db_file = optionsMap['extra_db_file'].getValue()
        self._db_file = optionsMap['dbFile'].getValue()
        self._mutate_tests = optionsMap['mutateTests'].getValue()
        self._generic_scan = optionsMap['genericScan'].getValue()
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['discovery.serverHeader']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin is a nikto port to python.
        It uses the scan_database file from nikto to search for new and vulnerable URL's.
        
        Seven configurable parameters exist:
            - updateScandb
            - cgiDirs
            - adminDirs
            - nukeDirs
            - dbFile
            - extra_db_file
            - mutateTests
            - genericScan
        
        This plugin reads every line in the scan_database (and extra_db_file) and based on the configuration 
        ( "cgiDirs", "adminDirs" , "nukeDirs" and "genericScan" ) it performs requests to the remote server
        searching for common files that may contain vulnerabilities.
        '''
