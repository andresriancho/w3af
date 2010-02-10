import re
import core.data.kb.knowledgeBase as kb
from plugins.attack.payloads.base_payload import base_payload

class running_honeypot(base_payload):
    '''
    This payload check if the server is  a Honeypot
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

        condition = False
        if parse_cpu_info(read('/proc/cpuinfo')) == 'UML':
            condition = True
        if '60 cow' in read('/proc/devices'):
            condition = True
        if '90 ubd' in read('/proc/devices'):
            condition = True
        if 'nodev\thostfs' in read('/proc/filesystems'):
            condition = True
        
        return result
