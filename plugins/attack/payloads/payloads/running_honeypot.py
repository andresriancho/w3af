import re
import core.data.kb.knowledgeBase as kb
from plugins.attack.payloads.base_payload import base_payload

class running_honeypot(base_payload):
    '''
    This payload check if the server is a Honeypot or is running one.
    '''
    def run_read(self):
        result = []

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

        def parse_cpu_info( cpu_info ):
            processor = re.search('(?<=model name\t: )(.*)', cpu_info)
            if processor:
                return processor.group(1)
            else:
                return ''
        
        running_honeypot = 'Is NOT running Honeypots'
        for file in files:
            if self.shell.read(file):
                running_honeypot = 'Is running Honeypots !!'
        
        is_a_honeypot = 'Is NOT a Honeypot'
        if parse_cpu_info(self.shell.read('/proc/cpuinfo')) == 'UML':
            is_a_honeypot = 'Is a Honeypot !'
        devices = self.shell.read('/proc/devices')
        if '60 cow' in devices or '90 ubd' in devices:
            is_a_honeypot = 'Is a Honeypot !'
        if 'nodev\thostfs' in self.shell.read('/proc/filesystems'):
            is_a_honeypot = 'Is a Honeypot !'
        
        result.append(running_honeypot+'. '+is_a_honeypot)

        return result
