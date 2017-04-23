import binascii
import os
import logging
import tkinter
from tkinter import ttk
from tkinter import messagebox, filedialog, Menu

from fileformat.xvd import XvdFile, XvdContentType
from hdd.external_storage_enum import DurangoContentDirectory
from nand.NANDOne import DurangoNand, FlashFiles

logging.basicConfig(format='[%(levelname)s] - %(name)s - %(message)s', level=logging.DEBUG)
log = logging.getLogger('gui.toolbox')

"""
        # Create menu
        menubar = Menu(self)
        menu_app = Menu(menubar, name='apple')
        menu_app.add_command(label='About')
        menu_app.add_separator()
        menu_open = Menu(menubar, name='open')
        menu_open.add_command(label='Harddrive')
        menu_open.add_command(command=self.open_directory, label='Directory')
        menu_open.add_command(command=self.open_files, label='Files')
        menu_file = Menu(menubar, name='file')
        menu_file.add_cascade(menu=menu_open, label='Open...')
        menu_file.add_command(label='Save report')
        menu_file.add_command(label='Toggle drivemode')
        menu_file.add_command(label='Exit')

        menubar.add_cascade(menu=menu_app)
        menubar.add_cascade(menu=menu_file, label='File')
        # Disable teardown
        self.master.option_add('*tearOff', False)
        # Assign master menubar
        self.master.config(menu=menubar)
"""

