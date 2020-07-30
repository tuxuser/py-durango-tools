#!/bin/env python

import sys
import io
import logging
from binascii import hexlify, unhexlify

from construct import Struct, Bytes
from construct import Int16ul, Int32ul, Int32sl, Int64ul, Int64sl
from durango.common.adapters import UUIDAdapter

log = logging.getLogger('fileformat.xvi')

XVI_MAGIC = b'crdi-xvc'
XVI_HEADER_SIZE = 0x270

XviFileHeader = Struct(
    "magic" / Bytes(8),
    "unknown1" / Bytes(0x238),          # 0x00
    "content_id" / UUIDAdapter(),       # 0x240
    "vdu_id" / UUIDAdapter(),           # 0x250
    "unknown4" / Int64ul,               # 0x260
    "unknown5" / Int32ul,               # 0x268
    "unknown6" / Int32ul,               # 0x26C
)

class XviFile(object):
    struct = XviFileHeader
    def __init__(self, header_buf):
        self._header = None
        if len(header_buf) < XVI_HEADER_SIZE:
            log.error('Passed header_buf smaller than XVI_HEADER_SIZE!')
            log.error('Got: %i, expected: %i bytes' % (len(header_buf), XVI_HEADER_SIZE))
            return
        self._header = self.struct.parse(header_buf)
        if self._header.magic != XVI_MAGIC:
            log.error('Invalid magic for XVI file: %s' % hexlify(self._header.magic))
            self._header = None

    @property
    def content_id(self):
        return self._header.content_type

    @property
    def vdu_id(self):
        return self._header.vdu_id

    def is_valid(self):
        if self._header:
            return True

    def print_info(self):
        header = self._header
        print(" -- XviHeader Info")
        print("Magic: %s" % header.magic)
        print("Content Id: %s" % header.content_id)
        print("VDU Id: %s" % header.vdu_id)


def main():
    if len(sys.argv) < 2:
        log.error("No filepath argument given!")
        sys.exit(-1)

    filepath = sys.argv[1]
    with io.open(filepath, 'rb') as f:
        buf = f.read(XVI_HEADER_SIZE)

    xvi_obj = XviFile(buf)
    if not xvi_obj.has_xvi_header():
        log.error("Parsing file %s failed!" % filepath)
        sys.exit(-2)

    xvi_obj.print_info()


if __name__ == "__main__":
    main()
