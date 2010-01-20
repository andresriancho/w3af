#REQUIRE_LINUX
#This payload shows TCP socket information
import re

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
    user = re.search('(\w*):\d*:(?<='+user+')', etc_passwd,  re.MULTILINE)
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

table = parse_tcp(open('/proc/net/tcp').read())

for list in table:
    list[0]=list[0].ljust(3)
    
    if list[1] != 'local_address':
        list[1] = str(dec_to_dotted_quad(int(split_ip(list[1])[0], 16)))
    list[1] = list[1].ljust(15)
    
    if list[2] != 'rem_address':
        list[2] = str(dec_to_dotted_quad(int(split_ip(list[2])[0] , 16)))
    list[2] = list[2].ljust(15)
    
    list[3] = list[3].ljust(2)
    list[4] = list[4].ljust(17)
    list[5] = list[5].ljust(11)
    list[6] = list[6].ljust(8)
    list[7] = list[7].ljust(8)

    if list[8] != 'uid':
        list[8] = get_username(open('/etc/passwd').read(), list[8])
    list[8] = list[8].ljust(9)
    list[9] = list[9].ljust(9)
    list[10] = list[10].ljust(9)
    result.append(str(" ".join(list)))
