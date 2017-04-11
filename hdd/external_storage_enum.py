#!/bin/env python

import sys
import io
import os
import json
import argparse
import logging

from fileformat.xvd import XvdFile, XvdContentType
from fileformat.xvd import XVD_HEADER_SIZE, XVD_TYPE_APP, XVD_TYPE_GAME

from xbox_webapi.authentication.auth import AuthenticationManager
from xbox_webapi.common.exceptions import AuthenticationException
from xbox_webapi.api.provider import XboxLiveClient
from xbox_webapi.api.eds.types import MediaGroup

logging.basicConfig(format='[%(levelname)s] - %(name)s - %(message)s', level=logging.DEBUG)
log = logging.getLogger('content_enum')

XVI_EXTENSION = ".xvi"
LAST_CONSOLE_FILE = "LastConsole"
TOKEN_DIR = "tokenstore.json"

ALL_MEDIAGROUPS = [MediaGroup.GAME_TYPE, MediaGroup.APP_TYPE]
DESIRED_FIELDS_SCRAPE = ['Images','VuiDisplayName']

class EDSScraper(object):
    '''
    Scraper for Entertainment Discovery Service (EDS)
    API documentation available at:
    https://developer.microsoft.com/en-us/games/xbox/docs/xboxlive/rest/atoc-reference-marketplace
    '''
    def __init__(self):
        self.xbl_client = None

    def _chunks(self, seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    def create_client(self, email=None, password=None):
        auth_result = None
        auth_mgr = AuthenticationManager(TOKEN_DIR)
        try:
            tokenstore = auth_mgr.authenticate(email_address=email, password=password)
        except AuthenticationException as e:
            log.error(e)
            return False
        userinfo = tokenstore.userinfo
        self.xbl_client = XboxLiveClient(userinfo.userhash, tokenstore.xsts_token, userinfo.xuid)
        return True

    def scrape_details(self, id_string, media_group):
        resp = self.xbl_client.eds.get_details(id_string, media_group,
            desired=self.xbl_client.eds.SEPERATOR.join(DESIRED_FIELDS_SCRAPE)
        )
        if resp.status_code != 200:
            log.error("Invalid EDS details response for %s" % id_string)
            return

        items = resp.json().get('Items')
        if not items:
            log.error("Failed getting details for %s" % id_string)
            return
        return items

    def scrape(self, content_list):
        '''
        Takes a list of tuples: (MediaGroup.Member, ContentEntry)
        '''
        for media_group in ALL_MEDIAGROUPS:
            entry_list = content_list.get(media_group)
            log.info('Scraping %i %s containers' % (len(entry_list), media_group))
            # Split content entires list in chunks of 10
            for chunk in self._chunks(entry_list, 10):
                # Assemble a list of just product_id strings
                product_id_list = [e.get('product_id') for e in chunk]
                # Scrape data from EDS 
                details = self.scrape_details(product_id_list, media_group)
                if not details:
                    log.error('Failed scraping %s' % product_id_list)
                    continue
                
                # Find matching node for id in returned list of items
                for entry in chunk:
                    matched_item = next((item for item in details if item['ID'] == entry['product_id']), None)
                    if not matched_item:
                        log.warning('No data for id: %s available it seems' % entry['product_id'])
                        continue
                    entry['name'] = matched_item.get('Name') 
                    entry['display_name'] = matched_item.get('VuiDisplayName')
                    entry['media_item_type'] = matched_item.get('MediaItemType')
                    entry['image_boxart'] = matched_item.get('Images', [{}])[0].get('Url')
        return content_list

class DurangoContentDirectory(object):
    def __init__(self, folderpath):
        self._rootpath = folderpath
    
    @property
    def folderpath(self):
        return self._rootpath

    def create_xvd_object(self, filepath):
        with io.open(filepath, 'rb') as f:
            size = f.seek(0,2)
            if size < XVD_HEADER_SIZE:
                return
            f.seek(0)
            buf = f.read(XVD_HEADER_SIZE)
        return XvdFile(buf)

    def get_media_group_for_type(self, content_type):
        if content_type in XVD_TYPE_APP:
            return MediaGroup.APP_TYPE
        elif content_type in XVD_TYPE_GAME:
            return MediaGroup.GAME_TYPE
        else:
            log.warning('Cannot find media group for content-type: 0x%x' % content_type)
            return None

    def show_parse_progress(self, total, current):
        percent = total / 100
        if total % (percent*10):
            print("\r%i percent completed (%i/%i)" % ((current / percent), current, total), end="\r")

    def parse(self):
        files = dict()
        for group in ALL_MEDIAGROUPS:
            files.update({group: list()})
        # Filter filelist initially - We only want files, no (sub)dirs, not LastConsole file
        get_filext = lambda f: os.path.splitext(f)[1].lower()
        filelist = [f for f in os.listdir(self._rootpath) if not os.path.isfile(f)]
        filelist = [f for f in filelist if f != LAST_CONSOLE_FILE]
        filelist = [f for f in filelist if get_filext(f) != XVI_EXTENSION]
        total_count = len(filelist)
        for idx, filename in enumerate(filelist):
            filepath = os.path.join(self._rootpath, filename)
            self.show_parse_progress(total_count, idx)
            xvd = self.create_xvd_object(filepath)
            if not xvd or not xvd.is_valid:
                continue
            media_group = self.get_media_group_for_type(xvd.content_type)
            entry = {
                'filepath': filepath,
                'product_id': str(xvd.product_id),
                'content_type': xvd.content_type,
                'type': XvdContentType.get_string_for_value(xvd.content_type)
            }
            files[media_group].append(entry)
        return files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Enumerate external hdd content')
    parser.add_argument('path', type=str, help='input path to external drive')
    parser.add_argument('--output', help='Json report output (otherwise its stdout)')
    args = parser.parse_args()

    if not os.path.exists(args.path):
        log.critical("Directory %s does not exist!" % args.path)
        sys.exit(-2)

    log.info("Parsing folder: %s" % args.path)
    content_dir = DurangoContentDirectory(args.path)
    content_list = content_dir.parse()

    for group in ALL_MEDIAGROUPS:
        log.info('Found %i %s containers...' % (
            len(content_list[group]), group
        ))

    scraper = EDSScraper()
    log.debug("Initializing EDS Scraper...")
    log.info("Need to login to XBL now...")
    log.info("If you already did that successfully lately, tokens were saved")
    log.info("In that case: Just press ENTER when you asked for credentials")

    email = input("Microsoft Account Email: ")
    password = input("Password: ")
    ret = scraper.create_client(email, password)
    if not ret:
        log.error('Failed to initialize EDS Scraper!')
        sys.exit(-3)

    log.info('Scraping details for content...')
    scraped = scraper.scrape(content_list)
    if args.output:
        with io.open(args.output, 'w') as f:
            json.dump(scraped, f, indent=2)
    else:
        print(json.dumps(scraped, indent=2))
    log.info('Done! Have a nice day')
