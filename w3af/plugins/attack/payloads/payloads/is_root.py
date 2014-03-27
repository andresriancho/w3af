from w3af.plugins.attack.payloads.base_payload import Payload


class is_root(Payload):
    """
    Return True if the remote user has root privileges.
    """
    def api_read(self):

        shadow = self.shell.read('/etc/shadow')
        return 'root' in shadow

    def run_read(self):
        api_result = self.api_read()

        if api_result:
            return 'The remote syscalls are run as root.'
        else:
            return 'The remote syscalls are NOT run as root.'
