import sys
import time

from utils.utils import clear_screen


def watch(scan, function_name):
    scan.seek(0)

    while True:
        clear_screen()

        try:
            # Hack me here
            globals()[function_name](scan)
            time.sleep(5)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception, e:
            print('Exception: %s' % e)
            sys.exit(1)
