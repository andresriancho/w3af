#REQUIRE_LINUX
import re

result = []

def default_home( self_environ ):
    user = re.search('(?<=HOME=)(.*?)\\x00', self_environ)
    return user.group(1)+'/'

result.append(default_home( read( '/proc/self/environ') ) )
