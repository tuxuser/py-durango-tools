import logging

from construct import this, Struct, Array
from construct import Int8ul, Int32ul, Int64ul, Bytes
from common.adapters import PascalStringUtf16, UUIDAdapter, FILETIMEAdapter
from common.enum import Enum

logging.basicConfig(format='[%(levelname)s] - %(name)s - %(message)s', level=logging.DEBUG)
log = logging.getLogger('fileformat.savegame_container')

BLOB_MAGIC = b'B\x00l\x00o\x00b\x00'
CONTAINERS_INDEX = 'containers.index'


class SavegameType(Enum):
    USER = 1
    MACHINE = 5

    @staticmethod
    def get_string_for_value(savegame_type):
        try:
            return SavegameType[savegame_type]
        except:
            log.warning('SavegameType: Cannot evaluate savegame_type 0x%x' % savegame_type)
            return "Unknown_SavegameType"


class BlobType(object):
    """Not sure about those indexes"""
    Binary = 1
    Json = 2
    Config = 3

"""
Structure of container.* files
"""
ContainerBlob = Struct(
    "unknown" / Int32ul,
    "unknown2"/ Int32ul,
    "magic" / Bytes(8),
    "data" / Bytes(0x88),
    "file_guid" / UUIDAdapter()
)

"""
Substruct of ContainerIndex, holds file entries
"""
ContainerIdxEntry = Struct(
    "filename" / PascalStringUtf16(Int32ul, encoding="utf16"),
    "filename_alt" / PascalStringUtf16(Int32ul, encoding="utf16"),
    "text" / PascalStringUtf16(Int32ul, encoding="utf16"),
    "blob_number" / Int8ul,
    "save_type" / Int32ul, # sync state?
    "folder_guid" / UUIDAdapter(),
    "filetime" / FILETIMEAdapter(),
    "unknown" / Int64ul, # always 0?
    "filesize" / Int32ul,
    "unknown2" / Int32ul # always 0?
)

"""
Structure of containers.index file
"""
ContainerIndex = Struct(
    "type" / Int32ul,
    "file_count" / Int32ul,
    "name" / PascalStringUtf16(Int32ul, encoding="utf16"),
    "aum_id" / PascalStringUtf16(Int32ul, encoding="utf16"),
    "filetime" / FILETIMEAdapter(),
    "unknown" / Int32ul, # seen values 0, 1, 3 so far
    "id" / PascalStringUtf16(Int32ul, encoding="utf16"),
    "files" / Array(this.file_count, ContainerIdxEntry)
)