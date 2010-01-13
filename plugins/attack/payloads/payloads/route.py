#REQUIRE_LINUX
import re
import socket

result = []


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

def parse_mask(net_route):
    destination = re.findall('^\w*\t\w*\t\w*\t\w*\t\w*\t\w*\t\w*\t(.*?)\s', net_route,  re.MULTILINE)
    if destination:
        return destination
    else:
        return ''

iface = parse_iface(open('/proc/net/route').read())
destination = parse_destination(open('/proc/net/route').read())
mask = parse_mask(open('/proc/net/route').read())

def dec_to_dotted_quad(n):
    d = 256 * 256 * 256
    q = []
    while d > 0:
        m,n = divmod(n,d)
        q.append(str(m))
        d = d/256
    q.reverse()
    return '.'.join(q)

destination = [ip for ip in destination if ip!='Destination']
for ip in destination:
        ip = str(dec_to_dotted_quad(int(ip, 16)))
        destination.append(ip)

