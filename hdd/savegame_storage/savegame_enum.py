#!/bin/env python

import sys
import io
import os
import json
import argparse
import logging

from construct import this, Struct, String, PascalString, Array, Padding
from construct import Int8ul, Int16ul, Int32ul, Int64ul, HexDump, Bytes
from adapters import PascalStringMach2, UUIDAdapter

from uuid import UUID

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
    "guid" / UUIDAdapter()
)

ContainerIdxEntry = Struct(
    "filename" / PascalStringMach2(Int32ul, encoding="utf16"),
    Padding(4),
    "text" / PascalStringMach2(Int32ul, encoding="utf16"),
    "blob_number" / Int8ul,
    "unknown1" / Int32ul,
    "guid" / UUIDAdapter(),
    "unknown2" / HexDump(Bytes(4)),
    "unknown3" / HexDump(Bytes(4)),
    "unknown4" / HexDump(Bytes(8)),
    "unknown5" / HexDump(Bytes(8))
)

"""
Structure of containers.index file
"""
ContainerIndex = Struct(
    "type" / Int32ul,
    "file_count" / Int32ul,
    "name" / PascalStringMach2(Int32ul, encoding="utf16"),
    "aum_id" / PascalStringMach2(Int32ul, encoding="utf16"),
    "unknown1" / HexDump(Bytes(4)),
    "unknown2" / HexDump(Bytes(4)),
    "unknown3" / HexDump(Bytes(4)),
    "id" / PascalStringMach2(Int32ul, encoding="utf16"),
    "files" / Array(this.file_count, ContainerIdxEntry)
)

class SavegameEnumerator(object):
    def __init__(self):
        pass

    def _generate_guid_filename(self, guid):
        return "{%s}" % guid.upper()

    def _get_xuid_and_guid_from_foldername(self, foldername):
        elements = foldername.split('_')
        if len(elements) < 3:
            return None, None
        xuid = elements[1]
        guid = elements[2]
        return xuid, guid

    def _parse_savegameblob(self, path, savegame_guid, blob_num):
        guid_folder = self._generate_guid_filename(savegame_guid)
        blob_name = "container.%i" % blob_num
        filepath = os.path.join(path, guid_folder, blob_name)
        try:
            with io.open(filepath, 'rb') as f:
                data = f.read()
        except FileNotFoundError as e:
            log.warning("Savegame blob %s not existant -> skipping, err: %s" % (savegame_guid, e))
            return
        return ContainerBlob.parse(data)

    def parse_savegamefolders(self, folderlist):
        savegame_content = dict()
        for folderpath in folderlist:
            # foldername: 'u_xuid_guid'
            foldername = os.path.basename(folderpath)
            xuid, guid = self._get_xuid_and_guid_from_foldername(foldername)
            # Assemble path to CONTAINERS_INDEX
            index_fpath = os.path.join(folderpath, CONTAINERS_INDEX)
            with io.open(index_fpath, 'rb') as f:
                data = f.read()
            parsed_index = ContainerIndex.parse(data)
            log.debug("Parsing %s (AUM: %s, xuid: %s, guid: %s) with %i files" % (
                parsed_index.name, parsed_index.aum_id, xuid, guid, len(parsed_index.files))
            )
            # Initially create guid dict
            if not savegame_content.get(guid):
                savegame_content.update({guid: dict()})
            # Initially create xuids dict
            if not savegame_content[guid].get('xuids'):
                savegame_content[guid].update({'xuids': dict()})
            if not savegame_content[guid]['xuids'].get(xuid):
                savegame_content[guid]['xuids'].update({xuid: dict()})
            # Fill the savegame dict
            savegame_content[guid].update({
                'name': parsed_index.name,
                'aum_id': parsed_index.aum_id,
                'type': parsed_index.type,
                'id': parsed_index.id
            })

            for savegame in parsed_index.files:
                parsed_blob = self._parse_savegameblob(folderpath, str(savegame.guid), savegame.blob_number)
                if not parsed_blob:
                    continue
                savegame_file = self._generate_guid_filename(str(parsed_blob.guid))
                log.debug("Enumerated savegame: %s %s (file: %s/%s)" % (
                    savegame.filename, savegame.text, str(savegame.guid), str(parsed_blob.guid)
                ))
                savegame_content[guid]['xuids'][xuid].update({str(savegame.guid): {
                    'filename': savegame.filename,
                    'text': savegame.text,
                    'guid': str(parsed_blob.guid),
                    'blob_number': savegame.blob_number
                }})
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
