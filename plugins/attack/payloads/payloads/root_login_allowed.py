import re
import core.data.kb.knowledgeBase as kb
from plugins.attack.payloads.base_payload import base_payload

class root_login_allowed(base_payload):
    '''
    This payload checks if root user is allowed to login on console.
    '''
    def api_read(self):
        result = []

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
                ssh_string = 'A SSH Bruteforce attack is posible.'
            elif parse_permit_root_login(config) == 'no':
                ssh_string = 'A SSH Bruteforce attack is NOT posible.'
            else:
                ssh_string = 'A SSH Bruteforce attack MIGHT be posible.'

        securetty = read('/etc/securetty')
        if securetty:
            if parse_securetty(securetty):
                result.append('Root user is allowed to login on CONSOLE. '+ssh_string)
            else:
                result.append('Root user is not allowed to login on CONSOLE. '+ssh_string)

        return result
    
    def run_read(self):
        result = self.api_read()
        if result == [ ]:
            result.append('Cant check if root login is allowed.')
        return result
