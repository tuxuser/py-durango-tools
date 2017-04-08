import logging

from construct import Struct, Bytes
from construct import Int16ul, Int16sl, Int32ul, Int32sl, Int64ul, Int64sl
from common import UUIDAdapter

log = logging.getLogger('fileformat.xvd')

class XvcRegionFlags(object):
    Resident =           1
    InitialPlay =        2 # might be 4, or maybe InitialPlay stuff in XvcInfo struct should be swapped with Preview
    Preview =            4
    FileSystemMetadata = 8

XVC_UPDATE_SEGMENT_SIZE = 0xC 
XvcUpdateSegmentInfo = Struct(
    "unknown1" / Int32ul,                   # 0x00
    "unknown1" / Int32ul,                   # 0x04
    "unknown1" / Int32ul,                   # 0x08
)

XVC_REGION_HEADER_SIZE = 0x80
XvcRegionHeader = Struct(
    "id" / Int32ul,                     # 0x00
    "key_id" / Int16ul,                 # 0x04
    "unknown1" / Int16ul,               # 0x06
    "flags" / Int32ul,                  # 0x08
    "unknown2" / Int32ul,               # 0x0C
    # XVC-HD = Header
    # XVC-EXVD = Embedded XVD
    # XVC-MD = XVC metadata
    # FS-MD = FileSystem metadata
    "description" / Bytes(0x40),        # 0x10
    "offset" / Int64ul,                 # 0x50
    "length" / Int64ul,                 # 0x58
    "region_pd_uid" / Int64ul,          # 0x60
    "unknown3" / Int64ul,               # 0x68
    "unknown4" / Int64ul,               # 0x70
    "unknown5" / Int64ul                # 0x78
)

XVC_INFO_SIZE = 0xDA8
XvcInfo = Struct(    
    "content_id" / UUIDAdapter()        # 0x00
    "xvc_enc_key_id" / Bytes(0xC00)     # 0x10 
    "description" / String(0x100)       # 0xC10
    "version" / Int32ul,                # 0xD10
    "region_count" / Int32ul,           # 0xD14
    "flags" / Int32ul,                  # 0xD18
    "unknown1" / Int16ul,               # 0xD1C
    "key_count" / Int16ul,              # 0xD1E
    "unknown2" / Int32ul,               # 0xD20
    "initial_play_region_id" / Int32ul, # 0xD24
    "initial_play_offset" / Int64ul,    # 0xD28
    "filetime_created" / Int64sl,       # 0xD30
    "preview_region_id" / Int32ul,      # 0xD38
    "update_segment_count" / Int32ul,   # 0xD3C
    "preview_offset" / Int64ul,         # 0xD40
    "unused_space" / Int64ul,           # 0xD48
    "reserved" / Padding(0x58)          # 0xD50
)
