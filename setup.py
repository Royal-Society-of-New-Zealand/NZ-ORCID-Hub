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
    $ pip install -e .  # OR (with development packages): pip install -e .[dev]
    $ export FLASK_APP=orcid_hub
    $ orcidhub initdb
    $ orcidhub cradmin EMAIL
    $ orcidhub run -p PORT
    * Running on http://localhost:PORT/

Ready for production? `Read this first <http://docs.orcidhub.org.nz/deploying/>`.

Links
`````

* `website <https://orcidhub.org.nz/>`_
* `FAQ <https://orcidhub.org.nz/faq/>`_
* `about the project <https://orcidhub.org.nz/about/>`_
* `documentation <http://docs.orcidhub.org.nz/>`_
"""

import re

from setuptools import find_packages, setup

# extract version from __init__.py
with open("orcid_hub/__init__.py", "r") as f:
    VERSION = next(re.finditer("__version__ = [\"'](.*?)[\"']", f.read())).group(1).strip()

setup(
    name="ORCID-Hub",
    version=VERSION,
    keywords=[
        "orcid",
        "hub",
        "research",
    ],
    author="Jason Gush, Radomirs Cirskis, Roshan Pawar",
    author_email="jagu04@gmail.com, nad2000@gmail.com, roshan.pawar@auckland.ac.nz",
    url="https://github.com/Royal-Society-of-New-Zealand/NZ-ORCID-Hub",
    long_description=__doc__ or open('docs/README.md').read(),
    # packages=["orcid_hub", ],
    packages=[
        "orcid_hub",
        "orcid_api",
    ],
    # packages=find_packages(),
    zip_safe=False,
    package_data={'': ["'orcid_swagger.yaml"]},
    include_package_data=True,
    # dependency_links=[
    #     "./orcid_api",  # pre-geneated and patched 'swagger_client' from form ./orcid_api
    # ],
    install_requires=[
        "requests",
        "requests_oauthlib",
        "psycopg2",
        "peewee==2.10.2",
        "peewee-validates",
        "flask-login",
        "Flask-WTF",
        "emails",
        "flask-admin",
        "python-slugify",
        "flask-script",
        "wtf-peewee==0.2.6",
        "pycountry",
        "html2text",
        "tablib",
        "raven",
        "raven[flask]",
        "pyyaml",
        "pykwalify",
        "flask-peewee==0.6.7",
        "Flask-OAuthlib",
        "flask-swagger",
        "flask-mail",
        "flask-restful",
        "validators",
        # "swagger_client",
        "rq",
        "rq-dashboard",
        "rq-scheduler",
        "Flask-RQ2",
        "Flask-RQ2[cli]",
    ],
    extras_require={
        "dev": [
            "sphinx",
            "sphinx-autobuild",
            "m2r",
            "recommonmark",
            "pyyaml",
            "coverage>=4.4.1",
            "coveralls>=1.2.0",
            "fake-factory>=9999.9.9",
            "flake8>=3.4.1",
            "flake8-docstrings>=1.1.0",
            "flake8-polyfill>=1.0.1",
            "flask-debugtoolbar>=0.10.1",
            "isort>=4.2.15",
            "mccabe>=0.6.1",
            "pep8-naming>=0.4.1",
            "pycodestyle>=2.3.1",
            "pydocs>=0.2",
            "pydocstyle>=2.0.0",
            "pyflakes>=1.5.0",
            "Pygments>=2.2.0",
            "pytest>=3.2.1",
            "pytest-cov>=2.5.1",
            "pytest-mock",
            "six>=1.10.0",
            "testpath>=0.3.1",
            "yapf>=0.17.0",
            "Faker",
        ],
        "test": [
            "pyyaml",
            "coverage>=4.4.1",
            "coveralls>=1.2.0",
            "fake-factory>=9999.9.9",
            "flake8>=3.4.1",
            "flake8-docstrings>=1.1.0",
            "flake8-polyfill>=1.0.1",
            "mccabe>=0.6.1",
            "pep8-naming>=0.4.1",
            "pycodestyle>=2.3.1",
            "pydocs>=0.2",
            "pyflakes>=1.5.0",
            "pytest>=3.2.1",
            "pytest-cov>=2.5.1",
            "pytest-mock",
            "testpath>=0.3.1",
            "Faker",
            "Online-W3C-Validator>=0.3.1",
        ],
    },
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
    ],
    entry_points='''
        [console_scripts]
        orcidhub=orcid_hub.cli:main
    '''

    # entry_points={
    #     "console_scripts": [
    #         "orcidhub=orcid_hub.cli:main"
    #     ]
    # }
)
