# Originally from https://github.com/airbus-seclab/ilo4_toolbox/blob/master/scripts/iLO4/ilo4_extract.py
# Updated locally to Python 3 as the original project is archived

import os
from ctypes import *
from struct import pack
import uuid

DEVICES = {
    uuid.UUID("9d7b312fe3c9764dbff6b9d0d085a952"): "ILO",
    uuid.UUID("2e8d14aa096e3e45bc6f63baa5f5ccc4"): "SYSTEM_ROM",
    uuid.UUID("916b239911c283429ca97423f25687f3"): "CUSTOM_ROM",
    uuid.UUID("9a43adb1d19dc141a4962da9313f1f07"): "CPLD",
    uuid.UUID("3bad180a84cb0c479050cafb33371a14"): "CARBONDALE",
    uuid.UUID("8aa2489e6c5819458405a04f84e27f0f"): "PIC",
    uuid.UUID("90aa533689703a45899c792827a50d67"): "NVME_BP_PIC",
    uuid.UUID("7760b86b75021446aae186618e8b1c27"): "POWER_SUPPLY",
    uuid.UUID("dffc32e2cbbc5347a99bf6b11c6eb074"): "EEPROM_I2C",
    uuid.UUID("18077fda4c441c49b9bfb5a9ccc5e6e8"): "FILES",
    uuid.UUID("0c4c1027c53a91498afbd1f3cd166fb4"): "LANGUAGE_PACK",
    uuid.UUID("a8d1685fab9795408c68bc3e1125268b"): "ILO_MOONSHOT",
    uuid.UUID("8384790bfcabcc4c914e26c4fb948cff"): "CPLD_MOONSHOT"
}

TARGETS = {
    uuid.UUID("2932ecaecc69d843bd0e61dc3406f71b"): "ILO_4",
    uuid.UUID("0000000000000000000000000000ffff"): "SERVER_ID",
    uuid.UUID("00000000000000000000000001FFFFFF"): "BIOS",
    uuid.UUID("00000000000000000000000001ffffff"): "BOOTBLOCK_0",
    uuid.UUID("00000000000000000000000001ffffff"): "BOOTBLOCK_1",
    uuid.UUID("0000000000000000000000000000cdff"): "CARBONDALE_1",
    uuid.UUID("00000000000000000000000000504dff"): "POWER_PIC",
    uuid.UUID("000000000000000000000000ffffffff"): "NMVE_BP_PIC",
    uuid.UUID("4cb0f50e84b9984295f04b3fffffffff"): "OEM_DATA",
    uuid.UUID("ffffffffffff000000000cf38db966ea"): "PS1",
    uuid.UUID("ffffffffffff000000000cf38db966ea"): "PS2"
}


def hexdump(src, length=16):
    FILTER = ''.join([chr(x) if 32 <= x <= 126 else '.' for x in range(256)])
    lines = []
    for c in range(0, len(src), length):
        chars = src[c:c+length]
        hexstr = ' '.join(f"{b:02x}" for b in chars)
        printable = ''.join(FILTER[b] for b in chars)
        lines.append(f"{c:04x}  {hexstr:<{length*3}}  {printable}\n")
    return ''.join(lines)


class SignatureParams(LittleEndianStructure):

    _fields_ = [
        ("sig_size", c_uint),
        ("modulus", c_byte * 0x200),
        ("exponent", c_byte * 0x200)
    ]

    def to_bytes(self, byte_array):
        return bytes(byte_array)

    def dump(self):
        print(f"  > signature size    : 0x{self.sig_size:x}")
        print("  > modulus")
        print(hexdump(self.to_bytes(self.modulus)))
        print("  > exponent")
        print(hexdump(self.to_bytes(self.exponent)))


