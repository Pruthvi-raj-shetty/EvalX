"""
The flask application package.
"""

from flask import Flask
app = Flask(__name__)
from .db import init_db
init_db()

import EvalX.views
app.secret_key = "secret123"