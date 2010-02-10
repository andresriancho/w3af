import re
from plugins.attack.payloads.base_payload import base_payload

class hosts(base_payload):
    '''
    This payload shows the hosts allow and deny files.
    '''
    def run_read(self):
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

        hosts = parse_hosts(self.shell.read('/etc/hosts'))
        allow = parse_hosts(self.shell.read('/etc/hosts.allow'))
        deny = parse_hosts(self.shell.read('/etc/hosts.deny'))
        #Resolv.conf?

        result.append('Hosts:')
        result.append(self.shell.read('/etc/hosts'))

        result.append('Hosts Allowed:')
        result.append(self.shell.read('/etc/hosts.allow'))

        result.append('Hosts Denied:')
        result.append(self.shell.read('/etc/hosts.deny'))

        result = [p for p in result if p != '']
        if result == [ ]:
            result.append('Hosts files not found.')
        return result


