# noqa
"""
ORCID-Hub
-----

ORCID-Hub is a ...

ORCID-Hub is Fun
````````````

...


And Easy to Setup
`````````````````

And run it:

.. code:: bash

    $ virtualevn -p python3.6 venv
    $ . venv/bin/activate
    $ pip install -e .
    $ export FLASK_APP=orcid_hub
    $ flask initdb
    $ flask run
    * Running on http://localhost:5000/

Ready for production? `Read this first <http://docs.orcidhub.org.nz/deploying/>`.

Links
`````

* `website <https://orcidhub.org.nz/>`_
* `FAQ <https://orcidhub.org.nz/faq/>`_
* `about the project <https://orcidhub.org.nz/about/>`_
* `documentation <http://docs.orcidhub.org.nz/>`_
"""
from setuptools import find_packages, setup

setup(
    name="ORCID Hub",
    version="2.0.0",
    url="https://github.com/Royal-Society-of-New-Zealand/NZ-ORCID-Hub",
    long_description=__doc__ or open('README.md').read(),
    # packages=[
    #     "orcid_hub",
    # ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "requests",
        "requests_oauthlib",
        "psycopg2",
        "peewee",
        "flask-login",
        "Flask-WTF",
        "emails",
        "flask-admin",
        "python-slugify",
        "flask-script",
        "wtf-peewee",
        "pycountry",
        "html2text",
        "tablib",
        "raven",
        "raven[flask]",
        "pyyaml",
        "pykwalify",
        "flask-peewee",
        "Flask-OAuthlib",
        "flask-swagger",
    ],
    license="MIT",
    classifiers=[
        "Development Status :: 1 - Release",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Ptyhon :: 3.6",
    ],
)
