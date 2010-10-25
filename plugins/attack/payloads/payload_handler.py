'''
payload_handler.py

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

import os
import sys

PAYLOAD_PATH= os.path.join('plugins','attack','payloads','payloads')


def payload_to_file( payload_name ):
    '''
    @parameter payload_name: The name of the payload.
    @return: The filename related to the payload.
    '''
    return os.path.join( PAYLOAD_PATH, payload_name + '.py' )
    
def is_payload( function_name ):
    '''
    @return: True if the function_name is referencing a payload.
    '''
    return function_name in get_payload_list()
    
def exec_payload(shell_obj, payload_name, parameters=[], use_api=False):
    '''
    Now I execute the payload, by providing the shell_obj.
    
    @param shell_obj: The shell object instance where I get the syscalls from.
                      If this is set to None, the handler will choose a shell from
                      the KB that provide the necessary syscalls. 
    @param payload_name: The name of the payload I want to run.
    @param parameters: A list with the parameters (strings) the user typed. 
    @use_api: Indicates if I need to use the API or not in this run. This is True when
                    exec_payload is called from base_payload.exec_payload()
                    
    @return: The payload result.
    '''
    if shell_obj is None:
        #
        #    I have to go to the KB, and filter the shell objects that are available there
        #    using the syscalls they provide and the syscalls I need.
        #
        
        #    The import needs to be here, don't ask why :P
        import core.data.kb.knowledgeBase as kb
        
        available_shells = kb.kb.getAllShells()
        for shell in available_shells:
            print shell
            if payload_name in runnable_payloads( shell ):
                shell_obj = shell
                break
    
    #
    #    Now that I have everything ready, lets run the payload
    #
    payload_inst = get_payload_instance(payload_name, shell_obj)
    if use_api:
        result = payload_inst.run_api(parameters)
    else:
        result = payload_inst.run(parameters)
    return result
    
def runnable_payloads(shell_obj):
    '''
    The payloads that can be run using this shell object.
    
    @return: A list with all runnable payload names.
    '''
    result = []
    
    for payload_name in get_payload_list():
        payload = get_payload_instance( payload_name, shell_obj )
        if payload.can_run():
            result.append( payload_name )
        
    return result

def get_payload_instance( payload_name,  shell_obj):
    '''
    @return: A payload instance.
    '''
    name = '.'.join( ['plugins','attack','payloads','payloads', payload_name] )
    __import__( name )
    module = sys.modules[name]
    klass = getattr( module , payload_name )
    return apply( klass, (shell_obj, ))

def get_payload_list():
    '''
    @return: A list of the payload names in the payloads directory.
    '''
    result = []
    py_list = [x for x in os.listdir(PAYLOAD_PATH) if x.endswith('.py') and x != '__init__.py']
    for p in py_list:
        p = p.replace('.py', '')
        result.append( p )
    
    return result
    
if __name__ == '__main__':
    print get_payload_instance('hosts', 'a')
