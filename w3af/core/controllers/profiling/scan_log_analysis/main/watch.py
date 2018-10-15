import sys
import time

from utils.utils import clear_screen
from .main import *


def watch(scan_log_filename, scan, function_name):
    scan.seek(0)

    while True:
        try:
            # Hack me here
            output = globals()[function_name](scan_log_filename, scan)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception, e:
            print('Exception: %s' % e)
            sys.exit(1)
        else:
            if output is not None:
                output.to_console()

            time.sleep(5)
            clear_screen()
