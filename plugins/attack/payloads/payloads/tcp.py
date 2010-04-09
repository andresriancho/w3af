import re
from plugins.attack.payloads.base_payload import base_payload

#TODO:Read TCP and TCP6?

class tcp(base_payload):
    '''
    This payload shows TCP socket information
    '''
    def api_read(self):
        result = {}
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
        
        etc = self.shell.read('/etc/passwd')
        table = parse_tcp(self.shell.read('/proc/net/tcp'))
    
        for list in table:
            if list[1] != 'local_address':
                ip = split_ip(list[1])
                list[1] = str(dec_to_dotted_quad(int(ip[0], 16)))+':'+str(int(ip[1], 16))
                
            if list[2] != 'rem_address':
                ip = split_ip(list[2])
                list[2] = str(dec_to_dotted_quad(int(ip[0] , 16)))+':'+str(int(ip[1], 16))
            
            if list[7] == 'tm->when':
                list[7] = 'uid'
            
            if list[7] != 'uid':
                list[7] = get_username(etc, list[7])
            
            if list[0] != 'sl':
                result[str(list[0].replace(':', ''))] = ({'local_address':list[1], 'rem_address':list[2], 'st':list[3],'uid':list[7], 'inode':list[11]})
            
        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('TCP Socket Information')
            result.append('sl'.ljust(3)+'local_address'.ljust(25)+'rem_address'.ljust(25)+\
                          'st'.ljust(4)+'uid'.ljust(13)+'inode'.ljust(20))
            for k, v in hashmap.iteritems():
                result.append(k.ljust(3)+v['local_address'].ljust(25)+v['rem_address'].ljust(25)+\
                              v['st'].ljust(4)+v['uid'].ljust(13)+v['inode'].ljust(20))

        if result == [ ]:
            result.append('TCP socket information not found.')
        return result
