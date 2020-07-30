#!/bin/env python

import sys
import io
import logging
from binascii import hexlify

from construct import Struct, Bytes, FlagsEnum, Padding, String, Array
from construct import Int32ul, Int64ul, Int64sl
from construct import Enum as CEnum
from durango.common.adapters import UUIDAdapter, FILETIMEAdapter
from durango.common.enum import Enum
from durango.common.constants import HASH_SIZE

log = logging.getLogger('fileformat.xvd')

XVD_MAGIC = b'msft-xvd'

class XvdContentType(Enum):
    Data = 0
    Title = 1
    SystemOS = 2 # system.xvd / sharedOS
    EraOS = 3 # era.xvd / exclusiveOS
    Scratch = 4
    ResetData = 5
    Application = 6
    HostOS = 7 # host.xvd / hostOS
    X360STFS = 8
    X360FATX = 9
    X360GDFX = 0xA
    Updater = 0xB
    OfflineUpdater = 0xC
    Template = 0xD # sostmpl.xvd SettingsTemplate.xvd
    MteHost = 0xE
    MteApp = 0xF
    MteTitle = 0x10
    MteEraOS = 0x11
    EraTools = 0x12
    SystemTools = 0x13
    SystemAux = 0x14
    # 0x15
    Codec = 0x16
    Qaslt = 0x17
    AppDLC = 0x18 # downloadable content for an application
    TitleDLC = 0x19 # downloadable content for a game title
    UniversalDLC = 0x1A # dowloadable content not associated with an application or game
    SystemData = 0x1B
    Test = 0x1C
    # 0x1D
    # 0x1E
    # 0x1F
    # 0x20
    UWA = 0x21 # UWP App

    @staticmethod
    def get_string_for_value(content_type):
        try:
            return XvdContentType[content_type]
        except:
            log.warning('ContentEntry: Cannot evaluate content_type 0x%x' % content_type)
            return "Unknown_XvdContentType"


class XvcLicenseBlockId(object):
    # EKB block ids
    EKB_UNKNOWN1 = 1    # length 0x02, value 0x05
    EKB_KEY_ID_STRING = 2    # length 0x20
    EKB_UNKNOWN2 = 3    # length 0x02, value 0x07
    EKB_UNKNOWN4 = 4    # length 0x01, value 0x31
    EKB_UNKNOWN5 = 5    # length 0x02, value 0x01
    EKB_ENCRYPTED_CIK = 7    # length 0x100

    #SPLicenseBlock block ids
    SP_LICENSE_SECTION = 0x14
    SP_UNKNOWN1 = 0x15
    SP_UNKNOWN2 = 0x16
    SP_UPLINK_KEY_ID = 0x18
    SP_KEY_ID = 0x1A
    SP_ENCRYPTED_CIK = 0x1B
    SP_DISC_ID_SECTION = 0x1C
    SP_UNKNOWN3 = 0x1E
    SP_UNKNOWN4 = 0x24
    SP_DISC_ID = 0x25
    SP_SIGNATURE_SECTION = 0x28
    SP_UNKNOWN5 = 0x29
    SP_UNKNOWN6 = 0x2C
    SP_POSSIBLE_HASH = 0x2A
    SP_POSSIBLE_SIGNATURE = 0x2B

"""These can contain XVC data"""
XvcContentTypes = [
    XvdContentType.Title,
    XvdContentType.Application,
    XvdContentType.MteApp,
    XvdContentType.MteTitle,
    XvdContentType.AppDLC,
    XvdContentType.TitleDLC,
    XvdContentType.UniversalDLC
]

"""Used by FlagsEnum substruct"""
XvdVolumeFlags = {
    "ReadOnly": 1,
    "EncryptionDisabled": 2,
    "DataIntegrityDisabled": 4,
    "LegacySectorSize": 8,
    "ResiliencyEnabled": 16,
    "SraReadOnly": 32,
    "RegionIdInXts": 64,
    "EraSpecific": 128
}

"""Used by Enum substruct"""
XvdType = {
    "Fixed": 0,
    "Dynamic": 1
}

"""Substruct of XvdFileHeader"""
XvdExtEntry = Struct(
    "code" / Int32ul,
    "length" / Int32ul,
    "offset" / Int64ul,
    "data_length" / Int32ul,
    "reserved" / Int32ul
)

XVD_KEY_SIZE = 32
SANDBOX_ID_SIZE = 16

