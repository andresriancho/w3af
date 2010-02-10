import re
from plugins.attack.payloads.base_payload import base_payload

class cpu_info(base_payload):
    '''
    This payload shows CPU Model and Core info.
    '''
    def run_read(self):
        result = []

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

        result.append(parse_cpu_info( self.shell.read('/proc/cpuinfo') ) \
        +' ['+parse_cpu_cores( self.shell.read('/proc/cpuinfo'))+' Cores]' )
        result = [p for p in result if p != '']
        if result == [ ]:
            result.append('CPU Info not found.')
        return result
