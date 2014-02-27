import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class cpu_info(Payload):
    """
    This payload shows CPU Model and Core info.
    """
    def api_read(self):
        result = {}

        def parse_cpu_info(cpu_info):
            processor = re.search('(?<=model name\t: )(.*)', cpu_info)
            if processor:
                processor_string = processor.group(1)
                splitted = processor_string.split(' ')
                splitted = [i for i in splitted if i != '']
                processor_string = ' '.join(splitted)
                return processor_string
            else:
                return ''

        def parse_cpu_cores(cpu_info):
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

        def parse_cpu_cores(iis6log):
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
        api_result = self.api_read()

        if not api_result:
            return 'No CPU information found.'
        else:
            rows = []
            rows.append(['Description', 'Value'])
            rows.append([])
            for name in api_result:
                rows.append([name, api_result[name]])

            result_table = table(rows)
            result_table.draw(80)
            return rows
