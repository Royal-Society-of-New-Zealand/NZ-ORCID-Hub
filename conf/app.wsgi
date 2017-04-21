import sys

def application(environ, start_response):
    status = '200 OK'

    output = """
╔═══╗─────────────╔╗───╔╗───╔╗
║╔═╗║────────────╔╝╚╗──║║──╔╝╚╗
║║─╚╬══╦═╗╔══╦═╦═╩╗╔╬╗╔╣║╔═╩╗╔╬╦══╦═╗╔══╗
║║─╔╣╔╗║╔╗╣╔╗║╔╣╔╗║║║║║║║║╔╗║║╠╣╔╗║╔╗╣══╣
║╚═╝║╚╝║║║║╚╝║║║╔╗║╚╣╚╝║╚╣╔╗║╚╣║╚╝║║║╠══║
╚═══╩══╩╝╚╩═╗╠╝╚╝╚╩═╩══╩═╩╝╚╩═╩╩══╩╝╚╩══╝
──────────╔═╝║
──────────╚══╝

IT IS RUNNING!

"""
    output += 'sys.version = %s\n' % sys.version
    output += 'sys.prefix = %s\n' % sys.prefix
    output += 'sys.path = %s\n' % repr(sys.path)
    output += 'mod_wsgi.process_group = %s\n' % repr(environ['mod_wsgi.process_group'])
    output += 'mod_wsgi.application_group = %s\n' % repr(environ['mod_wsgi.application_group'])
    output += 'wsgi.multithread = %s\n' % repr(environ['wsgi.multithread'])

    output = bytes(output, "utf-8")
    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', "%d" % len(output))]

    start_response(status, response_headers)

    return [output]

