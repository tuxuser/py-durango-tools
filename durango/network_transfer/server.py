import os
import io
import sys
import argparse
import logging
from urllib import parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from durango.network_transfer.mdns import NetworkTransferMDNS

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class NetworkTransferServer(BaseHTTPRequestHandler):
    HTTP_SERVER_PORT = 10248

    def __init__(self, *kargs):
        BaseHTTPRequestHandler.__init__(self, *kargs)
        self.current_file = None
        self.current_filepath = None
        self.current_file_size = 0

    def _file_exists(self, path):
        return os.path.isfile(path)

    def _send_headers(self, code, content_type=None, length=0, range=None):
        self.send_response(code)
        self.send_header('Server', 'Microsoft-HTTPAPI/2.0')
        if content_type:
            self.send_header('Content-Type', content_type)
        if range:
            self.send_header('Content-Range', range)

        self.send_header('Content-Length', length)
        self.end_headers()

    def send_error_bad_request(self):
        self._send_headers(400)

    def send_error_not_found(self):
        self._send_headers(404)

    def send_error_server_exception(self):
        self._send_headers(500)

    def send_metadata(self, filepath):
        with io.open(filepath, 'rb') as f:
            metadata_json = f.read()
            self._send_headers(200, 'text/json', len(metadata_json))
            self.wfile.write(metadata_json)

    def send_contraint(self, filepath):
        with io.open(filepath, 'rb') as f:
            constraint = f.read()
            self._send_headers(200, 'application/octet-stream', len(constraint))
            self.wfile.write(constraint)

    def send_filechunk(self, filepath, start_pos, end_pos):
        if filepath != self.current_filepath:
            if self.current_filepath:
                # Close open handle
                self.current_filepath.close()
            self.current_filepath = filepath
            self.current_file = io.open(self.current_filepath, 'rb')
            self.current_file.seek(0, os.SEEK_END)
            self.current_file_size = self.current_file.tell()

        # Assemble Content-Range header
        content_range = 'bytes %i-%i/%i' % (start_pos, end_pos,
                                            self.current_file_size)
        # Set to actual start position
        self.current_file.seek(start_pos, os.SEEK_SET)
        data = self.current_file.read(end_pos - start_pos + 1)
        self._send_headers(206, 'application/octet-stream',
                           len(data), content_range)
        self.wfile.write(data)

    def do_GET(self):
        path = parse.unquote(self.path.rstrip('/'))
        logger.debug('- Headers for GET: %s -' % path)
        logger.debug(str(self.headers).rstrip('\n\n'))
        logger.debug('- Headers end -')

        if path == '/col':
            self.send_error_bad_request()

        elif path == '/col/metadata':
            filepath = path.lstrip('/')
            if not self._file_exists(filepath):
                logger.error('Metadata requested: %s Not found' % filepath)
                return self.send_error_bad_request()
            self.send_metadata(filepath)

        elif path.startswith('/col/constraint/'):
            filepath = path.lstrip('/')
            if not self._file_exists(filepath):
                logger.error('File requested: %s Not found' % filepath)
                return self.send_error_bad_request()
            self.send_contraint(filepath)

        elif path.startswith('/col/content/'):
            filepath = path.lstrip('/')
            if not self._file_exists(filepath):
                logger.error('File requested: %s Not found' % filepath)
                return self.send_error_bad_request()
            range = self.headers.get('Range')
            if not range:
                logger.error('File requested: No bytes-range provided')
                return self.send_error_bad_request()
            range = range.split('=')
            if len(range) != 2 or range[0] != 'bytes':
                logger.error('File requested: bytes-range is not formatted properly')
                return self.send_error_bad_request()
            byterange = range[1].split('-')
            if len(byterange) != 2:
                logger.error('File requested: bytes-range has not start/end value')
                return self.send_error_bad_request()
            start_pos, end_pos = int(byterange[0]), int(byterange[1])
            if end_pos < start_pos:
                logger.error('File requested: End pos smaller than start %i-%i' % (
                    start_pos, end_pos)
                )
                return self.send_error_server_exception()

            self.send_filechunk(filepath, start_pos, end_pos)

        else:
            self.send_error_bad_request()
            raise Exception('Unexpected request: %s' % self.path)


def main():
    parser = argparse.ArgumentParser(description="Xbox One Network Transfer Server")
    parser.add_argument('--name', '-n', default='PyNetworkTransfer',
                        help='Servername to announce')
    parser.add_argument('--id', '-i', default='FD123456789AB',
                        help='LiveID to announce')
    parser.add_argument('--port', '-p', type=int, default=NetworkTransferServer.HTTP_SERVER_PORT,
                        help='Port for HTTP Server')
    parser.add_argument('address',
                        help='IP address to bind to')

    args = parser.parse_args()

    port = NetworkTransferServer.HTTP_SERVER_PORT
    server_endpoint = (args.address, args.port)
    httpd = HTTPServer(server_endpoint, NetworkTransferServer)
    logger.info('Announcing server via MDNS')
    xbox_mdns = NetworkTransferMDNS()
    xbox_mdns.register_service(args.name, args.id,
                               args.address, args.port)

    logger.info('Starting httpd on port %i...' % args.port)
    httpd.serve_forever()

    logger.info("Unregistering MDNS...")
    xbox_mdns.unregister_service()


if __name__ == "__main__":
    main()
