import sys
import io
from requests import Session
from durango.common.ms_cv import MsCorrelationVector
from durango.network_transfer.marketplace_catalog import MarketplaceCatalog
from durango.network_transfer.metadata import \
    NetworkTransferMetadataManager


def print_progress(i, current_val, max_val):
    current_val = int(current_val / 1024 / 1024)
    max_val = int(max_val / 1024 / 1024)
    sys.stdout.write(' (%i / %i MB)' % (current_val, max_val))
    sys.stdout.write("\r [ %d " % i + "% ] ")
    sys.stdout.flush()


class StoreDownloader(object):
    HEADERS = {
        'User-Agent': 'WindowsStoreSDK',
        'MS-CV': None
    }

    def __init__(self):
        self._session = Session()
        self._cv = MsCorrelationVector()

    def _get(self, url, params, stream=False):
        headers = StoreDownloader.HEADERS
        headers['MS-CV'] = self._cv.get_value()
        self._cv.increment()
        resp = self._session.get(url, params=params, headers=headers, stream=stream)
        resp.raise_for_status()
        return resp

    def get_from_onestore_ids(self, id_list):
        if not isinstance(id_list, list):
            raise Exception('Parameter not a list!')

        url = "https://displaycatalog.mp.microsoft.com/v7.0/products/?"
        params = {
            "fieldsTemplate": "InstallAgent",
            "bigIds": ','.join(id_list),
            "market": "US",
            "languages": "en-US"
        }
        return self._get(url, params)

    def _search(self, query, productFamily):
        if not isinstance(query, str):
            raise Exception('Parameter not a string!')

        url = "https://displaycatalog.mp.microsoft.com/v7.0/productFamilies/%s/products?" % productFamily
        params = {
            "query": query,
            "market": "US",
            "languages": "en-US",
            "fieldsTemplate": "details",
            "platformdependencyname": "windows.xbox"
        }
        return self._get(url, params)

    def search_game(self, query):
        return self._search(query, "Games")

    def search_app(self, query):
        return self._search(query, "Apps")

    def download_to(self, url, target_dir):
        with io.open(target_dir, 'wb') as f:
            resp = self._get(url, {}, True)
            resp.raise_for_status()
            file_size = int(resp.headers['Content-Length'])
            print('Total size: %i' % file_size)
            pos = 0
            for chunk in resp.iter_content():
                pos += len(chunk)
                f.write(chunk)
                curr_progress = int(pos / file_size * 100)
                print_progress(curr_progress, pos, file_size)
            return file_size


def main():
    DEVICE_ID = "936DA01F-9ABD-4D9D-80C7-02AF85C822A8"
    search_query = input("Enter your search term: ")

    store = StoreDownloader()
    # Check for games
    resp = store.search_game(search_query)
    games_catalog = MarketplaceCatalog(**resp.json())
    # Check for apps
    resp = store.search_app(search_query)
    apps_catalog = MarketplaceCatalog(resp.json())

    # Put results from both searches together
    products = games_catalog.Products
    products.extend(apps_catalog.Products)
    if not len(products):
        print("No Products found!")
        sys.exit(1)
    for idx, product in enumerate(products):
        print('%i) %s' % (idx, product))
    choice = int(input('Choose a title: '))
    product = products[choice]
    print('You chose: %s' % product)

    packages = product.get_packages()
    if not len(packages):
        print("No Packages found!")
        sys.exit(1)

    for idx, package in enumerate(packages):
        print('%i) %s' % (idx, package))
    choice = int(input('Choose a package: '))

    package = packages[choice]
    urls = package.get_download_urls()
    print('Download URL: %s' % urls)
    if not len(urls):
        print('No Download URLs found!')
        sys.exit(1)
    elif len(urls) > 1:
        for idx, u in enumerate(urls):
            print('%i) %s' % (idx, u))
        choice = int(input("Choose download URL: "))
        url = urls[choice]
    else:
        url = urls[0]

    metadata_mgr = NetworkTransferMetadataManager()
    metadata_mgr.open()

    target_filepath = 'col/content/{%s}#{%s}' % (DEVICE_ID, package.get_content_id())
    print('Downloading %s to %s' % (url, target_filepath))
    size = store.download_to(url, target_filepath)
    metadata_mgr.add_entry(product, package, target_filepath, size)
    metadata_mgr.commit()


if __name__ == "__main__":
    main()
