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
import copy

PAYLOAD_PATH= os.path.join('plugins','attack','payloads','payloads')

def get_used_syscalls( payload_name ):
    '''
    With functions I get the syscalls that are used by the payload.
    
    @parameter payload_name: The payload name that we want to analyze.
    @return: The list of syscalls that the payload needs.
    '''
    class payload_visitor(compiler.visitor.ExampleASTVisitor):
        def __init__(self):
            compiler.visitor.ExampleASTVisitor.__init__(self)
            self.defined_functions = []
            self.called_functions = []
            self.payload_dependencies = []
    
        def dispatch(self, node, *args):
            self.node = node
            meth = self._cache.get(node.__class__, None)
            className = node.__class__.__name__
            if meth is None:
                meth = getattr(self.visitor, 'visit' + className, 0)
                self._cache[node.__class__] = meth
            if self.VERBOSE > 1:
                print "dispatch", className, (meth and meth.__name__ or '')
            if meth:
                meth(node, *args)
            elif self.VERBOSE > 0:
                klass = node.__class__
                if not self.examples.has_key(klass):
                    self.examples[klass] = klass
                    print
                    print self.visitor
                    print klass
                    for attr in dir(node):
                        if attr[0] != '_':
                            print "\t", "%-12.12s" % attr, getattr(node, attr)
                    print
            return self.default(node, *args)
        
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
                if 'run_payload' == info.node.name:
                    #   The current payload calls another payload
                    self.payload_dependencies.append( info.args[0].value )
                    
                    # debug
                    #msg = payload_name + ' --> requires --> ' + info.args[0].value
                    #om.out.debug( msg )
                    
                elif not __builtins__.has_key(info.node.name):
                    self.called_functions.append( info.node.name )
                    
            except Exception,  e:
                pass

        def get_requirements(self):
            return list( set(self.called_functions) - set(self.defined_functions) )
            
        def get_payload_dependencies(self):
            return self.payload_dependencies

    #   Here I save the requirements for the initial payloads, and all the payloads that are called
    #   from that one. This is the final result.
    global_requirements = []
    
    #
    #   Parse the first payload. Remember that one payload can call many others, and those payloads
    #   can call even more.
    #
    ast = compiler.parseFile( payload_to_file(payload_name) )
    visitor = payload_visitor()
    result = compiler.visitor.walk(ast, visitor, walker=visitor, verbose=0 )
    global_requirements.extend( result.get_requirements() )
    
    #   Now I'll analyze each of the payloads called by the initial payload.
    for referenced_payload in result.get_payload_dependencies():
        #   I don't want to end up in a loop!
        #   TODO: 
        #       This only protects me from "direct loops", not from "long loops"
        #       Direct Loops:
        #           * A---> B---> A
        #       Long Loops:
        #           * A---> B---> C ---> A
        if referenced_payload != payload_name:
            global_requirements.extend( get_used_syscalls( referenced_payload) )
    
    #   Uniq
    global_requirements = list(set(global_requirements))
        
    return global_requirements


def payload_to_file( payload_name ):
    '''
    @parameter payload_name: The name of the payload.
    @return: The filename related to the payload.
    '''
    return os.path.join( PAYLOAD_PATH, payload_name + '.py' )
    
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

def get_unmet_requirements(shell_obj, requirements):
    '''
    @return: A list with the unmet dependencies.
    '''
    result = []
    available_functions = dir(shell_obj)
    available_functions.append('console')
    
    for name in requirements:
        if not name in available_functions:
            result.append(name)
    return result
    
def is_payload( function_name ):
    '''
    @return: True if the function_name is referencing a payload.
    '''
    return function_name in get_payload_list()
    
def exec_payload(shell_obj, payload_name):
    '''
    Now I execute the payload, by providing the function names that are in the shell_obj
    as "globals".
    
    @parameter shell_obj: The shell object instance.
    @parameter payload_name: The name of the payload I want to run.
    @return: The payload "result" variable.
    '''
    
    compiled = compiler.compile( file(payload_to_file(payload_name)).read() , payload_name, 'exec')
    
    def run_payload( name ):
        return exec_payload(shell_obj,  name)
    
    def create_fake_globals():
        #
        # Inject the syscalls provided by the exploit
        #
        __globals = {}
        for name in dir(shell_obj):
            __globals[name] = getattr(shell_obj, name)

        #
        # Inject the functions provided by the framework for debugging
        #
        __globals['console'] = getattr(om.out, 'console')
        
        #
        # Inject this function, that will allow me to run a payload from a payload
        #
        __globals['run_payload'] = run_payload
        
        return __globals
    
    __globals = create_fake_globals()
    
    try:
        exec compiled in __globals
    except Exception, e:
        #   Invalid payload...
        return ['The payload raised an exception: "' + str(e) + '".']
    else:
        #   Ok :)
        if 'result' in __globals:
            return __globals['result']
        else:
            return ['The payload returned an empty result.']

def runnable_payloads(shell_obj):
    '''
    The payloads that can be run using this shell object.
    @return: A list with all runnable payloads.
    '''
    result = []
    
    for payload_name in get_payload_list():
        requirements = get_used_syscalls( payload_name )
        if can_run( shell_obj , requirements):
            result.append( payload_name )
        
    return result

def get_payload_list():
    '''
    @return: A list of the payload names in the payloads directory.
    '''
    result = []
    
    for payload in os.listdir(PAYLOAD_PATH):
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
