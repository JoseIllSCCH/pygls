from pygls.server import LanguageServer

server = LanguageServer('example-server', 'v0.1')

server.start_tcp('127.0.0.1', 8989)