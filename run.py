# -*- coding: utf-8 -*-
"""Application runnier.

While application can be run using **flask run** commmand, this script
provides runner that could be launched form a dubugger or a consose with out **flask run**.
"""

import os

from orcid_hub import app

if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ['DEBUG'] = "1"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ["ENV"] = "dev0"
    app.debug = True
    app.secret_key = os.urandom(24)
    app.run(debug=True, port=8000)
