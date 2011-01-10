import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class route(base_payload):
    '''
    This payload shows the IP Routing Table.
    '''
    def api_read(self, parameters):
        result = {}
        result['route'] = []
        list = []

        def parse_route(net_route):
            new = []
            list = net_route.split(' ')
            list[0] = list[0]+list[1]
            list.remove(list[1])
            list = [i for i in list if i != '']
            for line in list:
                tmp = line.split('\t')
                tmp = [i for i in tmp if i !='']
                new.append(tmp)
            return new

        def dec_to_dotted_quad(n):
            d = 256 * 256 * 256
            q = []
            while d > 0:
                m,n = divmod(n,d)
                q.append(str(m))
                d = d/256
            q.reverse()
            return '.'.join(q)

        list = parse_route(self.shell.read('/proc/net/route'))
        for line in list:
            if len(line) > 7 and 'Iface' not in line:
                result['route'].append({'Iface':line[0][1:],\
                                        'Destination':str(dec_to_dotted_quad(int(line[1], 16))), \
                                        'Gateway':str(dec_to_dotted_quad(int(line[2], 16))), \
                                        'Mask':str(dec_to_dotted_quad(int(line[7], 16)))})
 
        return result
    
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result['route']:
            return 'Remote host routes could not be retrieved.'
        else:
            rows = []
            rows.append( ['Interface', 'Destination', 'Gateway', 'Mask'] ) 
            rows.append( [] )
            for a_route in api_result['route']:
                rows.append( [ a_route['Iface'],a_route['Destination'],a_route['Gateway'],a_route['Mask']] )

            result_table = table( rows )
            result_table.draw( 80 )                    

            return
        
