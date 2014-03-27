import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class running_honeypot(Payload):
    """
    This payload check if the server is a Honeypot or is running one.
    """
    def api_read(self):
        result = {}
        result['running_honeypot'] = False
        result['is_a_honeypot'] = False

        files = []
        files.append('/var/log/nepenthes.log')
        files.append('/etc/conf.d/mwcollectd')
        files.append('/opt/mwcollectd/lib/mwcollectd/log-file.so')
        files.append('/root/conf/mwcollectd.conf')
        files.append('/bin/mwcollectd')
        files.append('/usr/sbin/mwcollectd')
        files.append('/etc/init.d/mwcollectd')
        files.append('/etc/honeyd.conf')
        files.append('/etc/honeyd/red66.conf')
        files.append('/var/run/honeyd.pid')
        files.append('/etc/nepenthes/nepenthes.conf')

        def parse_cpu_info(cpu_info):
            processor = re.search('(?<=model name\t: )(.*)', cpu_info)
            if processor:
                return processor.group(1)
            else:
                return ''

        for file in files:
            if self.shell.read(file):
                result['running_honeypot'] = True

        if parse_cpu_info(self.shell.read('/proc/cpuinfo')) == 'UML':
            result['is_a_honeypot'] = True
        devices = self.shell.read('/proc/devices')
        if '60 cow' in devices or '90 ubd' in devices:
            result['is_a_honeypot'] = True
        if 'nodev\thostfs' in self.shell.read('/proc/filesystems'):
            result['is_a_honeypot'] = True

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            msg = 'Failed to verify if the remote host is running a honeypot.'
            return msg
        else:

            rows = []
            rows.append(['Honeypot', ])
            rows.append([])
            if api_result['running_honeypot']:
                rows.append(['Is running a Honeypot!', ])
            if api_result['is_a_honeypot']:
                rows.append(['Is a Honeypot!', ])
            if not api_result['running_honeypot'] and not api_result['is_a_honeypot']:
                rows.append(['No honeypot detected.', ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
