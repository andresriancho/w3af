import logging

try:
    from fabric.colors import red, yellow, green
except ImportError:
    # In case we don't have fabric
    red = yellow = green = lambda x: x


def configure_logging(log_file):
    logging.basicConfig(filename=log_file,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filemode='w',
                        level=logging.DEBUG)
    
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = ColorLog()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)


class ColorLog(logging.Handler):
    """
    A class to print colored messages to stdout
    """

    COLORS = {logging.CRITICAL: red,
              logging.ERROR: red,
              logging.WARNING: yellow,
              logging.INFO: green,
              logging.DEBUG: lambda x: x}
    
    def __init__(self):
        logging.Handler.__init__(self)

    def usesTime(self):
        return False

    def emit(self, record):
        color = self.COLORS.get(record.levelno, lambda x: x)
        print(color(record.msg))