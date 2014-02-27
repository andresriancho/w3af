from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class domainname(Payload):
    """
    This payload shows server domain name.
    """
    def api_read(self):
        result = {}
        result['domain_name'] = ''

        domainname_content = self.shell.read(
            '/proc/sys/kernel/domainname')[:-1]
        if domainname_content:
            result['domain_name'] = domainname_content

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'Domain name not found.'
        else:
            rows = []
            rows.append(['Domain name', ])
            rows.append([])
            for domain in api_result.values():
                rows.append([domain, ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
