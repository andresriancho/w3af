from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class users_name(base_payload):
    '''
    This payload shows users name
    '''
    def api_read(self):
        result = {}

        passwd = self.shell.read('/etc/passwd')
        if passwd:
            for line in passwd.split('\n'):
                if line.strip() != '':
                    splitted_line = line.split(':')
                    try:
                        user = splitted_line[0]
                        desc = splitted_line[-3]
                        directory = splitted_line[-2]
                        shell = splitted_line[-1]
                    except:
                        pass
                    else:
                        desc = desc.replace(',,,','')
                        if not directory.endswith('/'):
                            directory += '/'
                        result[user] = (directory,shell,desc)
        return result
    
    def run_read(self):
        api_result = self.api_read()
                
        if not api_result:
            return 'Users list not found.'
        else:
            rows = []
            rows.append( ['User', 'Home directory', 'Shell', 'Description'] )
            rows.append( [] )
            for username in api_result:
                home, shell, desc = api_result[username]
                rows.append( [username, home, shell, desc] )
                    
            result_table = table( rows )
            result_table.draw( 80 )
            return
