import re
from plugins.attack.payloads.base_payload import base_payload

class apache_version(base_payload):
    '''
    This payload shows Apache Version
    '''
    def api_read(self):
        result = {}
        result['version'] = []

        def parse_apache_binary (binary):
            version = re.search('(?<=/build/buildd/)(.*?)/',  binary)
            version2 = re.search('(?<=Apache)/(\d\.\d\.\d*)(.*?) ',  binary)
            if version and version2:
                return [version.group(1), version2.group(1)]
            elif version:
                return [version.group(1)]
            elif version2:
                return [version2.group(1)]
            else:
                return ''

        for version in parse_apache_binary(self.shell.read('/usr/sbin/apache2')):
            result['version'].append(version)

        for version in parse_apache_binary(self.shell.read('/usr/sbin/httpd')):
            result['version'].append(version)

        result['version'] = list(set(result['version']))
        result['version'] = [p for p in result['version'] if p != '']

        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        
        for version in hashmap['version']:
            result.append('Apache Version: '+version)
        
        if result == [ ]:
            result.append('Apache version not found.')
        return result
        
