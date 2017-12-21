# SEE: http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/
import sys, os
app_dir = os.path.dirname(__file__)
sys.path.insert(0, app_dir)

from orcid_hub import app as application
