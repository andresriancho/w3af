import re

URL_RE = re.compile(r'((http|https)://([\w:@\-./]*?)[^ \0\n\r\t"\'<>]*)', re.U | re.I)

RELATIVE_URL_RE = re.compile(
    r'((:?[/]{1,2}[\w\-~.%]+)+'
    # extension with two to four characters
    r'\.\w{2,4}'
    # query string
    r'(((\?)'
    # query string parameter
    r'([\w\-~.%]*=[\w\-~.%]*))'
    # ampersand and more parameters
    r'((&)([\w\-~.%]*=[\w\-~.%]*))*)?)', re.U | re.I)
