from flask import Flask
app = Flask('w3af')

from . import app
from . import middlewares
from . import resources