XVD_HEADER_SIZE = 0x1000
XvdFileHeader = Struct(
    "signature" / Bytes(0x200),              # 0x00 - 0x200
    "magic" / Bytes(8),                      # 0x200
    "volume_flags" / FlagsEnum(Int32ul, **XvdVolumeFlags), # 0x208
    "format_version" / Int32ul,              # 0x20C
    "filetime_created" / FILETIMEAdapter(),  # 0x210
    "drive_size" / Int64ul,                  # 0x218
    "content_id" / UUIDAdapter(),            # 0x220
    "user_id" / UUIDAdapter(),               # 0x230
    "root_hash" / Bytes(HASH_SIZE),          # 0x240
    "xvc_hash" / Bytes(HASH_SIZE),           # 0x260
    "xvd_type" / CEnum(Int32ul, **XvdType),  # 0x280
    "content_type" / Int32ul,                # 0x284
    "embedded_xvd_length" / Int32ul,         # 0x288
    "userdata_length" / Int32ul,             # 0x28C
    "xvc_length" / Int32ul,                  # 0x290
    "dynamic_header_length" / Int32ul,       # 0x294
    "block_size" / Int32ul,                  # 0x298
    "ext_entry" / Array(4, XvdExtEntry),     # 0x29C
    "xvd_capabilities" / Bytes(16),          # 0x2FC
    "pe_catalog_hash" / Bytes(HASH_SIZE),    # 0x30C
    "embedded_xvd_pduid" / UUIDAdapter(),    # 0x32C
    Padding(0x10),                           # 0x33C
    "key_material" / Bytes(XVD_KEY_SIZE),    # 0x34C
    "user_data_hash" / Bytes(HASH_SIZE),     # 0x36C
    "sandbox_id" / String(SANDBOX_ID_SIZE),  # 0x38C
    "product_id" / UUIDAdapter(),            # 0x39C
    "build_id" / UUIDAdapter(),              # 0x3AC
    "package_version" / Int64ul,             # 0x3BC
    "pe_catalog_info" / Bytes(0xA0),         # 0x3C4
    "writeable_expiration_data" / Int32ul,   # 0x464
    "writeable_policy_flags" / Int32ul,      # 0x468
    "local_storage_size" / Int32ul,          # 0x46C
    Padding(0x1C),                           # 0x470
    "sequence_number" / Int64sl,             # 0x48C
    "required_systemversion" / Int64ul,      # 0x494
    "odk_keyslot_id" / Int32ul,              # 0x49C
    "reserved" / Padding(0xB60)              # 0x4A0
)


class XvdFile(object):
    struct = XvdFileHeader

    def __init__(self, filepath):
        self.filepath = filepath
        with io.open(filepath, 'rb') as f:
            header_buf = f.read(XVD_HEADER_SIZE)
        if len(header_buf) != XVD_HEADER_SIZE:
            raise Exception('Could not read enough bytes for header')
        if header_buf[0x200: 0x200+8] != XVD_MAGIC:
            raise Exception('Invalid file-magic')
        self.header = self.struct.parse(header_buf)

    def _read_from_file(self, offset, size):
        with io.open(self.filepath, 'rb') as f:
            f.seek(offset, io.SEEK_SET)
            data = f.read(size)
        return data

    @property
    def is_xvc_file(self):
        if self.header.content_type in XvcContentTypes:
            return True
        return False

    @property
    def is_encrypted(self):
        return False if self.header.volume_flags.EncryptionDisabled else True

    @property
    def is_dataintegrity_enabled(self):
        return False if self.header.volume_flags.DataIntegrityDisabled else True

    def extract_embedded_xvd(self):
        if self.header.embedded_xvd_length == 0:
            return None
        return self._read_from_file(3 * 0x1000, self.header.embedded_xvd_length)

    def extract_user_data(self):
        if self.header.userdata_length == 0:
            return None
        return self._read_from_file(self.header.userdata_offset, self.header.userdata_length)

    def print_info(self):
        header = self.header
        print(" -- XvdHeader Info")
        print("Magic: %s" % header.magic)
        print("Content Type: %s (0x%x)" % (XvdContentType[header.content_type], header.content_type))
        #b.AppendLineSpace(fmt + (IsSignedWithRedKey ? "Signed" : "Not signed") + " with red key");
        print("ODK Keyslot Id: %i" % header.odk_keyslot_id)
        print("Flags: %s" % header.volume_flags)
        print("Filetime created: %s" % header.filetime_created)
        print("Drive size: 0x%x" % header.drive_size)
        print("Format version: 0x%x" % header.format_version)
        print("Content Id (VDUID): %s" % header.content_id)
        print("User Id (UDUID): %s" % header.user_id)
        print("Embedded XVD PDUID: %s" % header.embedded_xvd_pduid)
        print("Embedded XVD length: 0x%x" % header.embedded_xvd_length)
        print("User data length: 0x%x" % header.userdata_length)
        print("XVC data length: 0x%x" % header.xvc_length)
        print("Dynamic header length: 0x%x" % header.dynamic_header_length)
        print("Top HashBlock Hash: %s" % hexlify(header.root_hash))
        print("Original XVC data hash: %s" % hexlify(header.xvc_hash))
        print("Sandbox Id: %s" % header.sandbox_id)
        print("Product Id: %s" % header.product_id)
        print("Build Id (PDUID): %s" % header.build_id)
        print("Package version: %i" % header.package_version)
        print("Required System version: %i" % header.required_systemversion)
        print("Sequence number: %i" % header.sequence_number)
        print("Ext XVD Entries: %s" % header.ext_entry)

def main():
    if len(sys.argv) < 2:
        log.error("No filepath argument given!")
        sys.exit(-1)

    filepath = sys.argv[1]

    try:
        xvd_obj = XvdFile(filepath)
    except Exception as e:
        log.error("Parsing file %s failed! Msg: %s" % (filepath, e))
        sys.exit(-2)

    xvd_obj.print_info()

if __name__ == "__main__":
    main()
