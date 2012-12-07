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

from core.data.kb.read_shell import ReadShell
from core.data.dc.form import Form
from core.controllers.plugins.attack_plugin import AttackPlugin
from plugins.attack.db.sqlmap_wrapper import Target, SQLMapWrapper


class sqlmap(AttackPlugin):
    '''
    Exploit web servers that have sql injection vulnerabilities using sqlmap.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        AttackPlugin.__init__(self)

        # Internal variables
        self._sqlmap = None

    def get_attack_type(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''
        return 'shell'

    def get_kb_location(self):
        '''
        This method should return the vulnerability name (as saved in the kb)
        to exploit. For example, if the audit.os_commanding plugin finds an
        vuln, and saves it as:

        kb.kb.append( 'os_commanding' , 'os_commanding', vuln )

        Then the exploit plugin that exploits os_commanding
        ( attack.os_commanding ) should return 'os_commanding' in this method.
        '''
        return ['sqli', 'blind_sqli']

    def _generate_shell(self, vuln_obj):
        '''
        @param vuln_obj: The vuln to exploit.
        @return: The shell object based on the vulnerability that was passed as
                 a parameter.
        '''
        # Check if we really can execute commands on the remote server
        if self._verify_vuln(vuln_obj):
            # Create the shell object
            shell_obj = SQLMapShell(vuln_obj)
            shell_obj.set_url_opener(self._uri_opener)
            shell_obj.set_wrapper(self._sqlmap)
            return shell_obj
        else:
            return None

    def _verify_vuln(self, vuln_obj):
        '''
        This command verifies a vuln. This is really hard work! :P

        @return : True if vuln can be exploited.
        '''
        uri = vuln_obj.get_uri()
        
        post_data = None
        
        dc = vuln_obj.get_dc()
        if isinstance(dc, Form):
            post_data = str(dc) or None
        
        target = Target(uri, post_data)
        
        sqlmap = SQLMapWrapper(target)
        if sqlmap.is_vulnerable():
            self._sqlmap = sqlmap
            return True
        
        return False

    def get_root_probability(self):
        '''
        @return: This method returns the probability of getting a root shell
                 using this attack plugin. This is used by the "exploit *"
                 function to order the plugins and first try to exploit the
                 more critical ones. This method should return 0 for an exploit
                 that will never return a root shell, and 1 for an exploit that
                 WILL ALWAYS return a root shell.
        '''
        return 0.8

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits SQL injection vulnerabilities using sqlmap. For
        more information about sqlmap please visit:
        
            http://sqlmap.org/
        '''


class SQLMapShell(ReadShell):
    def set_wrapper(self, sqlmap):
        self.sqlmap = sqlmap

    def get_wrapper(self):
        return self.sqlmap

    ALIAS = ('dbs', 'tables', 'users', 'dump')

    def _run_functor(self, functor, params):
        cmd, process = apply(functor, params)
        
        om.out.information('Wrapped SQLMap command: %s' % cmd)
        # FIXME: What about stdin? How do we get the user input here?
        while process.poll() is None:
            for line in process.stdout.readline():
                om.out.console(line, newLine=False)
        
        final_content = process.stdout.read()
        om.out.console(final_content, newLine=False)

    def specific_user_input(self, command, params):
        # Call the parent in order to get read/download without duplicating
        # any code.
        resp = super(SQLMapShell, self).specific_user_input(command, params,
                                                            return_err=False)
        
        if resp is not None:
            return resp
        
        # SQLMap specific code starts
        params = tuple(params)
        
        if command in self.ALIAS:
            alias = getattr(self.sqlmap, command)
            self._run_functor(alias, params)
            return ''
        
        if command == 'sqlmap':
            self._run_functor(self.sqlmap.direct, params)
            return ''
        
        return
            
    def read(self, filename):
        return self.sqlmap.read(filename)
    
    def get_name(self):
        return 'sqlmap'

    def __repr__(self):
        '''
        @return: A string representation of this shell.
        '''
        return '<sqlmap shell object>'
    