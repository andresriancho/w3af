import re
import core.data.kb.knowledgeBase as kb
from plugins.attack.payloads.base_payload import base_payload

class root_login_allowed(base_payload):
    '''
    This payload checks if root user is allowed to login on console.
    '''
    def api_read(self):
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
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        
        if hashmap:
            if hashmap['ssh_attack']:
                result.append('A SSH Bruteforce attack is possible.')
            else:
                result.append('A SSH Bruteforce attack is not possible.')
            if hashmap['root_login']:
                result.append('Root user is allowed to login on CONSOLE.')
            else:
                result.append('Root user is NOT allowed to login on CONSOLE.')
        
        if result == [ ]:
            result.append('Cant check if root login is allowed. A SSH Bruteforce attack might be possible')
        return result
