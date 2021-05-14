from typing import List
import io
import sys
import json
from urllib import parse
from pydantic import BaseModel


class MetadataItem(BaseModel):
    type: str
    isXvc: bool
    contentId: str
    productId: str
    packageFamilyName: str
    oneStoreProductId: str
    version: str
    size: int
    allowedProductId: str
    allowedPackageFamilyName: str
    path: str
    availability: str
    relatedMedia: List[str]
    relatedMediaFamilyNames: List[str]


class NetworkTransferMetadata(BaseModel):
    items: List[MetadataItem]


class NetworkTransferMetadataManager(object):
    def __init__(self, filepath="col/metadata"):
        self._filepath = filepath
        self._metadata = None

    def open(self):
        try:
            with io.open(self._filepath, 'rt') as f:
                data = json.load(f)
                self._metadata = NetworkTransferMetadata(**data)
        except Exception as e:
            print('Metadata file could not be opened: %s' % e)
            print('Creating a fresh dict')
            self._metadata = NetworkTransferMetadata(items=list())

    def commit(self):
        try:
            with io.open(self._filepath, 'wt') as f:
                json.dump(self._metadata.dict(), f, indent=3)
        except Exception as e:
            print('Failed to write metadata: %s' % e)

    def add_entry(self, product, package, xvdpath, size):
        item = MetadataItem(
            type=product.get_type(),
            isXvc=True,
            contentId=package.get_content_id(),
            productId=product.get_product_id(),
            packageFamilyName=product.get_package_family_name(),
            oneStoreProductId=product.get_onestore_id(),
            version=product.get_version(),
            size=size,
            allowedProductId="",
            allowedPackageFamilyName="",
            path=parse.quote(xvdpath),
            availability="available",
            relatedMedia=[],
            relatedMediaFamilyNames=[]
        )
        self._metadata.items.append(item)


def main():
    if len(sys.argv) < 2:
        print('Pass path to metadata json file')
        sys.exit(1)

    metadata_mgr = NetworkTransferMetadataManager(sys.argv[1])
    metadata_mgr.open()


if __name__ == "__main__":
    main()
