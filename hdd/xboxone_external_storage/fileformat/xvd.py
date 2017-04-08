#!/bin/env python

import sys
import io
import logging
from binascii import hexlify, unhexlify

from construct import Struct, Bytes, Padding, String
from construct import Int16ul, Int32ul, Int32sl, Int64ul, Int64sl
from fileformat.common import UUIDAdapter, Constant, Enum
#from common import UUIDAdapter, Constant, Enum

log = logging.getLogger('fileformat.xvd')

XVD_MAGIC = b'msft-xvd'

class XvdContentType(Enum):
    Data = 0
    GameContainer = 1
    SystemOS = 2 # system.xvd / sharedOS
    EraOS = 3 # era.xvd / exclusiveOS
    Scratch = 4
    ResetData = 5
    Application = 6
    HostOS = 7 # host.xvd / hostOS
    # 8
    # 9
    # 0xA
    Updater = 0xB
    UpdaterAlt = 0xC # some updater.xvd files use this
    Template = 0xD # sostmpl.xvd SettingsTemplate.xvd
    # 0xE
    # 0xF
    # 0x10
    # 0x11
    # 0x12
    SystemTools = 0x13
    SystemAux = 0x14
    # 0x15
    # 0x16
    # 0x17
    AppDLC = 0x18 # downloadable content for an application
    GameDLC = 0x19 # downloadable content for a game title
    UniversalDLC = 0x1A # dowloadable content not associated with an application or game
    UWA = 0x21 # UWP App

    def get_string_for_value(content_type):
        try:
            return XvdContentType[content_type]
        except:
            log.warning('ContentEntry: Cannot evaluate content_type 0x%x' % content_type)
            return "Unknown_XvdContentType"

XVD_TYPE_APP = [
    XvdContentType.Application,
    XvdContentType.AppDLC,
    XvdContentType.UWA
]

XVD_TYPE_GAME = [
    XvdContentType.GameContainer,
    XvdContentType.GameDLC
]

XVD_TYPE_SYSTEM = [
    XvdContentType.Data,
    XvdContentType.SystemOS,
    XvdContentType.EraOS,
    XvdContentType.Scratch,
    XvdContentType.ResetData,
    XvdContentType.HostOS,
    XvdContentType.Updater,
    XvdContentType.UpdaterAlt,
    XvdContentType.Template,
    XvdContentType.SystemTools,
    XvdContentType.SystemAux,
]

class XvdVolumeFlags(object):
    ReadOnly =              1
    EncryptionDisabled =    2 # data decrypted, no encrypted CIKs
    DataIntegrityDisabled = 4 # unsigned and unhashed
    SystemFile =            8 #only observed in system files
    Unknown =            0x40 # unsure, never set on unsigned/unhashed files

class XvcLicenseBlockId(object):
    # EKB block ids
    EKB_UNKNOWN1 =       1    # length 0x02, value 0x05
    EKB_KEY_ID_STRING =  2    # length 0x20
    EKB_UNKNOWN2 =       3    # length 0x02, value 0x07
    EKB_UNKNOWN4 =       4    # length 0x01, value 0x31
    EKB_UNKNOWN5 =       5    # length 0x02, value 0x01
    EKB_ENCRYPTED_CIK =  7    # length 0x100
    #SPLicenseBlock block ids
    SP_LICENSE_SECTION =    0x14
    SP_UNKNOWN1 =           0x15
    SP_UNKNOWN2 =           0x16
    SP_UPLINK_KEY_ID =      0x18
    SP_KEY_ID =             0x1A
    SP_ENCRYPTED_CIK =      0x1B
    SP_DISC_ID_SECTION =    0x1C
    SP_UNKNOWN3 =           0x1E
    SP_UNKNOWN4 =           0x24
    SP_DISC_ID =            0x25
    SP_SIGNATURE_SECTION =  0x28
    SP_UNKNOWN5 =           0x29
    SP_UNKNOWN6 =           0x2C
    SP_POSSIBLE_HASH =      0x2A
    SP_POSSIBLE_SIGNATURE = 0x2B

XVD_HEADER_SIZE = 0x1000

XvdFileHeader = Struct(
    "signature" / Bytes(0x200),              # 0x00 - 0x200
    "magic" / Bytes(8),                      # 0x200
    "volume_flags" / Int32ul,                # 0x208
    "format_version" / Int32ul,              # 0x20C
    "filetime_created" / Int64sl,            # 0x210
    "drive_size" / Int64ul,                  # 0x218
    "content_id" / UUIDAdapter(),            # 0x220
    "user_id" / UUIDAdapter(),               # 0x230
    "block_hash" / Bytes(Constant.HASH_SIZE),# 0x240
    "xvcdata_hash" / Bytes(Constant.HASH_SIZE),# 0x260
    "unknown1_hashtablerelated" / Int32ul,   # 0x280
    "content_type" / Int32ul,                # 0x284
    "embedded_xvd_length" / Int32ul,         # 0x288
    "userdata_length" / Int32ul,             # 0x28C
    "xvcdata_length" / Int32ul,              # 0x290
    "dynamic_header_length" / Int32ul,       # 0x294
    "unknown2" / Int32ul,                    # 0x298
    "unknown3" / Bytes(0x60),                # 0x29C
    "pe_catalog_info0" / Int64ul,            # 0x2FC
    "unknown4" / Int64ul,                    # 0x304
    "pe_catalog_info1" / Bytes(0x20),        # 0x30C
    "embedded_xvd_pduid" / UUIDAdapter(),    # 0x32C
    "unknown5" / Bytes(0x10),                # 0x33C
    "encrypted_cik" / Bytes(0x20),           # 0x34C
    "pe_catalog_info2" / Bytes(0x20),        # 0x36C
    "sandbox_id" / String(0x10),             # 0x38C
    "product_id" / UUIDAdapter(),            # 0x39C
    "build_id" / UUIDAdapter(),              # 0x3AC
    "package_version_1" / Int16ul,           # 0x3BC
    "package_version_2" / Int16ul,           # 0x3BE
    "package_version_3" / Int16ul,           # 0x3C0
    "package_version_4" / Int16ul,           # 0x3C2
    "pe_catalog_info3" / Bytes(0xA0),        # 0x3C4
    "unknown6" / Int64ul,                    # 0x464
    "unknown7" / Int32ul,                    # 0x46C
    "unknown8" / Bytes(0x24),                # 0x470
    "required_systemversion_1" / Int16ul,    # 0x494
    "required_systemversion_2" / Int16ul,    # 0x496
    "required_systemversion_3" / Int16ul,    # 0x498
    "required_systemversion_4" / Int16ul,    # 0x49A
    "odk_keyslot_id" / Int32ul,              # 0x49C
    "reserved" / Padding(0xB60)              # 0x4A0
)

