import re
from plugins.attack.payloads.base_payload import base_payload

class route(base_payload):
    '''
    This payload shows the IP Routing Table.
    '''
    def run_read(self):
        result = []
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
        result.append('Iface'.ljust(20)+'Destination'.ljust(20)+'Gateway'.ljust(20)+'Mask'.ljust(20))
        for line in list:
            if len(line) > 7 and 'Iface' not in line:
                new = line[0][1:].ljust(20)+\
                str(dec_to_dotted_quad(int(line[1], 16))).ljust(20)+\
                str(dec_to_dotted_quad(int(line[2], 16))).ljust(20)+\
                str(dec_to_dotted_quad(int(line[7], 16))).ljust(20)
                result.append(new)
        if result == [ ]:
            result.append('Route information not found.')
        return result
