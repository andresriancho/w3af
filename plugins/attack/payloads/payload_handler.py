'''
payload_runner.py

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

import sys
import os
import compiler
import core.controllers.outputManager as om


def get_used_syscalls( payload_filename ):
    '''
    With functions I get the syscalls that are used by the payload.
    
    @parameter payload_filename: The payload filename that we want to analyze.
    @return: The list of syscalls that the payload needs.
    '''
    class payload_visitor:
        def __init__(self):
            self.defined_functions = []
            self.called_functions = []

        def visitFunction(self, parsed_func):
            if parsed_func.name in dir(__builtins__):
                msg = 'Please use a different name, overriding Python builtin functions'
                msg += ' is not recommended in Web Application Payloads.'
                print msg
            
            self.defined_functions.append( parsed_func.name )

        def visitCallFunc(self, info):
            #
            #  This fixes the bug that was reported by Juliano Rizzo that happens
            #  when a user does something like this: "file_handler.read()"
            #
            try:
                if info.node.name not in dir(__builtins__):
                    self.called_functions.append( info.node.name )
            except Exception,  e:
                pass

        def get_requirements(self):
            return list( set(self.called_functions) - set(self.defined_functions) )

    ast = compiler.parseFile( payload_filename )
    result = compiler.visitor.walk(ast, payload_visitor() )
    return result.get_requirements()


def can_run(shell_obj, requirements):
    '''
    @parameter requirements: The syscalls that the current payload needs.
    @parameter shell_obj: The shell object that will run the payload.
    @return: True if the shell_obj can run the payload.
    '''
    available_functions = dir(shell_obj)
    available_functions.append('console')
    
    for name in requirements:
        if not name in available_functions:
            return False
    return True


def exec_payload(shell_obj, payload_filename):
    '''
    Now I execute the payload, by providing the function names that are in the shell_obj
    as "globals".
    
    @parameter shell_obj: The shell object instance.
    @return: The payload "result" variable.
    '''
    compiled = compiler.compile( file(payload_filename).read() , payload_filename, 'exec')

    # Inject the syscalls provided by the exploit
    __globals = {}
    for name in dir(shell_obj):
        __globals[name] = getattr(shell_obj, name)
        
    # Inject the functions provided by the framework for debugging
    __globals['console'] = getattr(om.out, 'console')

    exec compiled in __globals
    
    if 'result' in __globals:
        return __globals['result']
    else:
        return []

def runnable_payloads(shell_obj):
    '''
    The payloads that can be run using this shell object.
    @return: A list with all runnable payloads.
    '''
    result = []
    payload_path = os.path.join('plugins','attack','payloads','payloads')
    
    for payload in os.listdir(payload_path):
        requirements = get_used_syscalls( os.path.join(payload_path, payload) )
        if can_run( shell_obj , requirements):
            result.append( payload.replace('.py', '') )
        
    return result


if __name__ == '__main__':
    payload_filename = 'payloads/test.py'
    
    requirements =  get_used_syscalls( payload_filename )
    
    #
    #   I define the shell object
    #
    class shell_class():
        def __init__(self):
            pass

        def read(self, foo):
            return 'Reading',foo

        def rexec(self, command):
            return 'Executing',foo
    
    s = shell_class()
    
    print can_run( s , requirements)
    
    exec_payload( s,  payload_filename)
