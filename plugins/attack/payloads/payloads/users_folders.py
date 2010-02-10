import re
from plugins.attack.payloads.base_payload import base_payload

class users_folders(base_payload):
    '''
    This payload shows folders assosiated with every user on the system.
    '''
    def run_read(self):
                
        result = []
        users = []

        def parse_users_folders( etc_passwd ):
            user = re.findall('(?<=/)(.*?)\:', etc_passwd)
            if user:
                return user
            else:
                return ''

        passwd = self.shell.read('/etc/passwd')
        if passwd:
            for user in parse_users_folders(passwd):
                result.append('/'+str(user)+'/')
           
        if result == [ ]:
            result.append('Users folders not found.')
        
        return result
