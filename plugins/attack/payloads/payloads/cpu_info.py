import re
from plugins.attack.payloads.base_payload import base_payload

class cpu_info(base_payload):
    '''
    This payload shows CPU Model and Core info.
    '''
    def api_read(self):
        result = {}

        def parse_cpu_info( cpu_info ):
            processor = re.search('(?<=model name\t: )(.*)', cpu_info)
            if processor:
                processor_string = processor.group(1)
                splitted = processor_string.split(' ')
                splitted = [ i for i in splitted if i != '']
                processor_string = ' '.join(splitted)
                return processor_string
            else:
                return ''

        def parse_cpu_cores( cpu_info ):
            cores = re.search('(?<=cpu cores\t: )(.*)', cpu_info)
            if cores:
                return cores.group(1)
            else:
                return '1'

        content = self.shell.read('/proc/cpuinfo')
        if content:
            result['cpu_info'] = parse_cpu_info(content)
            result['cpu_cores'] = parse_cpu_cores(content)

        return result
    
    def api_win_read(self):
        result = {}
        
        def parse_cpu_cores( iis6log ):
            cores = re.search('(?<=m_dwNumberOfProcessors=)(.*)', iis6log)
            if cores:
                return cores.group(1)
            else:
                return ''
        
        def parse_arch(iis6log):
            arch = re.search('(?<=m_csPlatform=)(.*)', iis6log)
            if arch:
                return arch.group(1)
            else:
                return ''
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        
        for k, v in hashmap.iteritems():
            k = k.replace('_', ' ')
            result.append(k.title()+': '+v)
        
        if result == [ ]:
            result.append('CPU Info not found.')
        return result
