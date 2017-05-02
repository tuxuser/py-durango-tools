import os
import logging
from tkinter import filedialog

from gui.option_frame import OptionFrame
from fileformat.xvd import XvdFile, XvdContentType
from hdd.external_storage_enum import XvdHandler

log = logging.getLogger('gui.xvd')


class XvdExplorer(OptionFrame):
    name = 'frame_xvd'
    empty_tree_msg = 'Please open some xvd files'
    xvd_handler = XvdHandler()
    tree_dict = dict()

    @property
    def _tree_fields(self):
        return [('#0', 'Name', self.sort_col_by_name, {"minwidth": 350, "width": 350}),
                ('type', 'Type', self.sort_col_by_type, {"minwidth": 110, "width": 110}),
                ('filepath', 'Path', self.sort_col_by_path, {})]

    @property
    def _button_fields(self):
        return [('open', 'Open files', self.on_click_open),
                ('save', 'Save file', self.on_click_save)]

    def on_click_open(self):
        filepaths = filedialog.askopenfilenames(multiple=True)
        if not filepaths or not len(filepaths):
            return
        filtered_list = self.xvd_handler.get_filtered_foldercontent(filepaths=filepaths)
        self.set_progressbar(max_val=len(filtered_list))
        self.reset_layout()
        # Free old treeview dict
        self.tree_dict.clear()
        for index, filepath in enumerate(filtered_list):
            self.set_progressbar(current=index)
            self.set_status(filepath)
            try:
                xvd = XvdFile(filepath)
            except Exception as e:
                log.debug('%s not valid xvd, Error: %s' % (filepath, e))
                continue
            self._populate_treeview(xvd, filepath)
        # Reset progressbar
        self.set_progressbar()
        self.set_status('Idle')

    def on_click_save(self):
        pass

    def on_treeview_item_select(self, event):
        item = self.treeview.focus()
        text = self.tree_dict.get(item)
        if item == '' or not text:
            self.set_details('No info available')
            return
        self.set_details(text)

    def _populate_treeview(self, xvd, filepath):
        type_str = XvdContentType.get_string_for_value(xvd.header.content_type)
        basename = os.path.basename(filepath)
        iid = self.treeview.insert('', 'end', text=basename, values=(type_str, filepath))
        self.tree_dict.update({iid: self.generate_details_for_xvd(xvd.header)})

    def generate_details_for_xvd(self, xvd_header):
        content_type_str = XvdContentType.get_string_for_value(xvd_header.content_type)
        text = 'XvdType: %s\n' % xvd_header.xvd_type
        text += 'Format: %s\n' % xvd_header.format_version
        text += 'Content Type: %s (%X)\n' % (content_type_str, xvd_header.content_type)
        text += 'Volume Flags: %s\n' % xvd_header.volume_flags
        text += 'ODK Keyslot Id: 0x%x\n' % xvd_header.odk_keyslot_id
        text += 'Created: %s\n' % xvd_header.filetime_created
        text += 'Size: %i MB\n' % (xvd_header.drive_size / 1024 / 1024)
        text += 'Contend Id: %s\n' % xvd_header.content_id
        text += 'User Id: %s\n' % xvd_header.user_id
        text += 'Embedded Xvd PDU Id: %s\n' % xvd_header.embedded_xvd_pduid
        text += 'SandboxId: %s\n' % xvd_header.sandbox_id.decode('utf-8')
        text += 'ProductId: %s\n' % xvd_header.product_id
        text += 'BuildId: %s\n' % xvd_header.build_id
        text += 'Package Version: %s\n' % xvd_header.package_version
        text += 'Req SysVersion: %s\n' % xvd_header.required_systemversion
        text += 'Sequence number: 0x%x\n' % xvd_header.sequence_number
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
