import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class hostname(Payload):
    """
    This payload shows the server hostname
    """
    def api_read(self):
        result = {}
        result['hostname'] = []

        values = []
        values.append(self.shell.read('/etc/hostname')[:-1])
        values.append(self.shell.read('/proc/sys/kernel/hostname')[:-1])

        values = list(set(values))
        values = [p for p in values if p != '']

        result['hostname'] = values

        return result

    def api_win_read(self):
        result = {}
        result['hostname'] = []

        def parse_iis6_log(iis6_log):
            root1 = re.findall('(?<=OC_COMPLETE_INSTALLATION:m_csMachineName=)(.*?) ', iis6_log, re.MULTILINE)
            root2 = re.findall('(?<=OC_QUEUE_FILE_OPS:m_csMachineName=)(.*?) ',
                               iis6_log, re.MULTILINE)
            root3 = re.findall('(?<=OC_COMPLETE_INSTALLATION:m_csMachineName=)(.*?) ', iis6_log, re.MULTILINE)
            root = root1 + root2 + root3
            if root:
                return root
            else:
                return []

        def parse_certocm_log(certocm_log):
            hostname = re.search(
                '(?<=Set Directory Security:\\)(.*?)\\', certocm_log)
            if hostname:
                return '\\' + hostname.group(0)
            else:
                return ''

        hostnames = parse_iis6_log(self.shell.read('/windows/iis6.log'))
        hostnames += parse_certocm_log(self.shell.read('/windows/certocm.log'))
        hostnames = list(set(hostnames))
        hostnames = [p for p in hostnames if p != '']
        result['hostname'] = hostnames
        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result['hostname']:
            return 'Host name could not be identified.'
        else:
            rows = []
            rows.append(['Hostname', ])
            rows.append([])
            for hostname in api_result['hostname']:
                rows.append([hostname, ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
