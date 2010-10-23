import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class portscan(base_payload):
    '''
    This payload portscans a given host or IP range.
    '''
    
    def api_is_open_port(self, ip_address, port_list):
        '''
        If I have a way of telling if a port is open or not, for example
        using PHP's include() error messages, then I can perform a portscan
        by doing something similar to:
        
        for port in port_list:
            open = self.shell.is_open_port( host, port )
            if open:
                report_open( port )
        '''
        result = {}
        result[ip_address] = []
        
        for port in port_list:
            is_open = self.shell.is_open_port( ip_address, port )
            if is_open:
                result[ ip_address ].append( port )
        
        return result


    def run_is_open_port(self, parameters):
        
        default_ports = ['21','22','25','80','443','3306']
        
        if len(parameters) < 1:
            msg = 'Usage: portscan <ip-address or domain> [port-list]\n'
            msg += 'If port-list not specified, the following is used: %s' % ','.join(default_ports)
            return msg
        
        ip_address = parameters[0]
        
        if len(parameters) == 2:
            port_list = ''.join( parameters[1:] )
            port_list = port_list.split(',')
            port_list = [port.strip() for port in port_list]
            port_list = [port for port in port_list if port.isdigit()]
        else:
            port_list = default_ports
        
        api_result = self.api_is_open_port( ip_address, port_list )
                
        if not api_result:
            return 'No open ports were found'
        else:
            rows = []
            rows.append( ['Host','Open TCP ports'] )
            rows.append( [] )
            for host in api_result:
                port_list = '\n'.join( [str(port) for port in api_result[host]] )
                rows.append( [host, port_list ] )
                    
            result_table = table( rows )
            result_table.draw( 80 )
            return
        