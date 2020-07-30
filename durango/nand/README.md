NANDOne v0.03
===========

Xbox One NAND Filesystem tool

Parses Xbox One Nanddumps for filesystem header and extracts the binary
files. It's probably not very compatible and contains bugs for sure :P

Enjoy!


Requirements
===========
 * Python 3.*
 * Xbox One eMMC NAND Dump
 * Python libs: construct

Usage
===========
nandone.py [-h] [--extract] filename

Flags:

-h 			Help

--extract 	Extract found files

Example:
nandone.py --extract nanddump.bin


Changelog
===========
v0.03
- Major rewrite
- Scan for filesystem header at ?all? 3 offsets
- Extract files by name

v0.02
- ExtractSFBXdata: Extracting the bootblock @ addr 0x0
- mmap: Fixing memory issues on 32bit systems by reading in chunks
- DumpSFBX: SFBX size is now read dynamically, not fixed anymore
- 'sfbxscan' is obsolete, that's done automatically now, if needed
- XVD header gets detected and printed in info output
- Filetype-magic is appended to extracted filenames
- Some cleanup
- Support for parsing and extracting SFBX entries
- Possibility to scan for SFBX block
- Additional error checking

v0.01
- Initial release
