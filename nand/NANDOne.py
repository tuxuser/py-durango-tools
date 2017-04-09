#!/usr/bin/env python

'''
NANDOne - Xbox One (Codename: Durango) NAND dump parser / extractor
* Maybe one day: " + decryptor"

Credits:
    noob25x / emoose: XVDTool (https://github.com/emoose/xvdtool)
    various people: supplying nand dumps
'''

import io
import os
import sys
import logging
import hashlib
import uuid
import binascii
import argparse

from construct import Int8ul, Int16ul, Int16ub
from construct import Int32ul, Int32ub, Int64ul, Int64ub
from construct import String, Bytes, Array, Padding, Struct

logging.basicConfig(format='[%(levelname)s] - %(name)s - %(message)s', level=logging.DEBUG)
log = logging.getLogger('nand_one')

APP_NAME = 'NANDOne'
BUILD_VER = 'v0.03'

FLASH_SIZE_LOG = 0x13BC00000
FLASH_SIZE_RAW = 0x13C000000
LOG_BLOCK_SZ = 0x1000

HEADER_SIZE = 1024
# Reverse magic
HEADER_MAGIC = b'XBFS'[::-1]

HEADER_HASH_SIZE = 32

HEADER_OFFSETS = [0x10000,
                0x810000,
                0x820000]

GUID_SIZE = 16

UPDATE_CONFIG_FILE = "update.cfg"

XVD_MAGIC = 'msft-xvd'
XVD_MAGIC_START = 0x200

FLASH_FILES_COUNT = 25
FlashFiles = [
    "1smcbl_a.bin",     # 01 1st SMC bootloader, slot A
    "header.bin",       # 02 Flash header
    "devkit.ini",       # 03 devkit init
    "mtedata.cfg",      # 04 MTE data ???
    "certkeys.bin",     # 05 Certificate keys
    "smcerr.log",       # 06 SMC error log
    "system.xvd",       # 07 SystemOS xvd
    "$sosrst.xvd",      # 08 SystemOS reset ???
    "download.xvd",     # 09 Download xvd ???
    "smc_s.cfg",        # 10 SMC config - signed
    "sp_s.cfg",         # 11 SP config - signed
    "os_s.cfg",         # 12 OS config - signed
    "smc_d.cfg",        # 13 SMC config - decrypted
    "sp_d.cfg",         # 14 SP config - decrypted
    "os_d.cfg",         # 15 OS config - decrypted
    "smcfw.bin",        # 16 SMC firmware
    "boot.bin",         # 17 Main Bootloader ???
    "host.xvd",         # 18 HostOS xvd
    "settings.xvd",     # 19 Settings xvd
    "1smcbl_b.bin",     # 20 1st SMC bootloader, slot B
    "bootanim.dat",     # 21 Bootanimation
    "sostmpl.xvd",      # 22 SystemOS template xvd
    "update.cfg",       # 23 Update config / log?
    "sosinit.xvd",      # 24 SystemOS init xvd
    "hwinit.cfg"        # 25 Hardware init config
]


# offset and size need to be multiplied by LOG_BLOCK_SZ
FlashFileEntry = Struct(
    "offset" / Int32ul,
    "size" / Int32ul,
    "unknown" / Int64ul
)

FlashHeader = Struct(
    "magic" / Bytes(4), # HEADER_MAGIC
    "format_version" / Int8ul,
    "sequence_version" / Int8ul,
    "layout_version" / Int16ul,
    "unknown_1" / Int64ul,
    "unknown_2" / Int64ul,
    "unknown_3" / Int64ul,
    "files" / Array(FLASH_FILES_COUNT, FlashFileEntry),
    Padding(544),
    "guid" / Bytes(GUID_SIZE),
    "hash" / Bytes(HEADER_HASH_SIZE) # SHA256 checksum
)

class DurangoXbfsTable(object):
    _files = {}
    _notfound_files = []
    def __init__(self, header_offset, format, sequence, layout, guid, hash, is_hash_valid):
        self._header_off = header_offset
        self._format = format
        self._sequence = sequence
        self._layout = layout
        self._guid = guid
        self._hash = hash

    @classmethod
    def from_struct(cls, header_offset, struct, is_hash_valid):
        return cls(header_offset, struct.format_version, struct.sequence_version,
            struct.layout_version, uuid.UUID(bytes=struct.guid),
            binascii.hexlify(struct.hash).decode('utf-8'),
            is_hash_valid)

    @property
    def header_offset(self):
        return self._header_off

    @property
    def sequence_version(self):
        return self._sequence
    
    @property
    def format_version(self):
        return self._format
    
    @property
    def layout_version(self):
        return self._layout

    @property
    def guid(self):
        return self._guid
    
    @property
    def hash(self):
        return self._hash

    @property
    def files(self):
        return self._files

    @property
    def notfound_list(self):
        return self._notfound_files

    def _add_file(self, name, offset, size):
        if size:
            self._files.update({name : (offset, size)})
        else:
            self._notfound_files.append(name)

    def get_file_by_name(self, name):
        fil = self._files.get(name)
        if fil:
            return (name, fil)

    def print_info(self):
        log.info("-- XBFS table info --")
        log.info("Header Offset: 0x%08x" % self.header_offset)
        log.info("Format: %i" % self.format_version)
        log.info("Sequence: %i" % self.sequence_version)
        log.info("Layout: %i" % self.layout_version)
        log.info("Guid: %s" % self.guid)
        log.info("Hash: %s" % self.hash)

    def print_filelist(self):
        log.info("-- XBFS filelist --")
        for name, offset_tuple in self.files.items():
            offset, size = offset_tuple
            log.info("off: 0x%08x, sz: 0x%08x, file: %s" % (offset, size, name))

