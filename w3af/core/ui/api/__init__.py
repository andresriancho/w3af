from flask import Flask
app = Flask('w3af')

from . import app
from . import resources