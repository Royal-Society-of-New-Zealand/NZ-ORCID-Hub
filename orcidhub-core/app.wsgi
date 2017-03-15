# SEE: http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import monitor
from application import app as application

monitor.start(os.path.dirname(__file__))
