"""
Toggles external usb drive, formatted for use with Xbox One (Durango) to use with the PC
2 bytes @ 0x1FE of first sector on hdd decide wether the drive is seen valid or not.
"""

import sys
import os
import argparse

MODE_ID_XBOXONE = b'\x99\xCC'
MODE_ID_REGULAR = b'\x55\xAA'

SECTOR_SIZE = 0x200
ID_POSITION = SECTOR_SIZE - 2

def toggle_drive(device, do_toggle=False):
    try:
        disk = os.open(device, os.O_RDWR)
    except PermissionError as e:
        print("You might run the script as root/admin!")
        print(e)
        sys.exit(-1)

    os.lseek(disk, ID_POSITION, os.SEEK_SET)
    id = os.read(disk, 2)
    
    new_id = None
    if id == MODE_ID_REGULAR:
        print("Current mode: Regular")
        new_id = MODE_ID_XBOXONE
    elif id == MODE_ID_XBOXONE:
        print("Current mode: Xbox")
        new_id = MODE_ID_REGULAR
    
    if do_toggle and new_id:
        print("Toggling mode...")
        os.lseek(disk, ID_POSITION, os.SEEK_SET)
        os.write(disk, new_id)
    elif do_toggle:
        print("Invalid Id found: %02X - not writing anything!")

    os.close(disk)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Toggle external storage between xbox/regular mode')
    parser.add_argument('blockdevice', type=str, help='block device to toggle')
    parser.add_argument('--toggle', action='store_true', help='Toggle hdd mode')

    args = parser.parse_args()

    print("Xbox One USB Hdd mode toggler")
    toggle_drive(args.blockdevice, args.toggle)