class FlashExplorer(object):
    def __init__(self, master):
        self.master = master
        self.nand = None

    @property
    def tablefields(self):
        return [('offset','Offset'),('size','Size')]

    @property
    def buttons(self):
        return [('Open', self.on_click_open),
                ('Extract', self.on_click_extract),
                ('Reset', self.on_click_reset)
        ]

    def init_layout(self):
        self.master.set_table(self.tablefields)
        self.master.set_buttons(self.buttons)
        self.master.table.insert('', 'end', text='Please load a flashdump')

        self.master.set_details('HEY', None)
        self.master.set_status('Idle')

    def on_click_open(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        self.nand = DurangoNand(filepath)
        self.master.set_status('Parsing file...')
        try:
            self.nand.parse()
        except Exception as e:
            self.master.set_status('Error: %s' % e)
            return
        sequence_version = self.nand.get_latest_sequence_version()
        # Now fill the UI with the info
        self.master.empty_table()
        self._insert_treeview(sequence_version)
        self._set_details(sequence_version)

    def on_click_extract(self):
        pass
    def on_click_reset(self):
        pass

    def _insert_treeview(self, sequence_num):
        table = self.nand.get_xbfs_table_by_sequence(sequence_num)
        for filename in FlashFiles:
            fil = self.nand.get_xbfs_fileentry_by_name(filename, table)
            if not fil:
                continue
            values = '%08x %08x' % (fil.offset, fil.size)
            self.master.table.insert('', 'end', text=filename, values=values)

    def _set_details(self, sequence_num):
        table = self.nand.get_xbfs_table_by_sequence(sequence_num)
        text = ''
        text += 'Dump Type: %s\n' % self.nand.dump_type
        text += 'Xbox Boot Filesystem\n'
        text += 'Header offset: 0x%08x\n' % self.nand.get_header_rawoffset(sequence_num)
        text += 'Format version: %s\n' % table.format_version
        text += 'Sequence version: %s\n' % table.sequence_version
        text += 'Layout version: %s\n' % table.layout_version
        text += 'GUID: %s\n' % str(table.guid)
        #text += 'Hash\n'
        #text += '%s\n' % binascii.hexlify(table.hash).decode('utf-8')
        text += 'Blocks used\n'
        text += 'Blocks free\n'
        self.master.set_details(text, None)

class XvdExplorer(object):
    def __init__(self, master):
        self.master = master
        self.content = DurangoContentDirectory()

    @property
    def tablefields(self):
        return [('type','Type'),('filepath','Path')]
    
    @property
    def buttons(self):
        return [('O', self.on_click_open),
                ('Extract', self.on_click_extract),
                ('Reset', self.on_click_reset),
                ('Hi', self.on_click_reset)
        ]

    def init_layout(self):
        self.master.set_table(self.tablefields)
        self.master.set_buttons(self.buttons)

        self.master.table.insert('', 'end', text='Please load some xvd')

        self.master.set_details('HEY', None)
        self.master.set_status('Idle')

    def on_click_open(self):
        import time
        filepaths = filedialog.askopenfilenames(multiple=True)
        if not filepaths or not len(filepaths):
            return
        filtered_list = self.content.get_filtered_foldercontent(filepaths=filepaths)
        self.master.set_progressbar(max=len(filtered_list))
        self.master.empty_table()
        for index, filepath in enumerate(filtered_list):
            self.master.set_progressbar(current=index)
            self.master.set_status(filepath)
            xvd = self.content.create_xvd_object(filepath)
            if not xvd or not xvd.is_valid:
                continue
            self._insert_treeview(xvd, filepath)
        # Reset progressbar
        self.master.set_progressbar()
        self.master.set_status('Idle')

    def on_click_extract(self):
        pass
    def on_click_reset(self):
        pass

    def _insert_treeview(self, xvd, filepath):
        media_group = self.content.get_media_group_for_type(xvd.content_type)
        type_str = XvdContentType.get_string_for_value(xvd.content_type)
        basename = os.path.basename(filepath)
        self.master.table.insert('', 'end', text=basename, values=(type_str, filepath))

    def _set_details(self, xvd_obj):
        text = ''
        text += 'Content Type: %s\n' % xvd.content_type
        text += 'Format: %s\n' % xvd.format_version
        text += 'Volume Flags: %s\n' % xvd.volume_flags
        text += 'Created: %s\n' % xvd.filetime_created
        text += 'Size: %s\n' % xvd.drive_size
        text += 'CID: %s\n' % xvd.content_id
        text += 'UID: %s\n' % xvd.user_id
        text += 'XVD PDUID: %s\n' % xvd.embedded_xvd_pduid
        text += 'SandboxId: %s\n' % xvd.sandbox_id
        text += 'ProductId: %s\n' % xvd.product_id
        text += 'BuildId: %s\n' % xvd.build_id
        text += 'Package Version: %\n' % xvd.package_version
        text += 'Req SysVersion: %s\n' % xvd.required_systemversion
        self.master.set_details(text, None)

class SavegameExplorer(object):
    def __init__(self, master):
        self.master = master

    @property
    def buttons(self):
        return [('Open', self.on_click_open),
                ('Extract', self.on_click_extract),
                ('Reset', self.on_click_reset)
        ]

    def init_layout(self):
        self.master.set_buttons(self.buttons)
        pass
    def on_click_open(self):
        pass
    def on_click_extract(self):
        pass
    def on_click_reset(self):
        pass
    def _parse(self):
        pass

class App(ttk.Frame):
    max_progress = 0
    def __init__(self, master):
        ttk.Frame.__init__(self, master)

        self.grid(column=0, row=0, sticky=('n','e','s','w'))
        self.details_image = None
        self.details_text = tkinter.StringVar()
        self.status_text = tkinter.StringVar()

        self.master.title('Durango Toolbox')
        self.master.resizable(False, False)
        
        self.xvd_layout = XvdExplorer(self)
        self.flash_layout = FlashExplorer(self)
        self.savegame_layout = SavegameExplorer(self)

        self.hdd_symbol = tkinter.PhotoImage(data="R0lGODlhQABAAPAAAAAAAAEAAiH5BAEAAAAALAAAAABAAEAAAAL+hI8Qy+0PI0y0KomzbrbvDzqdFZbfWJkqhlLr+7QJTC8yUtP3kcO70Xv9LkHTsKg6IkvKJajp3EBDHubPKnteT1NJNzLEZb6xsNi7ZZln6N147QKnJ/AU3S2v20Vzvj7ud5P3B8hARkgSmFWGWGjT99jo+IVnKMgBGXCpWGVZ6YkyOMIZSrpnOgm5icoGuoj5Clvq2nI3KzuKW8u4GxmrmSl5CvxJK8n7a4yI3Muqx3zrvGabrFwn2gx9TZ2tbda2iv0NXu0dbj5MnindKrWO7uge/VZMFS9/HqU+ry+e208vH0B2Zwb662SQG7+EvsoxJPPwXUKIEyUapHixQgEAOw==")
        self.floppy_symbol = tkinter.PhotoImage(data="R0lGODlhQABAAPAAAAAAAAAAACH5BAEAAAAALAAAAABAAEAAAAL+hB2py+0P1Zkn1IizXnRasIXi0yHIiKLll7ZiZ7nyRsXzHXkgzjvVnikJh8SLDwTMFZfMk8+GaXpeRpJGWr1OrUFsUptlfEneUQ0yPmLN22d3TQ1zwFK2XEJv2p3uaDnO15Am+BdyxuUHZ3iH91YHGJXnVYjoOKkX2aPZt9kJ5bk5CDojOupSapqCmmrG2oN6GbsKK3uZiVY7eauWSymoxHhzyEkYTNr2i2ssM5xMtnyKLAYcqNk8rVz9Kj2XvRodXHq9HU793TLe+KzNk54gzt0e/24+6v5ZzI5zDw+NPo9PDMBj5bzZA9hPnzCE9UDxa+jpoUGHDCdGrLjunCoejLw0quCYz+MeeBY7uQvnbyMjlAoJ6ot3z+UgAwUAADs=")
        self.microchip_symbol = tkinter.PhotoImage(data="R0lGODlhQABAAPAAAAAAAAEAAiH5BAEAAAAALAAAAABAAEAAAAL+hI+ZgWzhXotQ2YsVdPtV0HnHl5Um+IUqyUbnq6Uy144ujKP07lF+DtT1hkKRMQhb8YooGxLXotl+x6f1is1qc5uu9wsO367isjmcPavXYy77XbbC52A5/R4C4vftEx+PgdbzBzdoNkX4ZkhykTiH5FgYFKnYWLdIKYYpqJN52Jln6fmpN0rqZqoZ+IWYygoat+m60wXrM/t6uYrrBcnbu1sr6zoMbIuLadv6m5zxa4z63Nd8PFssXE2srCuthC0q7dvt/Jqdep3XPVPLrU4N/iweLs9Mz/s0bnePta91vgUwoMCBBAu+iHIkHRWDSogodGKwSEMmNSJOnNikCsESizMgZmTYUWLFjwU5LvnI6EQBADs=")

        ####### COLUMN 0 #######
        # Sidebar
        frm_sidebar = ttk.Frame(self)
        frm_sidebar.grid(column=0, row=0)

        sidebar_xvd = ttk.Button(frm_sidebar, image=self.hdd_symbol,
                                command=self.xvd_layout.init_layout)
        sidebar_flash = ttk.Button(frm_sidebar, image=self.microchip_symbol,
                                command=self.flash_layout.init_layout)
        sidebar_savegame = ttk.Button(frm_sidebar, image=self.floppy_symbol,
                                command=self.savegame_layout.init_layout)
        sidebar_xvd.grid(row=0)
        sidebar_flash.grid(row=1)
        sidebar_savegame.grid(row=2)

        # Status + progress bar
        frm_progress = ttk.Frame(self)
        frm_progress.grid(column=0, row=1, columnspan=5)
        lbl_status = ttk.Label(frm_progress, textvariable=self.status_text, anchor='w', width=30)
        lbl_status.grid(column=0, row=0, sticky=('w'))
        self.progressbar = ttk.Progressbar(frm_progress, orient=tkinter.HORIZONTAL, mode='determinate', length=300)
        self.progressbar.grid(column=1, row=0, sticky=('w'))

        ###### COLUMN 1 ######
        # Details labels
        lbl_details = ttk.Label(self, textvariable=self.details_text,
                                image=self.details_image,
                                compound='top', anchor='w', width=50)
        lbl_details.grid(column=1, row=0)

        ##### COLUMN 2 ########
        # table
        self.table = ttk.Treeview(self, selectmode='browse',padding=3)
        self.table.grid(column=2, row=0, sticky=('n', 's'))

        ##### COLUMN 3 ########
        # scrollbar
        scrollbar = tkinter.Scrollbar(self, orient=tkinter.VERTICAL)
        scrollbar.grid(column=3, row=0, sticky=('n', 's'))
        scrollbar.configure(command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)

        ##### COLUMN 4 #######
        # Buttons
        self.frm_buttons = ttk.Frame(self)
        self.frm_buttons.grid(column=4, row=0)

        # Click sidebar item 'XVD'
        sidebar_flash.invoke()

    def open_directory(self, event=None):
        dirname = filedialog.askdirectory(mustexist=True)
        folder_content = self.xvd_dir.get_filtered_foldercontent(dirname)
        log.info(folder_content)
    
    def open_files(self, event=None):
        folder_content = filedialog.askopenfilenames(multiple=True)
        log.info(folder_content)

    def set_details(self, text, image):
        self.details_image = image
        self.details_text.set(text)

    def set_buttons(self, button_list):
        for index, value in enumerate(button_list):
            name, command = value
            ttk.Button(self.frm_buttons, text=name, command=command).grid(row=index)

    def set_table(self, field_list):
        self.empty_table()
        self.table.heading('#0', text='Name')
        self.table.configure(columns=[e[0] for e in field_list])
        for field, name in field_list:
            self.table.heading(field, text=name)

    def empty_table(self):
        self.table.delete(*self.table.get_children())

    def set_status(self, text, progress=0.00):
        log.debug("New status: %s" % text)
        self.status_text.set(text)
    
    def set_progressbar(self, current=0, max=None):
        if max:
            self.max_progress = max
        else:
            max = self.max_progress
        
        self.progressbar.configure(maximum=max, value=current)

root = tkinter.Tk()
app = App(root)
app.mainloop()