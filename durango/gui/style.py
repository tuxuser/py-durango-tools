from tkinter import ttk


class UwpColors(object):
    Background = '#171717'
    Sidebar = '#1f1f1f'
    Selected = '#2f2f2f'
    Headline = '#4f4f4f'
    ContentBackground = '#737373'
    Text = '#ffffff'
    Highlight = '#3d7e70'
    SecondaryText = '#848484'
    XboxGreen = '#3D750F'
    OnlineHighlight = '#67ab48'


'''
Button	TButton
Checkbutton	TCheckbutton
Combobox	TCombobox
Entry	TEntry
Frame	TFrame
Label	TLabel
LabelFrame	TLabelFrame
Menubutton	TMenubutton
Notebook	TNotebook
PanedWindow	TPanedwindow (not TPanedWindow!)
Progressbar	Horizontal.TProgressbar or Vertical.TProgressbar, depending on the orient option.
Radiobutton	TRadiobutton
Scale	Horizontal.TScale or Vertical.TScale, depending on the orient option.
Scrollbar	Horizontal.TScrollbar or Vertical.TScrollbar, depending on the orient option.
Separator	TSeparator
Sizegrip	TSizegrip
Treeview	Treeview (not TTreview!)
'''

class UwpStyle(ttk.Style):
    def __init__(self):
        ttk.Style.__init__(self)
        self.theme_create("uwpstyle", "classic", settings={
            ".": {
                "configure": {
                    "background": UwpColors.Background,
                    "foreground": UwpColors.Text,
                    "troughcolor": UwpColors.SecondaryText,
                    "selectbackground": UwpColors.Selected,
                    "selectforeground": UwpColors.OnlineHighlight,
                    "fieldbackground": UwpColors.Background,
                    "font": ("Segoe UI", 12),
                    "borderwidth": 1
                },
                "map": {"foreground": [("disabled", UwpColors.XboxGreen)]}
            },
        })

        self.theme_use("uwpstyle")