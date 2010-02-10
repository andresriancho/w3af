import re
from plugins.attack.payloads.base_payload import base_payload

#TODO:Read TCP and TCP6?

class udp(base_payload):
    '''
    This payload shows UDP socket information
    '''
    def run_read(self):
        result = []
        table = []

        def parse_udp(net_udp):
            new = []
            list = net_udp.split('\n')
            list = [i for i in list if i != '']
            for item in list:
                tmp = item.split(' ')
                tmp = [i for i in tmp if i !='']
                new.append(tmp)
            new = [i for i in new if i != '']
            return new

        def get_username(etc_passwd, user):
            user = re.search('(\w*):(\w*):\d*:'+user, etc_passwd,  re.MULTILINE)
            if user:
                return user.group(1)
            else:
                return ''

        def split_ip(ip):
            ipPort = [ip[:8], ip[9:]]
            return ipPort

        def dec_to_dotted_quad(n):
            d = 256 * 256 * 256
            q = []
            while d > 0:
                m,n = divmod(n,d)
                q.append(str(m))
                d = d/256
            q.reverse()
            return '.'.join(q)
        
        etc = self.shell.read('/etc/passwd')
        table = parse_udp(self.shell.read('/proc/net/udp'))
    
        for list in table:
            new = []
            list[0]=list[0].ljust(4)
            if list[1] != 'local_address':
                ip = split_ip(list[1])
                list[1] = str(dec_to_dotted_quad(int(ip[0], 16)))+':'+str(int(ip[1], 16))
            list[1] = list[1].ljust(25)

            if list[2] != 'rem_address':
                ip = split_ip(list[2])
                list[2] = str(dec_to_dotted_quad(int(ip[0] , 16)))+':'+str(int(ip[1], 16))
            list[2] = list[2].ljust(25)
            
            if list[7] == 'tm->when':
                list[7] = 'uid'
            
            if list[7] != 'uid':
                list[7] = get_username(etc, list[7])
            list[7] = list[7].ljust(10)
          
            new.append(list[0])
            new.append(list[1])
            new.append(list[2])
            new.append(list[3])
            new.append(list[7])
            new.append(list[11])
            result.append(str(" ".join(new)))
        if result == [ ]:
            result.append('UDP socket information not found.')
        return result
