import re
from plugins.attack.payloads.base_payload import base_payload

#TODO:Read TCP and TCP6?
#TODO:Support UDP


class tcp(base_payload):
    '''
    This payload shows TCP socket information
    '''
    def run_read(self):
        result = []
        table = []

        def parse_tcp(net_tcp):
            new = []
            list = net_tcp.split('\n')
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
        etc = read('/etc/passwd')
        table = parse_tcp(self.shell.read('/proc/net/tcp'))
        for list in table:
            print list
            new = []
            list[0]=list[0].ljust(3)
            if list[1] != 'local_address':
                print table[2]
                ip = split_ip(list[1])
                list[1] = str(dec_to_dotted_quad(int(ip[0], 16)))+':'+str(int(ip[1], 16))
            list[1] = list[1].ljust(25)

            if list[2] != 'rem_address':
                ip = split_ip(list[2])
                list[2] = str(dec_to_dotted_quad(int(ip[0] , 16)))+':'+str(int(ip[2], 16))
                print 'hola'
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
        return result
