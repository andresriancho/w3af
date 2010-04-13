import re
import core.data.kb.knowledgeBase as kb
from plugins.attack.payloads.base_payload import base_payload

class running_honeypot(base_payload):
    '''
    This payload check if the server is a Honeypot or is running one.
    '''
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

        def parse_cpu_info( cpu_info ):
            processor = re.search('(?<=model name\t: )(.*)', cpu_info)
            if processor:
                return processor.group(1)
            else:
                return ''
        
        for file in files:
            if self.shell.read(file):
                result['running_honeypot'] = True
        

        if parse_cpu_info(self.shell.read('/proc/cpuinfo')) == 'UML':
            result['is_a_honeypot']  = True
        devices = self.shell.read('/proc/devices')
        if '60 cow' in devices or '90 ubd' in devices:
            result['is_a_honeypot'] = True
        if 'nodev\thostfs' in self.shell.read('/proc/filesystems'):
            result['is_a_honeypot'] = True
        
        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        
        if hashmap:
                if hashmap['running_honeypot']:
                   result.append('Is running a Honeypot !!')
                else:
                    result.append('Is NOT running a Honeypot')
                if hashmap['is_a_honeypot']:
                   result.append('Is a Honeypot !!!')
                else:
                    result.append('Is NOT a Honeypot.')

        return result
