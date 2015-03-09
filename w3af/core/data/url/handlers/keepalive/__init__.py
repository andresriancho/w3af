from .utils import debug, error, to_utf8_raw
from .http_response import HTTPResponse
from .connection_manager import ConnectionManager
from .connections import (ProxyHTTPConnection, ProxyHTTPSConnection,
                          HTTPConnection, HTTPSConnection)

from .handler import (KeepAliveHandler,
                      HTTPSHandler,
                      HTTPHandler,
                      URLTimeoutError)

# Max connections allowed per host
MAX_CONNECTIONS = 50

