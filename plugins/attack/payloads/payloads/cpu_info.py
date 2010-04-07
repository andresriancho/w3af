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
                return processor.group(1)
            else:
                return ''

        def parse_cpu_cores( cpu_info ):
            cores = re.search('(?<=cpu cores\t: )(.*)', cpu_info)
            if cores:
                return cores.group(1)
            else:
                return ''

        content = self.shell.read('/proc/cpuinfo')
        if content:
            result['cpu_info'] = parse_cpu_info(content)
            result['cpu_cores'] = parse_cpu_cores(content)

        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        
        for k, v in hashmap.iteritems():
            k = k.replace('_', ' ')
            result.append(k.title()+': '+v)
        
        if result == [ ]:
            result.append('CPU Info not found.')
        return result
