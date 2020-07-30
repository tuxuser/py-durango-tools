import logging
import tkinter
from tkinter import ttk

from durango.gui.style import UwpStyle
from durango.gui.flash import FlashExplorer
from durango.gui.xvd import XvdExplorer
from durango.gui.savegames import SavegameExplorer
from durango.gui import assets

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


class App(ttk.Frame):
    max_progress = 0

    def __init__(self, master):
        ttk.Frame.__init__(self, master)

        style = UwpStyle()

        #self.grid(column=0, row=0, sticky=('n','e','s','w'))
        self.grid(column=0, row=0)
        self.status_text = tkinter.StringVar()

        self.master.title('Durango Toolbox')
        #self.master.resizable(False, False)

        # (G/JIF) images, b64 encoded
        self.hdd_symbol = tkinter.PhotoImage(data=assets.HDD_SYMBOL)
        self.floppy_symbol = tkinter.PhotoImage(data=assets.FLOPPY_SYMBOL)
        self.microchip_symbol = tkinter.PhotoImage(data=assets.MICROCHIP_SYMBOL)

        # Sidebar
        frame_sidebar = ttk.Frame(self, name='frame_sidebar')
        frame_sidebar.grid(column=0, row=0)
        # Main frame
        frame_main = ttk.Frame(self, name='frame_main')
        frame_main.grid(column=1, row=0)

        self.xvd_layout = XvdExplorer(frame_main)
        self.flash_layout = FlashExplorer(frame_main)
        self.savegame_layout = SavegameExplorer(frame_main)

        sidebar_xvd = ttk.Button(frame_sidebar, name='sidebar_xvd')
        sidebar_xvd.configure(image=self.hdd_symbol, command=self.on_click_xvd)
        sidebar_flash = ttk.Button(frame_sidebar, name='sidebar_flash')
        sidebar_flash.configure(image=self.microchip_symbol, command=self.on_click_flash)
        sidebar_savegame = ttk.Button(frame_sidebar, name='sidebar_savegame')
        sidebar_savegame.configure(image=self.floppy_symbol, command=self.on_click_savegame)
        sidebar_xvd.grid(row=0)
        sidebar_flash.grid(row=1)
        sidebar_savegame.grid(row=2)

        # Initially open XVD view
        self.on_click_xvd()

    def on_click_xvd(self):
        self.flash_layout.deactivate()
        self.savegame_layout.deactivate()
        self.xvd_layout.activate()

    def on_click_flash(self):
        self.xvd_layout.deactivate()
        self.savegame_layout.deactivate()
        self.flash_layout.activate()

    def on_click_savegame(self):
        self.xvd_layout.deactivate()
        self.flash_layout.deactivate()
        self.savegame_layout.activate()


def main():
    root = tkinter.Tk()
    app = App(root)
    app.mainloop()


if __name__ == '__main__':
    main()
