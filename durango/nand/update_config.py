#!/usr/bin/env python

from construct import Int8ul, Int16ul, Int16ub
from construct import Int32ul, Int32ub, Int64ul, Int64ub
from construct import String, Bytes, Array, Padding, Struct
from hexdump import hexdump

UPDATE_CFG_MAGIC = b'UCFG'
UPDATE_CFG_MAGIC = Int32ub.parse(UPDATE_CFG_MAGIC)

UPDATE_CFG_MAX_DATA_SIZE = 0xCF0
UPDATE_CFG_HEADER_SIZE = 50

UPDATE_CFG_MAX_FILES = 19

BUILD_INFO_ID_SHORT = 5
BUILD_INFO_ID_LONG = 12

UpdateCfgFileEntry = Struct(
    "unknown_1" / Int32ul, # 0
    "unknown_2" / Int64ul, # 4
    "filename" / String(64, encoding="utf-8")  # 12
)

# Short build info size: 0xB2
UpdateCfgBuildShort = Struct(
    "build_id" / String(178, encoding="utf-8")
)

# Long build info size: 0x1E6
UpdateCfgBuildLong = Struct(
    "build_id_before" / String(176, encoding="utf-8"),
    "build_id_after" / String(176, encoding="utf-8"),
    "build_string" / String(134, encoding="utf-8")
)

UpdateCfgHeader = Struct(
    "unknown_1" / Int16ul, # 00: 07 00
    "unknown_2" / Int8ul, # 02: 01
    "unknown_3" / Int8ul, # 03: 40
    "unknown_4" / Int32ul, # 04: 00 00 00 00
    "hash" / Bytes(32), # 08: <32 bytes>
    "magic" / Int32ul, # 40: UPDATE_CFG_MAGIC
    "total_length" / Int32ul, # 44
    "unknown_5" / Int8ul, # 48
    "identifier" / Int8ul, # 49: 5->short (0xB2), 12->long (0x1E6)
)


class DurangoUpdateCfg(object):
    def __init__(self, data):
        self._data = data

    def parse(self):
        if UpdateCfgHeader.sizeof() != UPDATE_CFG_HEADER_SIZE:
            print("ERROR: UpdateCfgHeader struct does not match UPDATE_CFG_HEADER_SIZE!")
            print("Got %i instead of expected %i bytes" % (UpdateCfgHeader.sizeof(), UPDATE_CFG_HEADER_SIZE))
            return

        data = self._data
        header = UpdateCfgHeader.parse(data)
        if header.magic != UPDATE_CFG_MAGIC:
            print("ERROR: Invalid Magic for update.cfg!")
            return

        # Cut data to header-defined size
        data = data[:header.total_length]

        if header.identifier == BUILD_INFO_ID_SHORT:
            cfg_build_struct = UpdateCfgBuildShort
        elif header.identifier == BUILD_INFO_ID_LONG:
            cfg_build_struct = UpdateCfgBuildLong
        else:
            print("ERROR: Unknown identifier...")
            return

        data = data[UPDATE_CFG_HEADER_SIZE:]
        build_str = cfg_build_struct.parse(data)
        data = data[cfg_build_struct.sizeof():]
        files = Array(UPDATE_CFG_MAX_FILES, UpdateCfgFileEntry).parse(data)
        print(build_str)
        print(files)
