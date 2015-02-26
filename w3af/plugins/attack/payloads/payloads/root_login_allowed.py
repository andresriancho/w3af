import re

from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class root_login_allowed(Payload):
    """
    This payload checks if root user is allowed to login on console.
    """
    def api_read(self):
        result = {}

        ssh_config_result = self.exec_payload('ssh_config_files')
        result['ssh_root_bruteforce'] = 'unknown'

        for config in ssh_config_result.values():
            ssh_root_bruteforce = parse_permit_root_login(config)
            result['ssh_root_bruteforce'] = ssh_root_bruteforce
            if ssh_root_bruteforce:
                break

        securetty = self.shell.read('/etc/securetty')
        if securetty:
            result['securetty_root_login'] = parse_securetty(securetty)
        else:
            result['securetty_root_login'] = False

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            msg = 'Failed to verify if root login is allowed, a SSH bruteforce'\
                  ' attack might still be possible.'
            return msg
        else:

            rows = [['Root login allowed', ], []]

            if api_result['ssh_root_bruteforce']:
                rows.append(['A SSH Bruteforce attack is possible.', ])

            if api_result['securetty_root_login']:
                rows.append(['Root user is allowed to login on CONSOLE.', ])

            if not api_result['ssh_root_bruteforce'] and not api_result['securetty_root_login']:
                rows.append(['Root user is not allowed to login through SSH'
                             ' nor console.', ])

            result_table = table(rows)
            result_table.draw(80)
            return rows


def parse_securetty(securetty):
    console = re.search('^console', securetty)
    pts = re.search('^pts', securetty)
    return bool(console) or bool(pts)


def parse_permit_root_login(config):
    match_obj = re.search('PermitRootLogin (yes|no)', config)
    if match_obj is not None:
        return True if match_obj.group(1) == 'yes' else False

    return False
