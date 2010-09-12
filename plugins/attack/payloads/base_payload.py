'''
base_payload.py

Copyright 2009 Andres Riancho

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

import plugins.attack.payloads.payload_handler as payload_handler

SYSCALL_LIST = ['read', 'write', 'execute', 'unlink']


class base_payload(object):

    def __init__(self, shell_obj):
        self.shell = shell_obj
        
    def can_run(self):
        '''
        @return: True if this payload has any way of running with the "syscalls" provided by the
        shell_obj.
        '''
        #   Get the syscalls that this shell_obj implements
        available_syscalls = dir(self.shell)
        available_syscalls = [ x for x in available_syscalls if x in SYSCALL_LIST ]
        available_syscalls = set(available_syscalls)
        
        #   Get the different implementations of "run" that this payload has
        run_options = dir(self)
        run_options = [ x[4:] for x in run_options if x.startswith('run_')]
        run_options = set(run_options)
        
        return available_syscalls.intersection(run_options)
        
    def exec_payload(self, payload_name):
        '''
        Execute ANOTHER payload, by providing the other payload name.
        
        @parameter payload_name: The name of the payload I want to run.
        @return: The payload result.
        '''
        return payload_handler.exec_payload(self.shell, payload_name, use_api=True)
    
    def run(self,  *args):
        '''
        @return: The result of running the payload using the most performant way. Basically, if
        I can run commands using exec() I'll use that, if not I'll use read().
        '''
        #   Get the syscalls that this shell_obj implements
        available_syscalls = dir(self.shell)
        available_syscalls = [ x for x in available_syscalls if x in SYSCALL_LIST ]
        
        #   Get the different implementations of "run" that this payload has
        run_options = dir(self)
        run_options = [ x[:4] for x in run_options if x.startswith('run_')]

        if 'exec' in run_options and 'exec' in available_syscalls:
            return self.run_exec( *args )
        else:
            return self.run_read( *args )
    
    def run_api(self, *args):
        '''
        @return: The result of running the payload using the most performant way. Basically, if
        I can run commands using exec() I'll use that, if not I'll use read().
        '''
        #   Get the syscalls that this shell_obj implements
        available_syscalls = dir(self.shell)
        available_syscalls = [ x for x in available_syscalls if x in SYSCALL_LIST ]
        
        #   Get the different implementations of "run" that this payload has
        run_options = dir(self)
        run_options = [ x[:4] for x in run_options if x.startswith('api_')]

        if 'exec' in run_options and 'exec' in available_syscalls:
            return self.api_exec( *args )
        else:
            return self.api_read( *args )


    def require(self):
        '''
        @return: The operating system requirement to run this payload.
        '''
        return 'linux'
