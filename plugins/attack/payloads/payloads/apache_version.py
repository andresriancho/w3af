import re
from plugins.attack.payloads.base_payload import base_payload

class apache_version(base_payload):
    '''
    This payload shows Apache distributed configuration files (.htaccess & .htpasswd)
    '''
    def api_read(self):
        result = []

        def parse_apache_binary (binary):
            version = re.search('(?<=/build/buildd/)(.*?)/',  binary)
            version2 = re.search('(?<=Apache)/(\d\.\d\.\d*)(.*?) ',  binary)
            if version and version2:
                return [version.group(1), version2.group(1)]
            elif version:
                return [version.group(1)]
            elif version2:
                return [version.group(1)]
            else:
                return ''

        for version in parse_apache_binary(self.shell.read('/usr/sbin/apache2')):
            result.append(version)

        for version in parse_apache_binary(self.shell.read('/usr/sbin/httpd')):
            result.append(version)

        result = list(set(result))
        result = [p for p in result if p != '']
        return result
        
    def run_read(self):
        result = self.api_read()
        if result == [ ]:
            result.append('Apache version not found.')
        return result
        
