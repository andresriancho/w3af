import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class udp(base_payload):
    '''
    This payload shows udp socket information
    '''
    def api_read(self, parameters):
        result = {}

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
        #TODO: Read UDP and udp6?
        parsed_info = parse_udp(self.shell.read('/proc/net/udp'))
    
        for parsed_line in parsed_info:
            try:
                if parsed_line[1] != 'local_address':
                    ip = split_ip(parsed_line[1])
                    parsed_line[1] = str(dec_to_dotted_quad(int(ip[0], 16)))+':'+str(int(ip[1], 16))
                    
                if parsed_line[2] != 'rem_address':
                    ip = split_ip(parsed_line[2])
                    parsed_line[2] = str(dec_to_dotted_quad(int(ip[0] , 16)))+':'+str(int(ip[1], 16))
                
                if parsed_line[7] == 'tm->when':
                    parsed_line[7] = 'uid'
                
                if parsed_line[7] != 'uid':
                    parsed_line[7] = get_username(etc, parsed_line[7])
                
                if parsed_line[0] != 'sl':
                    key = str(parsed_line[0].replace(':', ''))
                    result[ key ] = {'local_address':parsed_line[1], 'rem_address':parsed_line[2],\
                                     'st':parsed_line[3],'uid':parsed_line[7], 'inode':parsed_line[11] }
            except:
                pass
            
        return result
        
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result:
            return 'No UDP information was identified.'
        else:
            rows = []
            rows.append( ['Id', 'Local Address', 'Remote Address', 'Status', 'User', 'Inode'] ) 
            rows.append( [] )
            
            for key in api_result:
                local_address = api_result[key]['local_address']
                rem_address = api_result[key]['rem_address']
                st = api_result[key]['st']
                uid = api_result[key]['uid']
                inode = api_result[key]['inode']
                
                rows.append( [key, local_address, rem_address, st, uid, inode] )
                
            result_table = table( rows )
            result_table.draw( 80 )                    
            return
