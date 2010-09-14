import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class apache_version(base_payload):
    '''
    This payload shows Apache Version
    '''
    def api_read(self, parameters):
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
        
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result['version']:
            return 'Apache version not found.'
        else:
            rows = []
            rows.append( ['Version',] ) 
            rows.append( [] )
            for key_name in api_result:
                for version in api_result[key_name]:
                    rows.append( [version,] )
            result_table = table( rows )
            result_table.draw( 80 )                    
            return

