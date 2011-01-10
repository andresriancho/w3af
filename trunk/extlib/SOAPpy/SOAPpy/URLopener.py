"""Provide a class for loading data from URL's that handles basic
authentication"""

ident = '$Id: URLopener.py,v 1.2 2004/01/31 04:20:06 warnes Exp $'
from version import __version__

from Config import Config
from urllib import FancyURLopener

class URLopener(FancyURLopener):

    username = None
    passwd = None


    def __init__(self, username=None, passwd=None, *args, **kw):
        FancyURLopener.__init__( self, *args, **kw)
        self.username = username
        self.passwd = passwd


    def prompt_user_passwd(self, host, realm):
       return self.username, self.passwd
