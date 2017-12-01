## Various python helper tools to deal with xbox one ##

# Notes #
Please use python3 for best compatibility. I didn't test with python2 at all.
For easy usage -> Add python bin-directory to your PATH variable
* Windows: https://docs.python.org/3/using/windows.html#excursus-setting-environment-variables
* Alternative for windows: Tick the option "Add to PATH" while installing python package
* Linux: It's usually done automatically on install

Use the following command to start the individual tools:

    python3 -m module
If you try to start the *.py file directly, most likely the imports wont be resolved.

### Example ###
   python3 -m gui.toolbox

# Content #

### gui ###

    gui.toolbox

### hdd - Hard drive tools ###

    hdd.external_storage_enum
    hdd.savegame_enum
    hdd.prepare_internal_hdd.xboxonehdd

### nand - Nand / eMMC flash tools ###

    nand.NANDOne
