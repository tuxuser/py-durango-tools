#!/bin/env python

import sys
import io
import os
import json
import argparse
import logging

from construct import this, Struct, String, PascalString, Array, Padding
from construct import Int8ul, Int16ul, Int32ul, Int64ul, HexDump, Bytes
from common.adapters import PascalStringUtf16, UUIDAdapter, FILETIMEAdapter

logging.basicConfig(format='[%(levelname)s] - %(name)s - %(message)s', level=logging.DEBUG)
log = logging.getLogger('savegame_enum')

BLOB_MAGIC = b'B\x00l\x00o\x00b\x00'
CONTAINERS_INDEX = 'containers.index'

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

ContainerIdxEntry = Struct(
    "filename" / PascalStringUtf16(Int32ul, encoding="utf16"),
    "filename_alt" / PascalStringUtf16(Int32ul, encoding="utf16"),
    "text" / PascalStringUtf16(Int32ul, encoding="utf16"),
    "blob_number" / Int8ul,
    "unknown1" / Int32ul,
    "folder_guid" / UUIDAdapter(),
    "filetime" / FILETIMEAdapter(),
    "unknown2" / HexDump(Bytes(8)),
    "filesize" / Int32ul,
    "unknown3" / HexDump(Bytes(4))
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
    "unknown" / HexDump(Bytes(4)),
    "id" / PascalStringUtf16(Int32ul, encoding="utf16"),
    "files" / Array(this.file_count, ContainerIdxEntry)
)

class SavegameType(object):
    USER = "u"
    MACHINE = "m"

class SavegameEnumerator(object):
    def __init__(self):
        pass

    def _generate_guid_filename(self, guid):
        return "{%s}" % guid.upper()

    def _get_xuid_guid_type_from_foldername(self, foldername):
        elements = foldername.split('_')
        save_type = elements[0]
        if SavegameType.MACHINE == save_type:
            guid = elements[1]
            xuid = "0"
        elif SavegameType.USER == save_type:
            xuid = elements[1]
            guid = elements[2]
        else:
            raise Exception("Encountered unknown savegametype")
        return xuid, guid, save_type

    def _parse_savegameblob(self, path, savegame_guid, blob_num):
        guid_folder = self._generate_guid_filename(savegame_guid)
        blob_name = "container.%i" % blob_num
        filepath = os.path.join(path, guid_folder, blob_name)
        try:
            with io.open(filepath, 'rb') as f:
                data = f.read()
        except FileNotFoundError as e:
            log.warning("Savegame blob %s not existant -> should be there normally!, err: %s" % (savegame_guid, e))
            return
        return ContainerBlob.parse(data)

    def parse_savegamefolders(self, folderlist):
        savegame_content = dict()
        for folderpath in folderlist:
            # foldername: 'u_xuid_guid' or 'm_guid' 
            foldername = os.path.basename(folderpath)
            xuid, guid, save_type = self._get_xuid_guid_type_from_foldername(foldername)
            # Assemble path to CONTAINERS_INDEX
            index_fpath = os.path.join(folderpath, CONTAINERS_INDEX)
            with io.open(index_fpath, 'rb') as f:
                data = f.read()
            log.debug("Parsing folder %s ..." % folderpath)
            parsed_index = ContainerIndex.parse(data)
            log.debug("Parsing %s (AUM: %s, xuid: %s, guid: %s) with %i files" % (
                parsed_index.name, parsed_index.aum_id, xuid, guid, len(parsed_index.files))
            )
            # Initially create guid dict
            if not savegame_content.get(guid):
                savegame_content.update({guid: dict()})
                savegame_content[guid].update({
                    'name': parsed_index.name,
                    'aum_id': parsed_index.aum_id,
                    'type': parsed_index.type,
                    'id': parsed_index.id
                })
            if not savegame_content[guid].get('savegames'):
                savegame_content[guid].update({'savegames':list()})

            for savegame in parsed_index.files:
                if not savegame.filesize:
                    log.debug("Savegame id: %s not available, skipping" % str(savegame.folder_guid))
                    continue
                parsed_blob = self._parse_savegameblob(folderpath, str(savegame.folder_guid), savegame.blob_number)
                if not parsed_blob:
                    continue
                savegame_file = self._generate_guid_filename(str(parsed_blob.file_guid))
                log.debug("Enumerated savegame: %s %s (file: %s/%s)" % (
                    savegame.filename, savegame.text, str(savegame.folder_guid), str(parsed_blob.file_guid)
                ))
                savegame_content[guid]['savegames'].append({
                    'filetime': str(savegame.filetime),
                    'filename': savegame.filename,
                    'filename_alt': savegame.filename_alt,
                    'filesize': savegame.filesize,
                    'text': savegame.text,
                    'folder_guid': str(savegame.folder_guid),
                    'file_guid': str(parsed_blob.file_guid),
                    'xuid': int(xuid),
                    'blob_number': savegame.blob_number,
                    'save_type': save_type
                })
        return savegame_content

    def get_folderlist(self, path):
        filelist = os.listdir(path)
        if CONTAINERS_INDEX in filelist:
            # It's explicit savegame path already
            return list(path)
        else:
            # Enumerate all savegame folder in passed dir by checking for CONTAINERS_INDEX
            filelist = [f for f in filelist if not os.path.isdir(f)]
            filelist = [os.path.abspath(os.path.join(path, f)) for f in filelist]
            filelist = [f for f in filelist if os.path.exists(os.path.join(f, CONTAINERS_INDEX)) ]
            return filelist

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Enumerate savegame directory')
    parser.add_argument('path', type=str, help='input directory')
    parser.add_argument('--output', help='Json report output (otherwise its stdout)')
    args = parser.parse_args()

    if not os.path.exists(args.path):
        log.error("Directory %s does not exist!" % args.path)
        sys.exit(-1)

    log.info("Parsing folder: %s" % args.path)
    enumerator = SavegameEnumerator()
    folderlist = enumerator.get_folderlist(args.path)
    parsed = enumerator.parse_savegamefolders(folderlist)
    if args.output:
        with io.open(args.output, 'w') as f:
            json.dump(parsed, f, indent=2)
    else:
        print(json.dumps(parsed, indent=2))
    log.info('Done! Have a nice day')