class XvdFile(object):
    struct = XvdFileHeader
    def __init__(self, header_buf):
        self._header = None
        if len(header_buf) < XVD_HEADER_SIZE:
            log.error('Passed header_buf smaller than XVD_HEADER_SIZE!')
            log.error('Got: %i, expected: %i bytes' % (len(header_buf), XVD_HEADER_SIZE))
            return
        self._header = self.struct.parse(header_buf)
        if self._header.magic != XVD_MAGIC:
            log.error('Invalid magic for XVD file: %s' % hexlify(self._header.magic))
            self._header = None

    @property
    def header(self):
        return self._header

    @property
    def content_type(self):
        return self._header.content_type

    @property
    def volume_flags(self):
        return self._header.volume_flags

    @property
    def user_id(self):
        return self._header.user_id

    @property
    def product_id(self):
        return self._header.product_id

    @property
    def sandbox_id(self):
        return self._header.sandbox_id

    @property
    def content_id(self):
        return self._header.content_id

    @property
    def is_valid(self):
        if self._header:
            return True

    def print_info(self):
        header = self._header
        print(" -- XvdHeader Info")
        print("Magic: %s" % header.magic)
        print("Content Type: %s (0x%x)" % (XvdContentType[header.content_type], header.content_type))
        #b.AppendLineSpace(fmt + (IsSignedWithRedKey ? "Signed" : "Not signed") + " with red key");
        print("ODK Keyslot Id: %s" % ("test" if header.odk_keyslot_id == 2 else "Unknown"))
        print("Volume flags: 0x%x" % header.volume_flags)
        print("Filetime created: %i" % header.filetime_created)
        print("Drive size: 0x%x" % header.drive_size)
        print("Format version: 0x%x" % header.format_version)
        print("Content Id (VDUID): %s" % header.content_id)
        print("User Id (UDUID): %s" % header.user_id)
        print("Embedded XVD PDUID: %s" % header.embedded_xvd_pduid)
        print("Embedded XVD length: 0x%x" % header.embedded_xvd_length)
        print("User data length: 0x%x" % header.userdata_length)
        print("XVC data length: 0x%x" % header.xvcdata_length)
        print("Dynamic header length: 0x%x" % header.dynamic_header_length)
        print("Top HashBlock Hash: %s" % hexlify(header.block_hash))
        print("Original XVC data hash: %s" % hexlify(header.xvcdata_hash))
        print("Sandbox Id: %s" % header.sandbox_id)
        print("Product Id: %s" % header.product_id)
        print("Build Id (PDUID): %s" % header.build_id)
        print("Package version: %i.%i.%i.%i" % (
            header.package_version_4, header.package_version_3, header.package_version_2, header.package_version_1
        ))
        print("Required System version: %i.%i.%i.%i" % (
            header.required_systemversion_4, header.required_systemversion_3, header.required_systemversion_2, header.required_systemversion_1
        ))
        print("ODK keyslot Id: 0x%x" % header.odk_keyslot_id)
        print("Encrypted CIK: %s" % hexlify(header.encrypted_cik))
        print("Flags:")
        print("  Read-Only" if header.volume_flags & XvdVolumeFlags.ReadOnly else "  Read/Write")
        print("  Decrypted" if header.volume_flags & XvdVolumeFlags.EncryptionDisabled else "  Encrypted")
        print("  Data integrity disabled" if header.volume_flags & XvdVolumeFlags.DataIntegrityDisabled else "  Data integrity enabled")
        if header.volume_flags & XvdVolumeFlags.SystemFile:
            print("  System File")
        print("  Unknown flag 0x40 set" if header.volume_flags & XvdVolumeFlags.Unknown else "  Unknown flag 0x40 not set")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        log.error("No filepath argument given!")
        sys.exit(-1)
    
    filepath = sys.argv[1]
    with io.open(filepath, 'rb') as f:
        buf = f.read(XVD_HEADER_SIZE)

    xvd_obj = XvdFile(buf)
    if not xvd_obj.is_valid:
        log.error("Parsing file %s failed!" % filepath)
        sys.exit(-2)
    
    xvd_obj.print_info()
