import re
from plugins.attack.payloads.base_payload import base_payload

#TODO: Perform more testing
class apache_run_group(base_payload):
    '''
    Get apache process group.
    '''
    def api_read(self):
        result = {}
        result['apache_run_group'] = []
        groups = []

        def parse_group_envvars (envvars_file):
            user = re.search('(?<=APACHE_RUN_GROUP=)(.*)', envvars_file)
            if user:
                return user.group(1)
            else:
                return ''

        apache_dir = self.exec_payload('apache_config_directory')['apache_directory']


        if apache_dir:
            for dir in apache_dir:
                groups.append(parse_group_envvars(self.shell.read(dir+'envvars')))
        #group.append(parse_group_envvars(open('/proc/PIDAPACHE/environ').read()))
        
        groups = list(set(groups))
        groups= [p for p in groups if p != '']
        
        for group in groups:
            result['apache_run_group'].append(group)
            
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
            result.append('Apache Run Group not found.')
        return result





