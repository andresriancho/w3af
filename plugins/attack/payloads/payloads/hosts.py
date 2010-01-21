#REQUIRE_LINUX
import re

result = []
allow = []
deny = []
hosts = []

def parse_hosts (etc_hosts):
    hosts = re.findall('^(?!#)(.*?)$', etc_hosts, re.MULTILINE)
    if hosts:
        return hosts
    else:
        return ''

hosts = parse_hosts(read('/etc/hosts'))
allow = parse_hosts(read('/etc/hosts.allow'))
deny = parse_hosts(read('/etc/hosts.deny'))
#Resolv.conf?

result.append('Hosts:')
result.append(read('/etc/hosts'))

result.append('Hosts Allowed:')
result.append(read('/etc/hosts.allow'))

result.append('Hosts Denied:')
result.append(read('/etc/hosts.deny'))

result = [p for p in result if p != '']
