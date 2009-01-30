import glob,sys

success=False
in_ironpython="IronPython" in sys.version

if in_ironpython:
    try:
        from ironpython_console import *
        success=True
    except ImportError:
        raise
else:
    try:
        from console import *
        success=True
    except ImportError:
        pass


if not success:
    raise ImportError("Could not find a console implementation for your platform")
