import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class root_login_allowed(Payload):
    """
    This payload checks if root user is allowed to login on console.
    """
    def api_read(self):
        result = {}

        def parse_securetty(securetty):
            console = re.search('^console', securetty)
            if console:
                return console.group(1)
            else:
                return ''

        def parse_permit_root_login(config):
            match_obj = re.search('PermitRootLogin (yes|no)', config)
            if match_obj:
                return match_obj.group(1)
            else:
                return ''

        ssh_config_result = self.exec_payload('ssh_config_files')
        result['ssh_root_bruteforce'] = 'unknown'
        for config in ssh_config_result.values():
            ssh_allows = parse_permit_root_login(config)
            if ssh_allows == 'yes':
                result['ssh_root_bruteforce'] = True
                break
            elif ssh_allows == 'no':
                result['ssh_root_bruteforce'] = False
                break

        securetty = self.shell.read('/etc/securetty')
        if securetty:
            if parse_securetty(securetty):
                result['securetty_root_login'] = True
            else:
                result['securetty_root_login'] = False

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            msg = 'Failed to verify if root login is allowed, '
            msg += ' a SSH bruteforce attack might still be possible.'
            return msg
        else:

            rows = []
            rows.append(['Root login allowed', ])
            rows.append([])
            if api_result['ssh_attack']:
                rows.append(['A SSH Bruteforce attack is possible.', ])
            if api_result['root_login']:
                rows.append(['Root user is allowed to login on CONSOLE.', ])
            if not api_result['root_login'] and not api_result['ssh_attack']:
                rows.append(['Root user is not allowed to login through SSH nor console.', ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
