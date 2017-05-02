#!/bin/env python

import sys
import io
import os
import json
import argparse
import logging
import uuid

from fileformat.savegame_container import ContainerIndex, ContainerBlob, CONTAINERS_INDEX

logging.basicConfig(format='[%(levelname)s] - %(name)s - %(message)s', level=logging.DEBUG)
log = logging.getLogger('savegame_enum')


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

    @staticmethod
    def generate_guid_filename(guid):
        if isinstance(guid, uuid.UUID):
            guid = str(guid)
        return "{%s}" % guid.upper()

    @staticmethod
    def get_xuid_guid_from_folderpath(folderpath):
        # foldername: 'u_xuid_guid' or 'm_guid'
        foldername = os.path.basename(folderpath)
        elements = foldername.split('_')
        save_type = elements[0]
        # Machine
        if "m" == save_type:
            guid = elements[1]
            xuid = "0"
        # User
        elif "u" == save_type:
            xuid = elements[1]
            guid = elements[2]
        else:
            raise Exception("Encountered unknown savegametype")
        return xuid, guid

    @staticmethod
    def generate_savegame_path(folderpath, folder_guid, savegame_guid):
        path = os.path.join(folderpath, SavegameEnumerator.generate_guid_filename(folder_guid))
        path = os.path.join(path, SavegameEnumerator.generate_guid_filename(savegame_guid))
        return path

    @staticmethod
    def generate_savegameblob_path(folderpath, folder_guid, blob_number):
        guid = SavegameEnumerator.generate_guid_filename(folder_guid)
        blob_name = "container.%i" % blob_number
        return os.path.join(folderpath, guid, blob_name)

    @staticmethod
    def generate_containerindex_path(folderpath):
        return os.path.join(folderpath, CONTAINERS_INDEX)

    @staticmethod
    def parse_savegameblob(filepath):
        try:
            with io.open(filepath, 'rb') as f:
                data = f.read()
        except FileNotFoundError as e:
            log.error("parse_savegameblob: %s" % e)
            return
        return ContainerBlob.parse(data)

    @staticmethod
    def parse_containterindex(filepath):
        try:
            with io.open(filepath, 'rb') as f:
                data = f.read()
        except FileNotFoundError as e:
            log.error("parse_containerindex: %s" %  e)
            return
        return ContainerIndex.parse(data)

    @staticmethod
    def parse_rootfolder(folderpath):
        xuid, guid = SavegameEnumerator.get_xuid_guid_from_folderpath(folderpath)
        log.debug("Parsing folder %s ..." % folderpath)
        # Assemble path to CONTAINERS_INDEX
        index_fpath = SavegameEnumerator.generate_containerindex_path(folderpath)
        index = SavegameEnumerator.parse_containterindex(index_fpath)
        if not index:
            log.error("Container Index %s not existant -> should be there normally!" % index_fpath)
            return
        log.debug("Parsing %s (AUM: %s, xuid: %s, guid: %s) with %i files" % (
            index.name, index.aum_id, xuid, guid, len(index.files))
        )
        return xuid, guid, index

    @staticmethod
    def parse_savegame(rootpath, savegame):
        if not savegame.filesize:
            log.debug("Savegame id: %s not available, skipping" % savegame.folder_guid)
            return
        blob_path = SavegameEnumerator.generate_savegameblob_path(rootpath, savegame.folder_guid, savegame.blob_number)
        parsed_blob = SavegameEnumerator.parse_savegameblob(blob_path)
        if not parsed_blob:
            log.error("Savegame blob %s not existant -> should be there normally!" % blob_path)
            return
        log.debug("Enumerated savegame: %s %s" % (savegame.filename, savegame.text))
        return parsed_blob

    def parse_savegamefolders(self, folderlist):
        for folderpath in folderlist:
            ret = self.parse_rootfolder(folderpath)
            if not ret:
                continue
            xuid, guid, index = ret
            for savegame in index.files:
                blob = self.parse_savegame(folderpath, savegame)
                if not blob:
                    continue
                savegame_path = self.generate_savegame_path(folderpath, savegame.folder_guid, blob.file_guid)
                self._save_to_dict(index, savegame, blob, guid, xuid, savegame_path)
        return self.savegame_content

    @staticmethod
    def get_folderlist(path):
        filelist = os.listdir(path)
        if CONTAINERS_INDEX in filelist:
            # It's explicit savegame path already
            return list(path)
        else:
            # Enumerate all savegame folder in passed dir by checking for CONTAINERS_INDEX
            filelist = [os.path.abspath(os.path.join(path, f)) for f in filelist]
            print(filelist)
            filelist = [f for f in filelist if os.path.exists(os.path.join(f, CONTAINERS_INDEX))]
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