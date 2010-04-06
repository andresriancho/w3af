#TODO: SELF ENVIRON NOT READABLE
import re
from plugins.attack.payloads.base_payload import base_payload

class current_user(base_payload):
    '''
    This payload shows current user on the system.
    '''
    def api_read(self):
        result = []

        def default_home( self_environ ):
            user = re.search('(?<=USER=)(.*?)\\x00', self_environ)
            if user:
                return user.group(1)
            else:
                return ''

        result.append(default_home( self.shell.read('/proc/self/environ')) )
        return result
    
    def run_read(self):
        result = self.api_read()
        if result == [ ]:
            result.append('Current user not found.')
        return result
