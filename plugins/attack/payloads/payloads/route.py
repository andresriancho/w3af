#REQUIRE_LINUX
import re

result = []
destination = []
gateway = []
mask = []

def parse_iface(net_route):
    iface = re.findall('^(.*?)\t', net_route,  re.MULTILINE)
    if iface:
        return iface
    else:
        return ''

def parse_destination(net_route):
    destination = re.findall('^\w*\t(.*?)\t', net_route,  re.MULTILINE)
    if destination:
        return destination
    else:
        return ''

def parse_gateway(net_route):
    gateway = re.findall('^\w*\t\w*\t(.*?)\t', net_route,  re.MULTILINE)
    if gateway:
        return gateway
    else:
        return ''

def parse_mask(net_route):
    mask= re.findall('^\w*\t\w*\t\w*\t\w*\t\w*\t\w*\t\w*\t(.*?)\s', net_route,  re.MULTILINE)
    if mask:
        return mask
    else:
        return ''

iface = parse_iface(read('/proc/net/route'))
destination = parse_destination(read('/proc/net/route'))
gateway = parse_gateway(read('/proc/net/route'))
mask = parse_mask(read('/proc/net/route'))

def dec_to_dotted_quad(n):
    d = 256 * 256 * 256
    q = []
    while d > 0:
        m,n = divmod(n,d)
        q.append(str(m))
        d = d/256
    q.reverse()
    return '.'.join(q)

destination = [ip for ip in destination if ip != 'Destination']
for ip in destination:
    ip = str(dec_to_dotted_quad(int(ip, 16)))

gateway = [id for id in gateway if id != 'Gateway']
#TODO: Translate correctly HEX-ASCII

mask = [ip for ip in mask if ip != 'Mask']
for ip in mask:
    ip = str(dec_to_dotted_quad(int(ip, 16)))

result.append('Destination'.ljust(20)+'Mask'.ljust(20)+'Iface'.ljust(20))
for dest in destination:
    i = destination.index(dest)
    result.append(destination.pop(i).ljust(20)+mask.pop(i).ljust(20)+iface.pop(i).ljust(20))
