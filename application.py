# -*- coding: utf-8 -*-
"""Application File."""

import os

from orcid_hub import app

if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ['DEBUG'] = "1"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ["ENV"] = "dev0"
    app.debug = True
    app.run(debug=True, port=5000)
