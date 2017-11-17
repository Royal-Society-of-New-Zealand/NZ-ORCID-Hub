#!/usr/bin/env python
# -*-coding: utf-8 -*-
"""Collects and renders Python and Flask application evironment and configuration."""

import cgi
import os
import platform
import socket
import sys

from . import app

optional_modules_list = [
    'Cookie', 'mod_wsgi', 'psycopg2', 'zlib', 'gzip', 'bz2', 'zipfile', 'tarfile', 'ldap',
    'socket', 'audioop', 'curses', 'imageop', 'aifc', 'sunau', 'wave', 'chunk', 'colorsys',
    'rgbimg', 'imghdr', 'sndhdr', 'ossaudiodev', 'sunaudiodev', 'adodbapi', 'cx_Oracle', 'ibm_db',
    'mxODBC', 'MySQLdb', 'pgdb', 'PyDO', 'sapdbapi', 'sqlite3'
]


def _info():
    for i in optional_modules_list:
        try:
            module = __import__(i)
            sys.modules[i] = module
            globals()[i] = module
        except Exception:
            pass

    info = {}
    info['python_version'] = platform.python_version()
    info['system_info'] = get_system_info()
    info['py_internals'] = get_py_internals()
    info['os_internals'] = get_os_internals()
    info['envvars'] = get_envvars()
    info['database_info'] = get_database_info()
    info['compression_info'] = get_compression_info()
    info['socket_info'] = get_socket_info()
    info['multimedia_info'] = get_multimedia_info()
    info["app_config"] = app.config
    return info


def get_system_info():  # noqa: D103
    system_info = []

    distname = platform.linux_distribution()[0]
    version = platform.linux_distribution()[1]
    if distname != '' and version != '':
        os_version = '%s %s (%s %s)' % (platform.system(), platform.release(), distname, version)
    else:
        os_version = '%s %s' % (platform.system(), platform.release())
    system_info.append(('OS Version', os_version))

    if hasattr(os, 'path'):
        system_info.append(('OS Path', os.environ['PATH']))

    if hasattr(sys, 'version'):
        system_info.append(('Python Version', sys.version))

    if hasattr(sys, 'subversion'):
        system_info.append(('Python Subversion', sys.subversion[0]))

    if hasattr(sys, 'prefix'):
        system_info.append(('Python Prefix', sys.prefix))

    if hasattr(sys, 'path'):
        system_info.append(('Python Path', sys.path))

    if hasattr(sys, 'executable'):
        system_info.append(('Python Executable', sys.executable))

    if hasattr(sys, 'api_version'):
        system_info.append(('Python API', sys.api_version))

    system_info.append(('Build Date', platform.python_build()[1]))
    system_info.append(('Compiler', platform.python_compiler()))

    return system_info


def get_py_internals():  # noqa: D103
    py_internals = []
    if hasattr(sys, 'builtin_module_names'):
        py_internals.append(('Built-in Modules', ', '.join(sys.builtin_module_names)))
    py_internals.append(('Byte Order', sys.byteorder + ' endian'))

    if hasattr(sys, 'getcheckinterval'):
        py_internals.append(('Check Interval', sys.getcheckinterval()))

    if hasattr(sys, 'getfilesystemencoding'):
        py_internals.append(('File System Encoding', sys.getfilesystemencoding()))

    max_integer_size = str(sys.maxsize) + ' (%s)' % \
                                          hex(sys.maxsize).upper()
    py_internals.append(('Maximum Integer Size', max_integer_size))

    if hasattr(sys, 'getrecursionlimit'):
        py_internals.append(('Maximum Recursion Depth', sys.getrecursionlimit()))

    if hasattr(sys, 'tracebacklimit'):
        traceback_limit = sys.tracebacklimit
    else:
        traceback_limit = 1000
    py_internals.append(('Maximum Traceback Limit', traceback_limit))

    py_internals.append(('Maximum Code Point', sys.maxunicode))
    return py_internals


