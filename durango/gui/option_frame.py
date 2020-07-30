import logging
import tkinter
from tkinter import ttk

log = logging.getLogger('gui.option_frame')


class OptionFrame(ttk.Frame):
    name = 'frame_option'
    empty_tree_msg = 'Please overwrite empty_tree_msg'
    max_progress = 0

    def __init__(self, master):
        ttk.Frame.__init__(self, master, name=self.name)

        self.details_text = tkinter.StringVar()
        self.status_text = tkinter.StringVar()

        # Holds user controllable items
        frame_action = ttk.Frame(self, name='frame_action')
        frame_action.grid(column=0, row=0)

        # Holds progressbar and status text
        frame_info = ttk.Frame(self, name='frame_info')
        frame_info.grid(column=0, row=1)

        ## Frame action
        # Column 0: Details
        details = ttk.Label(frame_action, name='details', textvariable=self.details_text,
                            anchor='w')
        details.grid(column=0, row=0)

        # Column 1: Treeview
        self.treeview = ttk.Treeview(frame_action, name='treeview', selectmode='browse', padding=3)
        self.treeview.grid(column=1, row=0, sticky=('n', 's'))

        # Column 2: Scrollbars
        scrollbar_v = tkinter.Scrollbar(frame_action, name='scrollbar_v', orient=tkinter.VERTICAL)
        scrollbar_v.grid(column=2, row=0, sticky=('n', 's'))
        scrollbar_h = tkinter.Scrollbar(frame_action, name='scrollbar_h', orient=tkinter.HORIZONTAL)
        scrollbar_h.grid(column=1, row=1, sticky=('e', 'w'))

        # Column 3: Buttonframe + Buttons
        button_fields = self._button_fields
        frame_buttons = ttk.Frame(frame_action)
        frame_buttons.grid(column=3, row=0)
        for index, value in enumerate(button_fields):
            name, text, command = value
            ttk.Button(frame_buttons, name=name, text=text, command=command).grid(row=index)

        ## Frame info
        # Column 0: Status text
        label_status = ttk.Label(frame_info, name='statuslabel')
        label_status.configure(textvariable=self.status_text, anchor='w', width=30)
        label_status.grid(column=0, row=0, sticky=('e', 'w'))

        self.progressbar = ttk.Progressbar(frame_info, name='progressbar')
        self.progressbar.configure(orient=tkinter.HORIZONTAL, mode='determinate', length=300)
        self.progressbar.grid(column=0, row=1, sticky=('e', 'w'))

        ## Configure stuff
        # Connect Treeview w/ scrollbar
        scrollbar_v.configure(command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=scrollbar_v.set)
        scrollbar_h.configure(command=self.treeview.xview)
        self.treeview.configure(xscrollcommand=scrollbar_h.set)

        # Set up treeview
        tree_fields = self._tree_fields
        # Dont set 'icon'-column twice => skip '#0'
        self.treeview.configure(columns=[e[0] for e in tree_fields if e[0] != '#0'])
        for field, name, onclick_command, params in tree_fields:
            self.treeview.heading(field, text=name, command=onclick_command)
            self.treeview.column(field, **params)

        # Bind command to treeview select
        self.treeview.bind('<<TreeviewSelect>>', self.on_treeview_item_select)

        # Set initial msg in treeview
        self.set_status_idle()
        self.treeview.insert('', 'end', text=self.empty_tree_msg)

    @property
    def _tree_fields(self):
        raise Exception('property self._tree_fields not overwritten')

    @property
    def _button_fields(self):
        raise Exception('property self._button_fields not overwritten')

    def activate(self):
        self.grid(column=0, row=0)

    def deactivate(self):
        self.grid_forget()

    def on_treeview_item_select(self, event):
        raise Exception('method on_treeview_item_select not overwritten')

    def set_status(self, text):
        log.debug("New status: %s" % text)
        self.status_text.set(text)

    def set_details(self, text):
        self.details_text.set(text)

    def set_progressbar(self, current=0, max_val=None):
        progressbar = self.progressbar
        if max_val:
            self.max_progress = max_val
        else:
            max_val = self.max_progress

        progressbar.configure(maximum=max_val, value=current)

    def set_status_idle(self):
        self.set_status('Idle')

    def reset_layout(self):
        self.treeview.delete(*self.treeview.get_children())
        self.set_status_idle()
