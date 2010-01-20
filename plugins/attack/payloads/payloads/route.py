#REQUIRE_LINUX
#This payload shows the IP Routing Table.
import re

result = []
list = []

def parse_route(net_route):
    new = []
    list = net_route.split(' ')
    list[0] = list[0]+list[1]
    list.pop(1)
    list = [i for i in list if i != '']
    for line in list:
        new.append(line.split('\t'))
    print new
    return new

list = parse_route(open('/proc/net/route').read())

def dec_to_dotted_quad(n):
    d = 256 * 256 * 256
    q = []
    while d > 0:
        m,n = divmod(n,d)
        q.append(str(m))
        d = d/256
    q.reverse()
    return '.'.join(q)

for list in result:
    if list[1] != 'Destination':
        list[1] = str(dec_to_dotted_quad(int(list[1], 16)))

    if list[2] != 'Gateway':
        list[2] = str(dec_to_dotted_quad(int(list[2], 16)))
    
    if list[7] != 'Mask':
        list[7] = str(dec_to_dotted_quad(int(list[7], 16)))


result.append('Destination'.ljust(20)+'Mask'.ljust(20)+'Iface'.ljust(20))
for dest in destination:
    i = destination.index(dest)
    result.append(destination.pop(i).ljust(20)+mask.pop(i).ljust(20)+iface.pop(i).ljust(20))
