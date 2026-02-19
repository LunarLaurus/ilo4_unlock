#!/usr/bin/env python2
"""
Firmware Analysis Toolkit - Signature Check Finder
Helps locate signature verification bypass points in iLO firmware
"""

import sys
import os
import struct
import subprocess

def hex_dump(data, offset=0, length=16):
    """Generate hexdump-style output"""
    for i in range(0, len(data), length):
        chunk = data[i:i+length]
        hex_str = ' '.join('{:02x}'.format(ord(b)) for b in chunk)
        ascii_str = ''.join(b if 32 <= ord(b) < 127 else '.' for b in chunk)
        print('{:08x}  {:48s}  |{}|'.format(offset + i, hex_str, ascii_str))

def find_pattern(data, pattern):
    """Find all occurrences of a byte pattern"""
    results = []
    start = 0
    while True:
        idx = data.find(pattern, start)
        if idx == -1:
            break
        results.append(idx)
        start = idx + 1
    return results

def find_strings(data, min_len=4):
    """Extract printable strings from binary"""
    strings = []
    current = []
    for i, b in enumerate(data):
        if 32 <= ord(b) <= 126:
            current.append(b)
        else:
            if len(current) >= min_len:
                strings.append((i - len(current), ''.join(current)))
            current = []
    return strings

def find_arm_branches(data):
    """Find ARM branch instructions"""
    branches = []
    for i in range(0, len(data) - 3, 4):
        word = struct.unpack('<I', data[i:i+4])[0]
        # B or BL instruction (bits 24-27 = 0b1010 or 0b1011)
        cond = (word >> 28) & 0xF
        opcode = (word >> 24) & 0xF
        if opcode in [0xA, 0xB]:
            # Check if it's BEQ, BNE, etc.
            if cond != 0xE:  # Not unconditional
                branches.append((i, 'B{cond} #{off}'.format(
                    cond=['EQ','NE','CS','CC','MI','PL','VS','VC',
                          'HI','LS','GE','LT','GT','LE','NV','??'][cond],
                    off=(word & 0xFFFFFF) * 4
                )))
    return branches

def find_sig_check_patterns(data):
    """Search for common signature check patterns"""
    
    print("\n=== Searching for Signature Check Patterns ===\n")
    
    # Pattern 1: The original BEQ signature check patch point
    # Original: 1D 00 00 0A (BEQ to next instruction + 0x28)
    # Patched:  1D 00 00 EA (unconditional branch)
    patterns = [
        ('Original sig check (BEQ)', b'\x1D\x00\x00\x0A'),
        ('Patched sig check (B)', b'\x1D\x00\x00\xEA'),
        ('BEQ pattern variant', b'\x00\x00\x0A\x1D'),
        ('BNE sig check', b'\x40\x00\x00\x1A'),  # Common in bootloader
    ]
    
    for name, pattern in patterns:
        results = find_pattern(data, pattern)
        if results:
            print("[{}] Found {} occurrences at:".format(name, len(results)))
            for idx in results[:10]:  # Show first 10
                print("  0x{:08X}".format(idx))
                # Show surrounding bytes
                context = data[max(0, idx-16):idx+32]
                hex_dump(context, max(0, idx-16))
                print()
        else:
            print("[{}] Not found".format(name))
    
    return

def find_command_strings(data):
    """Find command strings like FAN, OCSD, etc."""
    
    print("\n=== Searching for Command Strings ===\n")
    
    commands = [
        ('FAN', b'FAN\x00'),
        ('OCSD', b'OCSD\x00'),
        ('OCBB', b'OCBB\x00'),
        ('health/h', b'\x68\x00\x00\x00'),  # 'h' with nulls
        ('quit', b'quit'),
        ('DEBUG', b'DEBUG'),
        ('VSPR', b'VSPR'),
        ('NULL_CMD', b'NULL_CMD'),
    ]
    
    for name, pattern in commands:
        results = find_pattern(data, pattern)
        if results:
            print("[{}] Found at: {}".format(name, ', '.join('0x{:X}'.format(r) for r in results)))
    
    return

def analyze_elf(data):
    """Basic ELF analysis"""
    
    print("\n=== ELF Header Analysis ===\n")
    
    if not data.startswith('\x7fELF'):
        print("Not a valid ELF file")
        return
    
    # Parse ELF header
    ei_class = ord(data[4])  # 1=32bit, 2=64bit
    ei_endian = ord(data[5])  # 1=little, 2=big
    
    if ei_class == 1:  # 32-bit
        e_type = struct.unpack('<H', data[16:18])[0]
        e_machine = struct.unpack('<H', data[18:20])[0]
        e_entry = struct.unpack('<I', data[24:28])[0]
        e_phoff = struct.unpack('<I', data[28:32])[0]
        e_shoff = struct.unpack('<I', data[32:36])[0]
        
        print("Type: {:04x}".format(e_type))
        print("Machine: ARM" if e_machine == 40 else "Machine: {}".format(e_machine))
        print("Entry: 0x{:08X}".format(e_entry))
        print("Program header: 0x{:08X}".format(e_phoff))
        print("Section header: 0x{:08X}".format(e_shoff))
    
    return

def main():
    if len(sys.argv) < 2:
        print("Usage: {} <firmware_binary>".format(sys.argv[0]))
        print("")
        print("This tool helps analyze iLO firmware to find signature check")
        print("bypass locations for porting patches to new versions.")
        sys.exit(1)
    
    binary_path = sys.argv[1]
    
    if not os.path.exists(binary_path):
        print("Error: File not found: {}".format(binary_path))
        sys.exit(1)
    
    print("Loading binary: {}".format(binary_path))
    
    with open(binary_path, 'rb') as f:
        data = f.read()
    
    print("Size: {} bytes ({:.2f} MB)".format(len(data), len(data)/1024/1024))
    
    # Run analyses
    find_sig_check_patterns(data)
    analyze_elf(data)
    
    print("\n=== Next Steps ===")
    print("1. Compare offsets with known-working patch versions")
    print("2. Look for signature verification functions")
    print("3. Check for disabled/enabled code differences")
    print("4. Use bindiff for detailed comparison")

if __name__ == '__main__':
    main()
