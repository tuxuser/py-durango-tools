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

class DurangoNand(object):
    def __init__(self, filename):
        # offset : sequence_version
        self.header_offsets = dict()
        self.xbfs_tables = list()
        self.is_valid = True
        self.dump_type = None
        self.filename = filename
        self.filesize = os.stat(self.filename).st_size
        # Run minimal verification
        if self.filesize == FLASH_SIZE_LOG:
            self.dump_type = "RAW"
        elif self.filesize == FLASH_SIZE_RAW:
            self.dump_type = "LOGICAL"
        else:
            self.dump_type = "INVALID"
            self.is_valid = False

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

    def _log_block_to_size(self, value):
        return value * LOG_BLOCK_SZ
    
    def _size_to_log_block(self, value):
        return value / LOG_BLOCK_SZ

    def get_header_rawoffset(self, seq_version):
        return self.header_offsets[seq_version]

    def get_xbfs_sequence_list(self):
        return [t.sequence_version for t in self.xbfs_tables]

    def get_xbfs_table_by_sequence(self, seq_version):
        seq_list = self.get_xbfs_sequence_list()
        if not seq_version in seq_list:
            log.error("XBFS table with seq: %i not found!" % seq_version)
            return
        table_idx = seq_list.index(seq_version)
        return self.xbfs_tables[table_idx]

    def get_latest_sequence_version(self):
        seq_list = self.get_xbfs_sequence_list()
        seq_high = max(seq_list)
        if 0 in seq_list and seq_high == 0xFF:
            # Sequence version (uint8) wraps around
            # 0xFF -> 0x00
            return 0
        return seq_high

    def get_latest_xbfs_table(self):
        latest_seq = self.get_latest_sequence_version()
        return self.get_xbfs_table_by_sequence(latest_seq)

    def get_xbfs_fileentry_by_name(self, name, table):
        try:
            index = FlashFiles.index(name)
        except ValueError:
            log.error("Requested filename %s does not exist" % name)
            return

        entry = table.files[index]
        if not entry.size:
            log.error("File %s is not present in desired XBFS table" % name)
            return
        return entry

    def read_file_from_xbfs(self, filename, table):
        entry = self.get_xbfs_fileentry_by_name(filename, table)
        if not entry:
            return
        offset = self._log_block_to_size(entry.offset)
        size = self._log_block_to_size(entry.size)
        with io.open(self.filename, "rb") as f:
            f.seek(offset)
            return f.read(size)

    def print_info(self, table):
        header_offset = self.get_header_rawoffset(table.sequence_version)
        log.info("-- XBFS table info --")
        log.info("Header Offset: 0x%08x" % header_offset)
        log.info("Format: %i" % table.format_version)
        log.info("Sequence: %i" % table.sequence_version)
        log.info("Layout: %i" % table.layout_version)
        log.info("Guid: %s" % table.guid)
        log.info("Hash: %s" % binascii.hexlify(table.hash).decode('utf-8'))

    def print_filelist(self, table):
        log.info("-- XBFS filelist --")
        for filename in FlashFiles:
            fil = self.get_xbfs_fileentry_by_name(filename, table)
            if not fil:
                continue
            offset = self._log_block_to_size(fil.offset)
            size = self._log_block_to_size(fil.size)
            log.info("off: 0x%08x, sz: 0x%08x, file: %s" % (
                offset, size, filename
            ))

    def extract_files_from_table(self, table, dest_dir):
        for filename in FlashFiles:
            data = self.read_file_from_xbfs(filename, table)
            if not data:
                continue
            log.info("Extracting file %s.." % filename)
            self._save_file(data, dest_dir, filename)

    def parse(self):
        if not self.is_valid:
            log.error("ERROR: NAND dump does not match expected filesize!")
            log.error("Expecting 0x%08x or 0x%08x bytes dump!" % (FLASH_SIZE_LOG, FLASH_SIZE_RAW))
            return

        with io.open(self.filename, "rb") as f:
            # Search for fixed-offset filesystem header
            for offset in HEADER_OFFSETS:
                f.seek(offset)
                data = f.read(HEADER_SIZE)
                header = FlashHeader.parse(data)
                if header.magic != HEADER_MAGIC:
                    continue
                hash = self._hash(data[:-HEADER_HASH_SIZE])
                self.xbfs_tables.append(header)
                self.header_offsets[header.sequence_version] = offset

        if not len(self.get_xbfs_sequence_list()):
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
    nand.print_info(table)
    nand.print_filelist(table)
    if args.extract:
        log.info("Extracting files...")
        dirname = "%s_%s" % (args.filename, table.guid)
        nand.extract_files_from_table(table, dirname)