class DurangoNand(object):
    def __init__(self, filename):
        self._xbfs_tables = []
        # Lowest possible sequence is 1
        self._latest_sequence = 0
        self._valid = False
        self._dump_type = None
        self._filename = filename
        self._filesize = os.stat(self.filename).st_size
        # Run minimal verification
        self._verify_inputfile()

    def _verify_inputfile(self):
        if self._filesize == FLASH_SIZE_LOG:
            self._dump_type = "RAW"
        elif self._filesize == FLASH_SIZE_RAW:
            self._dump_type = "LOGICAL"

        if self._dump_type:
            self._valid = True

    @property
    def filename(self):
        return self._filename
    
    @property
    def filesize(self):
        return self._filesize

    @property
    def is_valid(self):
        return self._valid

    @property
    def dump_type(self):
        return self._dump_type

    @property
    def latest_sequence_version(self):
        return self._latest_sequence

    @property
    def xbfs_tables(self):
        return self._xbfs_tables

    def _hash(self, data):
        return hashlib.sha256(data).digest()

    def _save_file(self, buf, dirname, filename):
        try:
            os.mkdir(dirname)
        except FileExistsError as e:
            pass

        dest_path = os.path.join(dirname, filename)
        with open(dest_path, "wb") as dest_fd:
            dest_fd.write(buf)
            dest_fd.flush()

    def _add_xbfs_table(self, table):
        self._xbfs_tables.append((table.sequence_version, table))
        if table.sequence_version > self.latest_sequence_version:
            self._latest_sequence = table.sequence_version

    def get_xbfs_table_by_sequence(self, sequence):
        table = dict(self._xbfs_tables).get(sequence)
        if not table:
            raise Exception("XBFS table with seq: %i not found!" % sequence)
        return table

    def get_latest_xbfs_table(self):
        return self.get_xbfs_table_by_sequence(self.latest_sequence_version)

    def get_xbfs_sequence_list(self):
        return [f for f in dict(self._xbfs_tables)]

    def extract_files_from_table(self, table):
        dirname = "%s_%s" % (self.filename, table.guid)
        with io.open(self.filename, "rb") as f:
            for name, offset_tuple in table.files.items():
                offset, size = offset_tuple
                f.seek(offset)
                data = f.read(size)
                log.info("Extracting file 0x%08x : %s " % (offset, name))
                self._save_file(data, dirname, name)

    def extract_table_by_seq(self, sequence_num):
        table = self.get_xbfs_table_by_sequence(sequence_num)
        self.extract_files_from_table(table)

    def parse(self):
        if not self.is_valid:
            log.error("ERROR: NAND dump does not match expected filesize!")
            log.error("Expecting 0x%08x or 0x%08x bytes dump!" % (FLASH_SIZE_LOG, FLASH_SIZE_RAW))
            return

        with io.open(self.filename, "rb") as f:
            # Search for fixed-offset filesystem header
            for offset in HEADER_OFFSETS:
                hash_valid = True
                f.seek(offset)
                data = f.read(HEADER_SIZE)
                header = FlashHeader.parse(data)
                if header.magic != HEADER_MAGIC:
                    continue
                hash = self._hash(data[:-HEADER_HASH_SIZE])
                xbfs_table = DurangoXbfsTable.from_struct(offset, header, (hash == header.hash))
                for idx, name in enumerate(FlashFiles):
                    offset = header.files[idx].offset * LOG_BLOCK_SZ
                    size = header.files[idx].size * LOG_BLOCK_SZ
                    xbfs_table._add_file(name, offset, size)
                self._add_xbfs_table(xbfs_table)

        if not self.latest_sequence_version:
            raise Exception("No valid XBFS table found!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse raw Durango Nanddump')
    parser.add_argument('filename', type=str, help='input filename')
    parser.add_argument('--extract', action='store_true', help='extract files from nand')
    log.info("%s %s started" % (APP_NAME, BUILD_VER))

    args = parser.parse_args()

    if not os.path.isfile(args.filename):
        log.error("ERROR: file %s does not exist!" % args.filename)
        sys.exit(-1)
    
    log.info("Nanddump file: %s" % args.filename)
    nand = DurangoNand(args.filename)
    log.info("Dump type: %s" % nand.dump_type)
    nand.parse()

    table = nand.get_latest_xbfs_table()
    log.info("Available Sequences: %s" % nand.get_xbfs_sequence_list())
    log.info("Latest sequence num: %i" % table.sequence_version)
    table.print_info()
    table.print_filelist()
    if args.extract:
        log.info("Extracting files...")
        nand.extract_files_from_table(table)
