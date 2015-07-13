from .utils.mp_flask import ThreadedFlask
app = ThreadedFlask('w3af')

from . import app
from . import middlewares
from . import resources