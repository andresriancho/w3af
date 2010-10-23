from plugins.attack.payloads.base_payload import base_payload
import core.controllers.outputManager as om
from core.controllers.vdaemon.vdFactory import getVirtualDaemon
from core.controllers.w3afException import w3afException


class metasploit(base_payload):
    '''
    This payload interacts with the metasploit framework.
    '''
    def api_execute(self, parameters):
        try:
            vd = getVirtualDaemon(self.shell.execute)
        except w3afException, w3:
            return 'Error, %s' % w3
        else:
            vd.run( parameters )
            return 'Successfully started the virtual daemon.'
    
    def run_execute(self, parameters):
        api_result = self.api_execute(parameters)
        return api_result