class HpImageHeader(LittleEndianStructure):

    _fields_ = [
        ("img_magic", c_char * 0x8),
        ("major", c_byte),
        ("minor", c_byte),
        ("field_A", c_ushort),
        ("device_id", c_byte * 0x10),
        ("field_1C", c_uint),
        ("field_20", c_uint),
        ("field_24", c_uint),
        ("field_28", c_uint),
        ("field_2C", c_uint),
        ("field_30", c_uint),
        ("field_34", c_uint),
        ("field_38", c_uint),
        ("field_3C", c_uint),
        ("version", c_char * 0x20),
        ("name", c_char * 0x40),
        ("gap", c_byte * 0x400),
    ]

    def to_bytes(self, byte_array):
        return bytes(byte_array)

    def dump(self):
        print(f"  > img_magic          : {self.to_bytes(self.img_magic).decode(errors='ignore')}")
        print(f"  > version major      : 0x{self.major:x}")
        print(f"  > version minor      : 0x{self.minor:x}")
        print(f"  > field_A            : 0x{self.field_A:02x}")

        dev = ""
        dev_id = uuid.UUID(self.to_bytes(self.device_id).hex())
        if dev_id in DEVICES:
            dev = DEVICES[dev_id]

        print(f"  > device id          : {dev}")
        print(hexdump(self.to_bytes(self.device_id)))
        print(f"  > field_1C           : 0x{self.field_1C:x}")
        print(f"  > field_20           : 0x{self.field_20:x}")
        print(f"  > field_24           : 0x{self.field_24:x}")
        print(f"  > field_28           : 0x{self.field_28:x}")
        print(f"  > field_2C           : 0x{self.field_2C:x}")
        print(f"  > field_30           : 0x{self.field_30:x}")
        print(f"  > field_34           : 0x{self.field_34:x}")
        print(f"  > field_38           : 0x{self.field_38:x}")
        print(f"  > field_3C           : 0x{self.field_3C:x}")
        print(f"  > version            : {self.to_bytes(self.version).decode(errors='ignore')}")
        print(f"  > name               : {self.to_bytes(self.name).decode(errors='ignore')}")
        print("  > gap")


# -------------------------------
# Decompression functions
# -------------------------------

window = bytearray(0x1000)
wchar = 0

def decompress_all(data, fname, chunks=0x10000):
    global window, wchar
    fff = open(fname, "wb")

    while len(data) > 0:
        ret = decompress(data[:chunks], fff)
        if len(data) < chunks:
            if ret == 0:
                data = b""
            else:
                data = data[-ret:]
            ret = decompress(data[:chunks], fff, limit=0)
            if ret == 0:
                data = b""
            else:
                data = data[-ret:]
        else:
            data = data[chunks-ret:]

    fff.close()
    return os.path.getsize(fname)


def decompress(data, fff, limit=16):
    global window, wchar
    out = bytearray()

    while len(data) > limit:
        comp = data[0]
        data = data[1:]

        for i in range(8):
            if limit == 0 and len(data) == 0:
                break
            if ((comp >> (7-i)) & 1) == 1:
                out.append(data[0])
                window[wchar] = data[0]
                wchar = (wchar + 1) % 0x1000
                data = data[1:]
            else:
                x = (data[0] >> 4) + 3
                ptr = wchar - (data[1] + ((data[0] & 0xf) << 8)) - 1
                for k in range(x):
                    out.append(window[(ptr+k) & 0xfff])
                    window[wchar] = window[(ptr+k) & 0xfff]
                    wchar = (wchar + 1) % 0x1000
                data = data[2:]

    fff.write(out)
    return len(data)


def compress(data):
    data = b"\x00"*0x1000 + data
    current_off = 0x1000
    oc = 0
    outbuff = bytearray()
    tmp_buff = bytearray()
    mark = 0

    while current_off < len(data):
        k = 3
        off = -1

        while data[current_off:current_off+k] in data[current_off-0x1000:current_off+k-1] and k < 19 and (current_off+k) < len(data):
            k += 1

        k -= 1

        if k >= 3:
            off = (data[current_off-0x1000:current_off+k-1]).rfind(data[current_off:current_off+k])
            if off == 4095 and data[current_off:current_off+k] == data[current_off-0x1000+off-1:current_off-0x1000+off-1+k]:
                off -= 1

        if off == -1:
            mark |= (1 << (7-oc))
            tmp_buff.append(data[current_off])
            current_off += 1
        else:
            special = (((k-3) << 12) | ((-off-1)&0xfff)) & 0xffff
            tmp_buff += pack(">H", special)
            current_off += k
        oc += 1

        if oc == 8:
            outbuff.append(mark)
            outbuff += tmp_buff
            tmp_buff = bytearray()
            oc = 0
            mark = 0

    while oc < 8:
        mark |= (1 << (7-oc))
        oc += 1
    outbuff.append(mark)
    outbuff += tmp_buff

    return bytes(outbuff)
