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
from common.enum import Enum

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
    "save_type" / Int32ul,
    "folder_guid" / UUIDAdapter(),
    "filetime" / FILETIMEAdapter(),
    "unknown2" / Int64ul,
    "filesize" / Int32ul,
    "unknown3" / Int32ul
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

class SavegameType(Enum):
    USER = 1
    MACHINE = 5

class SavegameEnumerator(object):
    def __init__(self):
        self.savegame_content = dict()

    def _save_to_dict(self, parsed_index, savegame, parsed_blob, guid, xuid, savegame_path):
        # Initially create guid dict
        guid = guid.lower()
        if not self.savegame_content.get(guid):
            self.savegame_content.update({guid: dict()})
            self.savegame_content[guid].update({
                'name': parsed_index.name,
                'aum_id': parsed_index.aum_id,
                'type': parsed_index.type,
                'id': parsed_index.id
            })
        if not self.savegame_content[guid].get('savegames'):
            self.savegame_content[guid].update({'savegames':list()})
        self.savegame_content[guid]['savegames'].append({
            'filetime': str(savegame.filetime),
            'filename': savegame.filename,
            'filename_alt': savegame.filename_alt,
            'filesize': savegame.filesize,
            'text': savegame.text,
            'folder_guid': str(savegame.folder_guid),
            'file_guid': str(parsed_blob.file_guid),
            'xuid': int(xuid),
            'blob_number': savegame.blob_number,
            'save_type': savegame.save_type,
            'filepath': savegame_path
        })

    def _generate_guid_filename(self, guid):
        return "{%s}" % guid.upper()

    def _get_xuid_guid_from_folderpath(self, folderpath):
        # foldername: 'u_xuid_guid' or 'm_guid'
        foldername = os.path.basename(folderpath)
        elements = foldername.split('_')
        save_type = elements[0]
        if "m" == save_type: # machine
            guid = elements[1]
            xuid = "0"
        elif "u" == save_type: # user
            xuid = elements[1]
            guid = elements[2]
        else:
            raise Exception("Encountered unknown savegametype")
        return xuid, guid

    def _generate_savegame_path(self, folderpath, folder_guid, savegame_guid):
        path = os.path.join(folderpath, self._generate_guid_filename(folder_guid))
        path = os.path.join(path, self._generate_guid_filename(savegame_guid))
        return path

    def _generate_savegameblob_path(self, folderpath, folder_guid, blob_number):
        guid = self._generate_guid_filename(folder_guid)
        blob_name = "container.%i" % blob_number
        return os.path.join(folderpath, guid, blob_name)

    def _generate_containerindex_path(self, folderpath):
        return os.path.join(folderpath, CONTAINERS_INDEX)

    def parse_savegameblob(self, filepath):
        try:
            with io.open(filepath, 'rb') as f:
                data = f.read()
        except FileNotFoundError as e:
            log.error("parse_savegameblob: %s" % e)
            return
        return ContainerBlob.parse(data)

    def parse_containterindex(self, filepath):
        try:
            with io.open(filepath, 'rb') as f:
                data = f.read()
        except FileNotFoundError as e:
            log.error("parse_containerindex: %s" %  e)
            return
        return ContainerIndex.parse(data)

    def parse_savegamefolders(self, folderlist):
        for folderpath in folderlist:
            xuid, guid = self._get_xuid_guid_from_folderpath(folderpath)
            log.debug("Parsing folder %s ..." % folderpath)
            # Assemble path to CONTAINERS_INDEX
            index_fpath = self._generate_containerindex_path(folderpath)
            parsed_index = self.parse_containterindex(index_fpath)
            if not parsed_index:
                log.error("Container Index %s not existant -> should be there normally!" % index_fpath)
                continue
            log.debug("Parsing %s (AUM: %s, xuid: %s, guid: %s) with %i files" % (
                parsed_index.name, parsed_index.aum_id, xuid, guid, len(parsed_index.files))
            )
            for savegame in parsed_index.files:
                folder_guid = str(savegame.folder_guid)
                if not savegame.filesize:
                    log.debug("Savegame id: %s not available, skipping" % folder_guid)
                    continue
                blob_path = self._generate_savegameblob_path(folderpath, folder_guid, savegame.blob_number)
                parsed_blob = self.parse_savegameblob(blob_path)
                if not parsed_blob:
                    log.error("Savegame blob %s not existant -> should be there normally!" % blob_path)
                    continue
                file_guid = str(parsed_blob.file_guid)
                savegame_path = self._generate_savegame_path(folderpath, folder_guid, file_guid)
                log.debug("Enumerated savegame: %s %s (file: %s)" % (
                    savegame.filename, savegame.text, savegame_path
                ))
                self._save_to_dict(parsed_index, savegame, parsed_blob, guid, xuid, savegame_path)
        return self.savegame_content

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
    
    def get_title_node(self, guid=None, product_id=None, aum_id=None):
        if not guid and not aum_id:
            log.error('Need either guid, product_id or aum_id to locate title')
            return
        if guid:
            guid = guid.lower()
            node = self.savegame_content.get(guid)
        elif product_id:
            product_id = product_id.lower()
            node = next((item for item in self.savegame_content.values() if item['id'] == product_id), None)
        elif aum_id:
            node = next((item for item in self.savegame_content.values() if item['aum_id'] == aum_id), None)
        return node

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