## Various python helper tools to deal with xbox one ##

# Notes #
Please use python3 for best compatibility. I didn't test with python2 at all.

Use the following command to start the individual tools:

    python3 -m module
If you try to start the *.py file directly, most likely the imports wont be resolved.

# Content #

### hdd - Hard drive tools ###

    hdd.external_storage_enum
    hdd.savegame_enum
    hdd.prepare_internal_hdd.xboxonehdd

### nand - Nand / eMMC flash tools ###

    nand.NANDOne
