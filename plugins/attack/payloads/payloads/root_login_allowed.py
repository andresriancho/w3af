import re
import core.data.kb.knowledgeBase as kb
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class root_login_allowed(base_payload):
    '''
    This payload checks if root user is allowed to login on console.
    '''
    def api_read(self, parameters):
        result = {}

        def parse_securetty( securetty ):
            console = re.search('^console', securetty)
            if console:
                return console.group(1)
            else:
                return ''

        def parse_permit_root_login(config):
            condition = re.findall('(?<=PermitRootLogin )(.*)', config)
            if condition:
                return condition.group(1)
            else:
                return ''

        ssh_string = ''
        ssh_config_result = self.exec_payload('ssh_config_files')
        for config in ssh_config_result:
            if parse_permit_root_login(config) == 'yes':
                result['ssh_attack'] = True
            elif parse_permit_root_login(config) == 'no':
                result['ssh_attack'] = False
            else:
                result['ssh_attack'] = ''

        securetty = self.shell.read('/etc/securetty')
        if securetty:
            if parse_securetty(securetty):
                result['root_login'] = True
            else:
                result['root_login'] = False

        return result
    
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result:
            msg = 'Failed to verify if root login is allowed, '
            msg += ' a SSH bruteforce attack might still be possible.'
            return msg
        else:
            
            rows = []
            rows.append( ['Root login allowed',] ) 
            rows.append( [] )
            if api_result['ssh_attack']:
                rows.append( ['A SSH Bruteforce attack is possible.',] )
            if api_result['root_login']:
                rows.append( ['Root user is allowed to login on CONSOLE.',] )
            if not api_result['root_login'] and not api_result['ssh_attack']:
                rows.append( ['Root user is not allowed to login through SSH nor console.',] )
                
            result_table = table( rows )
            result_table.draw( 80 )                    
            return
        
