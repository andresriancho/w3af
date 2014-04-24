import re

#URL_RE = ('((http|https):[A-Za-z0-9/](([A-Za-z0-9$_.+!*(),;/?:@&~=-])|%'
#    '[A-Fa-f0-9]{2})+(#([a-zA-Z0-9][a-zA-Z0-9$_.+!*(),;/?:@&~=%-]*))?)')
URL_RE = re.compile('((http|https)://([\w:@\-\./]*?)[^ \n\r\t"\'<>]*)', re.U)
