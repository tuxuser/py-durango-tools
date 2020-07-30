import os
import logging
from tkinter import filedialog

from durango.gui.option_frame import OptionFrame
from durango.fileformat.savegame_container import SavegameType
from durango.hdd.savegame_enum import SavegameEnumerator

log = logging.getLogger('gui.savegames')


class SavegameExplorer(OptionFrame):
    name = 'frame_savegames'
    empty_tree_msg = 'Please open the savegame directory'
    savegame_handler = SavegameEnumerator()
    tree_dict = dict()

    @property
    def _tree_fields(self):
        return [('#0', 'Name', self.sort_col_by_name, {'minwidth': 250, 'width': 250}),
                ('type', 'type', self.sort_col_by_type, {'minwidth': 80, 'width': 80}),
                ('xuid', 'xuid', self.sort_col_by_path, {'minwidth': 100, 'width': 100})]

    @property
    def _button_fields(self):
        return [('open', 'Open directory', self.on_click_open),
                ('extract', 'Extract file', self.on_click_extract),
                ('replace', 'Replace file', self.on_click_replace),
                ('inject', 'Inject file', self.on_click_inject),
                ('delete', 'Delete file', self.on_click_delete)]

    def on_click_open(self):
        dirpath = filedialog.askdirectory(title='Choose savegame topdirectory', mustexist=True)
        if not dirpath:
            return
        # Filter for valid subdirs
        folderlist = self.savegame_handler.get_folderlist(dirpath)
        self.set_progressbar(max_val=len(folderlist))
        self.reset_layout()
        for index, folderpath in enumerate(folderlist):
            self.set_progressbar(current=index)
            self.set_status(folderpath)
            ret = self.savegame_handler.parse_rootfolder(folderpath)
            if not ret:
                continue
            xuid, guid, index = ret
            parsed_saves = list()
            for savegame in index.files:
                blob = self.savegame_handler.parse_savegame(folderpath, savegame)
                if not blob:
                    continue
                parsed_saves.append((savegame, blob))
            self._populate_treeview(folderpath, xuid, guid, index, parsed_saves)

        # Reset progressbar
        self.set_progressbar()
        self.set_status('Finished')

    def on_click_extract(self):
        pass

    def on_click_replace(self):
        pass

    def on_click_inject(self):
        pass

    def on_click_delete(self):
        pass

    def _populate_treeview(self, folderpath, xuid, guid, index, saves_blob_list):
        top_iid = self.treeview.insert('', 'end', text=index.name)
        self.tree_dict.update({top_iid: self.generate_details_for_index(folderpath, index, guid)})
        for savegame, blob in saves_blob_list:
            savetype_str = SavegameType.get_string_for_value(savegame.save_type)
            iid = self.treeview.insert(top_iid, 'end', text=savegame.filename, values=(savetype_str, xuid))
            self.tree_dict.update({iid: self.generate_details_for_savegame(savegame, blob)})

    def on_treeview_item_select(self, event):
        item = self.treeview.focus()
        text = self.tree_dict.get(item)
        if item == '' or not text:
            self.set_details('No info available')
        else:
            self.set_details(text)

    def generate_details_for_index(self, folderpath, index, guid):
        text = 'Aum Id: %s\n' % index.aum_id
        text += 'ScId: %s\n' % guid
        text += 'Folder: %s\n' % os.path.basename(folderpath)
        text += 'Id: %s\n' % index.id
        text += 'Filecount: %i\n' % index.file_count
        text += 'Created: %s\n' % index.filetime
        text += 'Unknown: %i\n' % index.unknown
        return text

    def generate_details_for_savegame(self, savegame, blob):
        savegame_path = self.savegame_handler.generate_savegame_path('', savegame.folder_guid, blob.file_guid)
        blob_path = self.savegame_handler.generate_savegameblob_path('', savegame.folder_guid, savegame.blob_number)
        savetype_str = SavegameType.get_string_for_value(savegame.save_type)
        text = 'Filename: %s\n' % savegame.filename
        text += 'Text: %s\n' % savegame.filename_alt
        text += 'Filesize: %i bytes\n' % savegame.filesize
        text += 'Path: %s\n' % savegame_path
        text += 'Blob Path: %s\n' % blob_path
        text += 'Type: %s (%i)\n' % (savetype_str, savegame.save_type)
        text += 'Created: %s\n' % savegame.filetime
        text += 'Entry Unknown: %i\n' % savegame.unknown
        text += 'Entry Unknown2: %i\n' % savegame.unknown2
        text += 'Blob Unknown: %i\n' % blob.unknown
        text += 'Blob Unknown2: %i\n' % blob.unknown2
        return text

    def sort_col_by_name(self):
        log.debug('Sorting by name')
        pass
    def sort_col_by_type(self):
        log.debug('Sorting by type')
        pass
    def sort_col_by_path(self):
        log.debug('Sorting by path')
        pass
