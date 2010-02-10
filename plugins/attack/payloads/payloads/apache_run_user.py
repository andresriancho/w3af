import re
from plugins.attack.payloads.base_payload import base_payload

class apache_run_user(base_payload):
    '''
    '''
    def run_read(self):
        result = []
        users = []

        def parse_user_envvars (envvars_file):
            user = re.search('(?<=APACHE_RUN_USER=)(.*)', envvars_file)
            if user:
                return user.group(1)
            else:
                return ''

        apache_dir = self.exec_payload('apache_config_directory')
        if apache_dir:
            for dir in apache_dir:
                users.append(parse_user_envvars(self.shell.read(dir+'envvars')))

        #TODO: ROOT users.append(parse_user_envvars(open('/proc/PIDAPACHE/environ').read()))

        for user in users:
            result.append(user)

        result = list(set(result))
        result = [p for p in result if p != '']
        if result == [ ]:
            result.append('Apache Run User not found.')
        return result
