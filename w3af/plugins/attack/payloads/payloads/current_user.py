import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class current_user(Payload):
    """
    This payload shows current username & folder on the system.
    """
    def api_read(self):
        result = {}
        result['current'] = {}

        def default_user(self_environ):
            user = re.search('(?<=USER=)(.*?)\\x00', self_environ)
            if user:
                return user.group(1)
            else:
                return None

        def default_home(self_environ):
            user = re.search('(?<=HOME=)(.*?)\\x00', self_environ)
            if user:
                return user.group(1) + '/'
            else:
                return None

        self_environ = self.shell.read('/proc/self/environ')
        if self_environ:
            result['current'] = ({'user': default_user(self_environ),
                                  'home': default_home(self_environ)})

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result['current']:
            return 'Current user not found.'
        else:
            rows = []
            rows.append(['Current user'])
            rows.append([])
            for key_name in api_result:
                for user in api_result[key_name]:
                    rows.append([user, ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