def get_os_internals():  # noqa: D103
    os_internals = []
    if hasattr(os, 'getcwd'):
        os_internals.append(("Current Working Directory", os.getcwd()))
    if hasattr(os, 'getegid'):
        os_internals.append(("Effective Group ID", os.getegid()))

    if hasattr(os, 'geteuid'):
        os_internals.append(("Effective User ID", os.geteuid()))

    if hasattr(os, 'getgid'):
        os_internals.append(("Group ID", os.getgid()))

    if hasattr(os, 'getuid'):
        os_internals.append(("User ID", os.getuid()))

    if hasattr(os, 'getgroups'):
        os_internals.append(("Group Membership", ', '.join(map(str, os.getgroups()))))

    if hasattr(os, 'linesep'):
        os_internals.append(("Line Seperator", repr(os.linesep)[1:-1]))

    if hasattr(os, 'pathsep'):
        os_internals.append(("Path Seperator", os.pathsep))

    if hasattr(os, 'getloadavg'):
        os_internals.append(("Load Avarage", ', '.join(
            map(lambda x: str(round(x, 2)), os.getloadavg()))))

    return os_internals


def get_envvars():  # noqa: D103
    return [(k, cgi.escape(v, quote=True)) for k, v in os.environ.items()]


def get_database_info():  # noqa: D103
    database_info = []
    database_info.append(('DB2/Informix (ibm_db)', is_imported('ibm_db')))
    database_info.append(('MSSQL (adodbapi)', is_imported('adodbapi')))
    database_info.append(('MySQL (MySQL-Python)', is_imported('MySQLdb')))
    database_info.append(('ODBC (mxODBC)', is_imported('mxODBC')))
    database_info.append(('Oracle (cx_Oracle)', is_imported('cx_Oracle')))
    database_info.append(('PostgreSQL (PyGreSQL)', is_imported('pgdb')))
    database_info.append(('PostgreSQL (Psycopg)', is_imported('psycopg2')))
    database_info.append(('Python Data Objects (PyDO)', is_imported('PyDO')))
    database_info.append(('SAP DB (sapdbapi)', is_imported('sapdbapi')))
    database_info.append(('SQLite3', is_imported('sqlite3')))
    return database_info


def get_compression_info():  # noqa: D103
    compression_info = []
    compression_info.append(('Bzip2 Support', is_imported('bz2')))
    compression_info.append(('Gzip Support', is_imported('gzip')))
    compression_info.append(('Tar Support', is_imported('tarfile')))
    compression_info.append(('Zip Support', is_imported('zipfile')))
    compression_info.append(('Zlib Support', is_imported('zlib')))
    return compression_info


def get_socket_info():  # noqa: D103
    socket_info = []
    socket_info.append(('Hostname', socket.gethostname()))
    socket_info.append(('Hostname (fully qualified)',
                        socket.gethostbyaddr(socket.gethostname())[0]))
    try:
        socket_info.append(('IP Address', socket.gethostbyname(socket.gethostname())))
    except Exception:
        pass
    socket_info.append(('IPv6 Support', getattr(socket, 'has_ipv6', False)))
    socket_info.append(('SSL Support', hasattr(socket, 'ssl')))
    return socket_info


def get_multimedia_info():  # noqa: D103
    multimedia_info = []
    multimedia_info.append(('AIFF Support', is_imported('aifc')))
    multimedia_info.append(('Color System Conversion Support', is_imported('colorsys')))
    multimedia_info.append(('curses Support', is_imported('curses')))
    multimedia_info.append(('IFF Chunk Support', is_imported('chunk')))
    multimedia_info.append(('Image Header Support', is_imported('imghdr')))
    multimedia_info.append(('OSS Audio Device Support', is_imported('ossaudiodev')))
    multimedia_info.append(('Raw Audio Support', is_imported('audioop')))
    multimedia_info.append(('Raw Image Support', is_imported('imageop')))
    multimedia_info.append(('SGI RGB Support', is_imported('rgbimg')))
    multimedia_info.append(('Sound Header Support', is_imported('sndhdr')))
    multimedia_info.append(('Sun Audio Device Support', is_imported('sunaudiodev')))
    multimedia_info.append(('Sun AU Support', is_imported('sunau')))
    multimedia_info.append(('Wave Support', is_imported('wave')))
    return multimedia_info


def is_imported(module):  # noqa: D103
    if module in sys.modules:
        return 'enabled'
    return 'disabled'


info = _info()
