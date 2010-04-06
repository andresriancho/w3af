import re
from plugins.attack.payloads.base_payload import base_payload

class apache_run_group(base_payload):
    '''
    '''
    def api_read(self):
        result = []
        groups = []

        def parse_group_envvars (envvars_file):
            user = re.search('(?<=APACHE_RUN_GROUP=)(.*)', envvars_file)
            if user:
                return user.group(1)
            else:
                return ''

        apache_dir = self.exec_payload('apache_config_directory')
        if apache_dir:
            for dir in apache_dir:
                groups.append(parse_group_envvars(self.shell.read(dir+'envvars')))
        #group.append(parse_group_envvars(open('/proc/PIDAPACHE/environ').read()))

        for group in groups:
            result.append(group)
        result = list(set(result))
        result = [p for p in result if p != '']
        return result
        
    def run_read(self):
        result = self.api_read()
        if result == [ ]:
            result.append('Apache Run Group not found.')
        return result





