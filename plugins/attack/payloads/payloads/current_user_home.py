#REQUIRE_LINUX
import re

result = []

def default_home( self_environ ):
    user = re.search('(?<=HOME=)(.*?)\\x00', self_environ)
    if user:
        return user.group(1)+'/'
    else:
        return ''

result.append(default_home( read( '/proc/self/environ') ) )
