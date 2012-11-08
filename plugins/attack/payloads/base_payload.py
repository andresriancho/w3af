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
import textwrap

import plugins.attack.payloads.payload_handler as payload_handler

from core.controllers.threads.threadpool import return_args
from core.controllers.threads.threadManager import thread_manager

SYSCALL_LIST = ['read', 'write', 'execute', 'unlink', 'is_open_port']


class base_payload(object):

    def __init__(self, shell_obj):
        self.shell = shell_obj
        
    def can_run(self):
        '''
        @return: True if this payload has any way of running with the "syscalls"
                 provided by the shell_obj.
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
        
    def exec_payload(self, payload_name, args=()):
        '''
        Execute ANOTHER payload, by providing the other payload name.
        
        @param payload_name: The name of the payload I want to run.
        @return: The payload result.
        '''
        try:
            return payload_handler.exec_payload(self.shell, payload_name, args, use_api=True)
        except:
            #
            #    Run the payload name with any shell that has the capabilities we need,
            #    not the one we're already using (that failed because it doesn't have
            #    the capabilities).
            #
            try:
                return payload_handler.exec_payload(None, payload_name, args, use_api=True)
            except:
                msg = 'The payload you are trying to run ("%s") can not be run with the current' % self
                msg += ' is trying to call another payload ("%s") which is failing because' % payload_name
                msg += ' there are no shells that support the necessary system calls.'
                return msg
                
    
    def run(self, *args):
        '''
        @return: The result of running the payload using the most performant way. Basically, if
        I can run commands using exec() I'll use that, if not I'll use read().
        '''
        #   Get the syscalls that this shell_obj implements
        available_syscalls = dir(self.shell)
        available_syscalls = [ x for x in available_syscalls if x in SYSCALL_LIST ]
        
        #   Get the different implementations of "run" that this payload has
        run_options = dir(self)
        run_options = [ x[4:] for x in run_options if x.startswith('run_')]

        if 'execute' in run_options and 'execute' in available_syscalls:
            return self.run_execute( *args )
        elif 'is_open_port' in run_options and 'is_open_port' in available_syscalls:
            return self.run_is_open_port( *args )
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
        run_options = [ x[4:] for x in run_options if x.startswith('api_')]

        if 'execute' in run_options and 'execute' in available_syscalls:
            return self.api_execute( *args )
        elif 'is_open_port' in run_options and 'is_open_port' in available_syscalls:
            return self.api_is_open_port( *args )
        else:
            return self.api_read( *args )

    def require(self):
        '''
        @return: The operating system requirement to run this payload.
        '''
        return 'linux'
    
    def read_multi(self, fname_iter):
        '''
        @param fname_iter: An iterator that yields all the file names to read.
        '''
        read_file = return_args(self.shell.read)
        for (file_name,), content in thread_manager.threadpool.imap_unordered(read_file, fname_iter):
            yield file_name, content
        
    def get_desc(self):
        if self.__doc__ is not None:
            return textwrap.dedent(self.__doc__ ).strip()
        else:
            return 'No help available for this payload.'
       