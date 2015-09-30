"""
sqlmap.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
import copy
import Queue
import select
import textwrap

from multiprocessing.dummy import Process

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.exceptions import OSDetectionException
from w3af.core.controllers.plugins.attack_plugin import AttackPlugin
from w3af.core.controllers.intrusion_tools.readMethodHelpers import read_os_detection
from w3af.core.data.kb.read_shell import ReadShell
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.fuzzer.mutants.postdata_mutant import PostDataMutant
from w3af.plugins.attack.db.sqlmap_wrapper import Target, SQLMapWrapper
from w3af.plugins.attack.payloads.decorators.read_decorator import read_debug


class sqlmap(AttackPlugin):
    """
    Exploit web servers that have sql injection vulnerabilities using sqlmap.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        AttackPlugin.__init__(self)

        # Internal variables
        self._sqlmap = None

    def get_attack_type(self):
        """
        :return: The type of exploit, SHELL, PROXY, etc.
        """
        return 'shell'

    def get_kb_location(self):
        """
        This method should return the vulnerability name (as saved in the kb)
        to exploit. For example, if the audit.os_commanding plugin finds an
        vuln, and saves it as:

        kb.kb.append( 'os_commanding' , 'os_commanding', vuln )

        Then the exploit plugin that exploits os_commanding
        ( attack.os_commanding ) should return 'os_commanding' in this method.
        """
        return ['sqli', 'blind_sqli']

    def _generate_shell(self, vuln_obj):
        """
        :param vuln_obj: The vuln to exploit.
        :return: The shell object based on the vulnerability that was passed as
                 a parameter.
        """
        # Check if we really can execute commands on the remote server
        if self._verify_vuln(vuln_obj):
            # Create the shell object
            shell_obj = SQLMapShell(vuln_obj, self._uri_opener,
                                    self.worker_pool, self._sqlmap)
            return shell_obj
        else:
            return None

    def _verify_vuln(self, vuln_obj):
        """
        This command verifies a vuln. This is really hard work! :P

        :return : True if vuln can be exploited.
        """
        mutant = vuln_obj.get_mutant()

        if not isinstance(mutant, (QSMutant, PostDataMutant)):
            msg = ('The SQL injection vulnerability at %s can not be exploited'
                   ' by w3af\'s sqlmap wrapper because it can only handle'
                   ' query string and url-encoded post data parameters.')
            om.out.console(msg % (mutant.get_url(),))
            return False

        orig_value = mutant.get_token().get_original_value()

        # When the original value of the parameter was empty, mostly when it
        # was an HTML form, sqlmap can't find the vulnerability (and w3af does)
        # so we're adding a '1' here just in case.
        parameter_values = {orig_value, '1'}

        for pvalue in parameter_values:
            mutant = copy.deepcopy(mutant)
            mutant.set_token_value(pvalue)

            self._sqlmap = None

            post_data = mutant.get_data() or None
            target = Target(mutant.get_uri(), post_data)

            try:
                sqlmap = SQLMapWrapper(target, self._uri_opener)
            except TypeError:
                issue_url = 'https://github.com/andresriancho/w3af/issues/6439'
                msg = ('w3af\'s sqlmap wrapper has some limitations, and you'
                       ' just found one of them. For more information please'
                       ' visit %s .')
                om.out.console(msg % issue_url)
                return False

            try:
                is_vuln = sqlmap.is_vulnerable()
            except:
                sqlmap.cleanup()

                if sqlmap.last_stdout is None or sqlmap.last_stderr is None:
                    # Not sure when we get here
                    return False

                taint_error = 'provided tainted parameter'
                if not (taint_error in sqlmap.last_stdout or
                        taint_error in sqlmap.last_stderr):
                    # Some error that we don't have a special handling for
                    return False

                issue_url = 'https://github.com/andresriancho/w3af/issues/1989'
                msg = ('w3af\'s sqlmap wrapper has some limitations, and you'
                       ' just found one of them. For more information please'
                       ' visit %s and add the steps required to reproduce this'
                       ' issue which will help us debug and fix it.')
                om.out.console(msg % issue_url)
                return False

            if is_vuln:
                self._sqlmap = sqlmap
                return True
            else:
                sqlmap.cleanup()
        
        return False

    def get_root_probability(self):
        """
        :return: This method returns the probability of getting a root shell
                 using this attack plugin. This is used by the "exploit *"
                 function to order the plugins and first try to exploit the
                 more critical ones. This method should return 0 for an exploit
                 that will never return a root shell, and 1 for an exploit that
                 WILL ALWAYS return a root shell.
        """
        return 0.8

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin exploits SQL injection vulnerabilities using sqlmap. For
        more information about sqlmap please visit:
        
            http://sqlmap.org/
        """


class RunFunctor(Process):
    def __init__(self, functor, params):
        super(RunFunctor, self).__init__()
        self.daemon = True
        self.name = 'SQLMapWrapper'
        
        self.functor = functor
        self.params = params
        self.user_input = Queue.Queue()
        
        class FakeProcess(object):
            def poll(self):
                return None
        self.process = FakeProcess()
        
    def run(self):
        cmd, process = apply(self.functor, self.params)

        if process is None:
            # Something really bad happen with sqlmap
            om.out.console('Failed to start the sqlmap subprocess')
            return
        
        self.process = process
        
        om.out.information('Wrapped SQLMap command: %s' % cmd)
        
        try:
            while process.poll() is None:
                read_ready, _, _ = select.select([process.stdout], [], [], 0.1)
                
                if read_ready:
                    line = process.stdout.read(1)
                    om.out.console(line, new_line=False)
                    
        except KeyboardInterrupt:
            om.out.information('Terminating SQLMap after Ctrl+C.')
            process.terminate()
        
        final_content = process.stdout.read()
        om.out.console(final_content, new_line=False)


class SQLMapShell(ReadShell):

    ALIAS = ('dbs', 'tables', 'users', 'dump')

    def __init__(self, vuln, uri_opener, worker_pool, sqlmap):
        self.sqlmap = sqlmap
        super(SQLMapShell, self).__init__(vuln, uri_opener, worker_pool)

    def specific_user_input(self, command, params, return_err=True):
        # Call the parent in order to get read/download without duplicating
        # any code.
        #
        # Not using super() due to some issues I've found in real life
        #   https://github.com/andresriancho/w3af/issues/3610
        #
        # Documented here:
        #   http://goo.gl/jhRznU
        #   http://thomas-cokelaer.info/blog/2011/09/382/
        resp = ReadShell.specific_user_input(self, command, params,
                                             return_err=False)
        
        if resp is not None:
            return resp
        
        # SQLMap specific code starts
        params = tuple(params)
        functor = None
        
        if command in self.ALIAS:
            functor = getattr(self.sqlmap, command)
        
        if command == 'sqlmap':
            functor = self.sqlmap.direct
        
        if functor is not None:
            # TODO: I run this in a different thread in order to be able to
            #       (in the future) handle stdin and all other UI inputs.
            sqlmap_thread = RunFunctor(functor, params)
            sqlmap_thread.start()
            sqlmap_thread.join()
            
            # Returning this empty string makes the console avoid printing
            # a message that says that the command was not found
            return ''
        
        return
    
    @read_debug        
    def read(self, filename):
        return self.sqlmap.read(filename)
    
    def get_name(self):
        return 'sqlmap'
    
    def end(self):
        self.sqlmap.cleanup()
    
    def __repr__(self):
        """
        :return: A string representation of this shell.
        """
        return '<sqlmap shell object>'
    
    def identify_os(self):
        """
        Identify the remote operating system by reading different files from
        the OS.
        """
        try:
            self._rOS = read_os_detection(self.read)
        except OSDetectionException, osde:
            om.out.debug('%s' % osde)
            self._rOS = 'unknown'
        
        # TODO: Could we determine this by calling some payloads?
        self._rSystem = 'sqlmap'
        self._rSystemName = 'db'
        self._rUser = 'sqlmap'
        
    def help(self, command):
        """
        Handle the help command.
        """
        if command in ('read', 'download'):
            return super(SQLMapShell, self).help(command)
        
        elif command == 'sqlmap':
            _help = """\
            sqlmap:
                Run sqlmap and specify any extra parameters.
            
            Examples:
                sqlmap -T users -D example_db --dump
                sqlmap --tables
                sqlmap --dbs
            """
        else:
            _help = """\
            Available commands:
                help                            Display this information
                
                lsp                             List payloads
                payload <payload>               Execute "payload" and get the result
                read <file>                     Read the remote server <file> and echo to this console
                download <remote> <local>       Download <remote> file to <local> file system location
                
                dbs                             List DBMS databases
                tables                          List DBMS tables for the current database 
                users                           List DBMS users
                dump                            Dump table information
                
                sqlmap                          Run a sqlmap command. For example, the "dbs" command
                                                is an alias for "sqlmap --dbs".
                
                exit                            Exit this shell session
            """
        return textwrap.dedent(_help)

    def __reduce__(self):
        """
        Need to define this method since the Shell class defines it, and we have
        a different number of __init__ parameters.
        """
        return self.__class__, (self._vuln, None, None, self.sqlmap)

    def set_url_opener(self, uo):
        if uo is not None:
            self._uri_opener = uo
            self.sqlmap.start_proxy(uo)