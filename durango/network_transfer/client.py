import io
import sys
import json
import logging
from time import sleep
from urllib import parse
from requests import Request, Response, Session
from durango.common.ms_cv import MsCorrelationVector
from durango.network_transfer.mdns import NetworkTransferMDNS
from durango.network_transfer.metadata import \
    MetadataItem, \
    NetworkTransferMetadata
from durango.network_transfer.store_downloader import StoreDownloader

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def print_progress(i, current_val, max_val) -> None:
    current_val = int(current_val / 1024 / 1024)
    max_val = int(max_val / 1024 / 1024)
    sys.stdout.write(' (%i / %i MB)' % (current_val, max_val))
    sys.stdout.write("\r [ %d " % i + "% ] ")
    sys.stdout.flush()


class NetworkTransferClient(object):
    CHUNK_SIZE = 500000
    # HTTP_PORT = 10248
    IGNORE_HEADERS = ['User-Agent', 'Accept', 'Accept-Encoding']

    def __init__(self):
        self.session = Session()

    def _get(self, url: str, headers: dict) -> Response:
        req = Request('GET', url, headers=headers)
        prepared = self.session.prepare_request(req)
        for header in self.IGNORE_HEADERS:
            # Check if we passed our own version of ignored header
            if header not in headers:
                del prepared.headers[header]

        resp = self.session.send(prepared)
        logger.debug('Request Headers, URL: %s :::\n' % url)
        logger.debug('%s\n ::: End Request Headers' % resp.request.headers)
        logger.debug('Response Headers, URL: %s :::\n' % url)
        logger.debug('%s\n ::: End Response Headers' % resp.headers)
        resp.raise_for_status()
        return resp

    def download_onestore_info(self, metadata: NetworkTransferMetadata) -> dict:
        onestore_ids = [item.oneStoreProductId for item in metadata.items if item.oneStoreProductId]
        downloader = StoreDownloader()
        resp = downloader.get_from_onestore_ids(onestore_ids)
        info = resp.json().get('Products')
        # Sort by OneStoreId / ProductId
        sorted_dict = dict()
        for i in info:
            sorted_dict.update({i['ProductId']: i})
        return sorted_dict

    def _download_chunk(self, url: str, start_pos: int, end_pos: int) -> Response:
        headers = {
            'Range': 'bytes=%i-%i' % (start_pos, end_pos),
            'MS-CV': MsCorrelationVector().get_value(),
            'Host': parse.urlparse(url).netloc
        }
        return self._get(url, headers=headers)

    def download_item(self, address: str, entry: MetadataItem) -> None:
        content_url = 'http://%s%s' % (address, entry.path)
        constraint_url = content_url.replace('content', 'constraint')
        # Request null position
        resp = self._download_chunk(content_url, 0, 0)
        # Read total length from response header
        # "Content-Range: 0-0/999999" (999999 is total size)
        content_range = resp.headers.get('Content-Range', '')
        total_size = int(content_range.split('/')[1])
        if total_size != entry.size:
            raise Exception('Total Size does not match')

        # Try to download CONSTRAINT
        try:
            headers = {'MS-CV': MsCorrelationVector().get_value()}
            resp = self._get(constraint_url, headers=headers)
            with io.open(entry.contentId + '.constraint', 'wb') as cf:
                cf.write(resp.content)
            print('Downloaded constraint file to: %s' % entry.contentId + '.constraint')
        except Exception as e:
            print(f'FAILED TO DOWNLOAD CONSTRAINT! exc: {e}')

        # Download the xvd blob
        with io.open(entry.contentId, 'wb') as f:
            old_p = -1
            position = 0
            while position < total_size:
                resp = self._download_chunk(content_url,
                                            position, position+self.CHUNK_SIZE)
                if len(resp.content) == 0:
                    break
                f.write(resp.content)
                # Progress bar
                curr_progress = int(position / total_size * 100)
                if curr_progress > old_p:
                    old_p = curr_progress
                    print_progress(curr_progress, position, total_size)
                position += len(resp.content)
            print_progress(100, total_size, total_size)
            f.flush()

    def download_metadata(self, address: str) -> Response:
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'CopyOnLanSvc'
        }
        return self._get('http://%s/col/metadata' % address, headers=headers)

    @staticmethod
    def objectify_metadata(metadata: Response | str | dict) -> NetworkTransferMetadata:
        if isinstance(metadata, Response):
            data = metadata.json()
        elif isinstance(metadata, str):
            data = json.loads(metadata)
        else:
            data = metadata
        if not isinstance(data, dict):
            logger.error('Invalid data passed to objectify_metadata')
            return

        return NetworkTransferMetadata(**data)


def main():
    print('Xbox NetworkTransfer Client')
    mdns_discovery = NetworkTransferMDNS()
    mdns_discovery.discover()
    print('Waiting for consoles to advertise...')
    sleep(2)

    consoles = mdns_discovery.consoles
    if not len(consoles):
        logger.error('No consoles found')
        sys.exit(1)

    print('Found the following consoles:')
    for idx, console in enumerate(consoles):
        print('%i) %s' % (idx, console))

    choice = input('Which console to connect to? Enter number: ')
    index = int(choice)
    console = consoles[index]
    print('Chosen: %s' % console)

    client = NetworkTransferClient()
    resp = client.download_metadata(console.address)
    metadata = client.objectify_metadata(resp)

    try:
        print('Downloading data from Xbox Live')
        items_data = client.download_onestore_info(metadata)
    except Exception as e:
        logger.error('Failed downloading from xbl, Error: %s' % e)
        items_data = {}

    count = 0
    for entry in metadata.items:
        size = entry.size
        info = items_data.get(entry.oneStoreProductId)
        if info:
            name = info['LocalizedProperties'][0]['ProductTitle']
        else:
            name = "%s %s" % (entry.packageFamilyName, entry.contentId)

        print("%i) %s  %s %i MB" % (count, name, entry.type, size / 1024 / 1024))
        count += 1

    choice = input('Download item? Enter number: ')
    index = int(choice)

    try:
        item = metadata.items[index]
        print('\nDownloading: %s (%s)\n' % (item.packageFamilyName,
                                            item.contentId))
        client.download_item(console.address, item)
        print('\nFile finished downloading!\n')
    except KeyError as e:
        logger.error('Failed to parse json %s\n' % e)
    except Exception as e:
        logger.error('Failed downloading: %s\n' % e)


if __name__ == '__main__':
    main()
