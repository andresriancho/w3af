"""
Facade that hides the differences between the SOAPpy and SOAP.py
libraries, so that google.py doesn't have to deal with them.

@author:     Brian Landers <brian@bluecoat93.org>
@license:    Python
@version:    0.5.4
"""

import warnings
from distutils.version import LooseVersion

__author__    = "Brian Landers <brian@bluecoat93.org>"
__version__ = "0.6"
__license__ = "Python"

#
# Wrapper around the python 'warnings' facility
#
def warn( message, level=RuntimeWarning ):
    warnings.warn( message, level, stacklevel=3 )
    
# We can't use older version of SOAPpy, due to bugs that break the Google API
minSOAPpyVersion = "0.11.3"

#
# Try loading SOAPpy first.  If that fails, fall back to the old SOAP.py
#
SOAPpy = None
try:
    import SOAPpy
    from SOAPpy import SOAPProxy, Types
    
    if LooseVersion( minSOAPpyVersion ) > \
       LooseVersion( SOAPpy.version.__version__ ):
       
        warn( "Versions of SOAPpy before %s have known bugs that prevent " +
              "PyGoogle from functioning." % minSOAPpyVersion )
        raise ImportError
        
except ImportError:
    warn( "SOAPpy not imported. Trying legacy SOAP.py.",
          DeprecationWarning )
    try:
        import SOAP
    except ImportError:
        raise RuntimeError( "Unable to find SOAPpy or SOAP. Can't continue.\n" )

#
# Constants that differ between the modules
#
if SOAPpy:
    false      = Types.booleanType(0)
    true       = Types.booleanType(1)
    structType = Types.structType
    faultType  = Types.faultType
else:
    false      = SOAP.booleanType(0)
    true       = SOAP.booleanType(1)
    structType = SOAP.structType
    faultType  = SOAP.faultType

#
# Get a SOAP Proxy object in the correct way for the module we're using
#
def getProxy( url, namespace, http_proxy ):    
    if SOAPpy:
        return SOAPProxy( url,
                          namespace  = namespace,
                          http_proxy = http_proxy )
    
    else:
        return SOAP.SOAPProxy( url,
                               namespace  = namespace,
                               http_proxy = http_proxy )

#
# Convert an object to a dictionary in the proper way for the module
# we're using for SOAP
#
def toDict( obj ):
    if SOAPpy:
        return obj._asdict()
    else:
        return obj._asdict
