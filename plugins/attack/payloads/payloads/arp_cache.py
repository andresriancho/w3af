from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class arp_cache(base_payload):
    '''
    This payload shows the ARP CACHE
    '''
    def api_read(self, parameters):
        result = {}
        
        files = []
        files.append('/proc/net/arp')

        for file in files:
            content = self.shell.read(file)
            if content != '':
                for line in content.split('\n'):
                    splitted_line = line.split(' ')
                    splitted_line = [ i for i in splitted_line if i != '']
                    
                    try:
                        ip_address = splitted_line[0] 
                        hw_address = splitted_line[3]
                        device = splitted_line[5]
                    except:
                        pass
                    else:
                        result[ ip_address ] = (hw_address,device)
        
        return result
    
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result:
            return 'ARP cache not found.'
        else:
            rows = []
            rows.append( ['IP address', 'HW address', 'Device'] ) 
            rows.append( [] )
            for ip_address in api_result:
                hw_addr, device = api_result[ip_address]
                rows.append( [ip_address, hw_addr, device] )
            result_table = table( rows )
            result_table.draw( 80 )                    
            return
