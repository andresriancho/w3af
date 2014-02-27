import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class kernel_version(Payload):
    """
    This payload shows Kernel version
    """
    def api_read(self):
        result = {}
        result['kernel_version'] = ''

        paths = []

        def parse_proc_version(proc_version):
            version = re.search('(?<=Linux version ).*?\)', proc_version)
            if version:
                return version.group(0)
            else:
                return ''

        def parse_sched_debug(sched_debug):
            version = re.search(
                '(?<=Sched Debug Version: )(v\d\.\d\d, )(.*)', sched_debug)
            if version:
                return version.group(2)
            else:
                return ''

        paths.append(parse_proc_version(self.shell.read('/proc/version')))
        paths.append(self.shell.read('/proc/sys/kernel/osrelease')[:-1])
        paths.append(parse_sched_debug(self.shell.read('/proc/sched_debug')))

        longest = ''
        for version in paths:
            if len(version) > len(longest):
                longest = version
        if longest:
            result['kernel_version'] = longest

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result['kernel_version']:
            return 'Failed to identify kernel version.'
        else:
            rows = []
            rows.append(['Kernel version', ])
            rows.append([])
            rows.append([api_result['kernel_version'], ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
