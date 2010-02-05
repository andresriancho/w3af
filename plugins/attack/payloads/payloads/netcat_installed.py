#REQUIRE_LINUX
#This payload verifies if Netcat is installed and supports "-e"

result = []
files = []

files.append('/bin/netcat')
files.append('/etc/alternative/netcat')
files.append('/bin/nc')

installed = 'Netcat is not installed'
support = 'without "-e" support !'
for file in files:
    file_content = read(file)
    if file_content:
        installed = 'Netcat is installed'
        if '-e filename' in file_content:
            support = 'with -e Support !'

result.append(installed+' '+support)
    
