import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
ThreadingHTTPServer(('0.0.0.0',int(os.getenv('PORT','8080'))),partial(SimpleHTTPRequestHandler,directory='dist')).serve_forever()
