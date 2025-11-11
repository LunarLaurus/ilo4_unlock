#!/usr/bin/env python3
#
# This file is part of ilo4_unlock (https://github.com/kendallgoto/ilo4_unlock/).
# Copyright (c) 2022 Kendall Goto
# with some code derived from https://github.com/airbus-seclab/ilo4_toolbox
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import sys
from keystone import *

def read_patch(file):
    with open(file, "rb") as f:
        handler = f.read()
        # remove comments
        handler_split = handler.split(b'\n')
        for i in range(len(handler_split)):
            this_line = handler_split[i].split(b";")[0]
            handler_split[i] = this_line
        handler = b"\n".join(handler_split)
        # Keystone expects str in Python 3, so decode
        ks = Ks(KS_ARCH_ARM, KS_MODE_ARM)
        try:
            output = ks.asm(handler.decode('utf-8'))
        except KsError as e:
            print("Error with Keystone", e)
            if hasattr(e, 'get_asm_count') and e.get_asm_count() is not None:
                print("asmcount = %u" % e.get_asm_count())
            sys.exit(1)
        # convert list of ints to bytes
        return bytes(output[0])

def hexdump(src, length=16):
    FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.' for x in range(256)])
    lines = []
    for c in range(0, len(src), length):
        chars = src[c:c+length]
        hex_str = ' '.join(["%02x" % x for x in chars])
        printable = ''.join([chr(x) if x <= 127 and FILTER[x] != '\x00' else '.' for x in chars])
        lines.append("%04x  %-*s  %s\n" % (c, length*3, hex_str, printable))
    return ''.join(lines)
