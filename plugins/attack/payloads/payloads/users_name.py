import re
from plugins.attack.payloads.base_payload import base_payload

class users_name(base_payload):
    '''
    This payload shows users name parsing the /etc/passwd file
    '''
    def run_read(self):
        result = []
        users = []

        def parse_users_name( etc_passwd ):
            user = re.findall('^(.*?)\:', etc_passwd,  re.MULTILINE)
            if user:
                return user
            else:
                return ''

        for user in parse_users_name(self.shell.read('/etc/passwd')):
            result.append(str(user))
        
        return result
