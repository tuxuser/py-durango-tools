import logging
from tkinter import filedialog

from gui.option_frame import OptionFrame
from nand.NANDOne import DurangoNand

log = logging.getLogger('gui.flash')


class FlashExplorer(OptionFrame):
    name = 'frame_flash'
    empty_tree_msg = 'Please open a flashdump'
    nand = None
    tree_dict = dict()

    @property
    def _tree_fields(self):
        return [('#0', 'Name', self.sort_col_by_name, {"minwidth": 400, "width": 400}),
                ('block', 'Block', self.sort_col_by_startblock, {"minwidth": 100, "width": 100}),
                ('size', 'Size', self.sort_col_by_size, {"minwidth": 100, "width": 100})]

    @property
    def _button_fields(self):
        return [('open', 'Open image', self.on_click_open),
                ('extract', 'Extract file', self.on_click_extract),
                ('replace', 'Replace file', self.on_click_replace),
                ('delete', 'Delete file', self.on_click_delete)]

    def on_click_open(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        self.nand = DurangoNand(filepath)
        self.set_status('Parsing file...')
        try:
            self.nand.parse()
        except Exception as e:
            self.set_status('Error: %s' % e)
            return
        self.set_status('Parsing finished')

        # Now fill the UI with the info
        self.reset_layout()
        # Free old treeview dict
        self.tree_dict.clear()
        self._populate_treeview()

    def on_click_extract(self):
        pass

    def on_click_replace(self):
        pass

    def on_click_delete(self):
        pass

    def _populate_treeview(self):
        top_iid = self.treeview.insert('', 'end', text='General info')
        self.tree_dict.update({top_iid: self.nand.generate_overview_details()})
        tables = self.nand.tables
        for table in tables:
            filelist = self.nand.get_filelist(table)
            header_offset = self.nand.get_header_rawoffset(table.sequence_version)
            table_text = 'XBFS @ offset 0x%08x // Sequence: %03i // Files: %i' % (
                header_offset, table.sequence_version, len(filelist))
            top_iid = self.treeview.insert('', 'end', text=table_text)
            self.tree_dict.update({top_iid: self.nand.generate_xbfs_details(table)})
            for file_tuple in filelist:
                filename, offset, size = file_tuple
                offset_size = '0x%X 0x%X' % (offset, size)
                iid = self.treeview.insert(top_iid, 'end', text=filename, values=offset_size)
                self.tree_dict.update({iid: self.nand.generate_file_details(file_tuple)})

    def on_treeview_item_select(self, event):
        item = self.treeview.focus()
        text = self.tree_dict.get(item)
        if item == '' or not text:
            self.set_details('No info available')
        else:
            self.set_details(text)

    def sort_col_by_name(self):
        log.debug('Sorting by name')
        pass
    def sort_col_by_startblock(self):
        log.debug('Sorting by startblock')
        pass
    def sort_col_by_size(self):
        log.debug('Sorting by size')
        pass
