#REQUIRE_LINUX
#This payload shows the IP Routing Table.
#FIXME
import re

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

list = parse_route(open('/proc/net/route').read())

for line in list:
    new = line[0].ljust(20)+line[1].ljust(20)+line[2].ljust(20)+line[7].ljust(20)
    result.append(new)

def dec_to_dotted_quad(n):
    d = 256 * 256 * 256
    q = []
    while d > 0:
        m,n = divmod(n,d)
        q.append(str(m))
        d = d/256
    q.reverse()
    return '.'.join(q)

#for list in result:
    #if list[1] != 'Destination':
     #   list[1] = str(dec_to_dotted_quad(int(list[1], 16)))

    #if list[2] != 'Gateway':
    #    list[2] = str(dec_to_dotted_quad(int(list[2], 16)))
    
    #if list[7] != 'Mask':
     #   list[7] = str(dec_to_dotted_quad(int(list[7], 16)))


result.append('Destination'.ljust(20)+'Mask'.ljust(20)+'Iface'.ljust(20))
for dest in destination:
    i = destination.index(dest)
    result.append(str(' '.join(destination.pop(i).ljust(20)+mask.pop(i).ljust(20)+iface.pop(i).ljust(20))))
