#!/usr/bin/env python2
"""
Compare two iLO firmware versions to identify offset differences
Useful for porting patches between versions
"""

import sys
import os
import struct

def extract_elf_sections(data):
    """Extract ELF section info"""
    if not data.startswith('\x7fELF'):
        return None
    
    sections = []
    ei_class = ord(data[4])
    
    if ei_class == 1:  # 32-bit ELF
        e_shoff = struct.unpack('<I', data[32:36])[0]
        e_shentsize = struct.unpack('<H', data[46:48])[0]
        e_shnum = struct.unpack('<H', data[48:50])[0]
        e_shstrndx = struct.unpack('<H', data[50:52])[0]
        
        if e_shoff == 0:
            return None
            
        # String table
        str_off = e_shoff + e_shstrndx * e_shentsize
        str_tab = data[str_off:str_off+256]
        
        for i in range(e_shnum):
            off = e_shoff + i * e_shentsize
            sh_name = struct.unpack('<I', data[off:off+4])[0]
            sh_addr = struct.unpack('<I', data[off+12:off+16])[0]
            sh_offset = struct.unpack('<I', data[off+16:off+20])[0]
            sh_size = struct.unpack('<I', data[off+20:off+24])[0]
            
            name = "unknown"
            if sh_name < len(str_tab):
                name = str_tab[sh_name:].split('\x00')[0]
            
            sections.append({
                'name': name,
                'addr': sh_addr,
                'offset': sh_offset,
                'size': sh_size
            })
    
    return sections

def find_string_offsets(data, strings):
    """Find offset positions of strings"""
    results = {}
    for s in strings:
        pos = data.find(s)
        if pos != -1:
            results[s] = pos
    return results

def compare_binaries(file1, file2, name1="v277", name2="v278"):
    """Compare two firmware binaries"""
    
    print("=== Firmware Comparison: {} vs {} ===\n".format(name1, name2))
    
    with open(file1, 'rb') as f:
        data1 = f.read()
    with open(file2, 'rb') as f:
        data2 = f.read()
    
    print("Size {}: {} bytes".format(name1, len(data1)))
    print("Size {}: {} bytes".format(name2, len(data2)))
    print("Difference: {} bytes\n".format(len(data2) - len(data1)))
    
    # Find common strings
    common_strings = [
        'quit', 'FAN', 'OCSD', 'OCBB', 'DEBUG', 'VSPR', 'NULL_CMD',
        'health_ipc_call', 'signature', 'verify'
    ]
    
    print("=== String Offset Comparison ===\n")
    print("{:<20} {:>10} {:>10} {:>10}".format("String", name1, name2, "Delta"))
    print("-" * 55)
    
    for s in common_strings:
        pos1 = data1.find(s)
        pos2 = data2.find(s)
        
        if pos1 != -1 and pos2 != -1:
            delta = pos2 - pos1
            print("{:<20} 0x{:08X} 0x{:08X} {:+d}".format(s, pos1, pos2, delta))
    
    # Analyze ELF sections
    print("\n=== ELF Section Comparison ===\n")
    
    sections1 = extract_elf_sections(data1)
    sections2 = extract_elf_sections(data2)
    
    if sections1 and sections2:
        print("Section differences:")
        for s1 in sections1:
            s2 = next((s for s in sections2 if s['name'] == s1['name']), None)
            if s2:
                if s1['offset'] != s2['offset']:
                    print("  {}: offset 0x{:X} -> 0x{:X} (delta: {:+d})".format(
                        s1['name'], s1['offset'], s2['offset'], s2['offset'] - s1['offset']))
                if s1['size'] != s2['size']:
                    print("  {}: size {} -> {} (delta: {:+d})".format(
                        s1['name'], s1['size'], s2['size'], s2['size'] - s1['size']))
    
    # Byte-level comparison (sample)
    print("\n=== Sample Byte Comparison ===\n")
    
    # Check if data2 has same patterns as data1 at shifted offsets
    patterns = [
        ('Sig check (BEQ)', '\x1D\x00\x00\x0A'),
        ('Sig check (BNE)', '\x40\x00\x00\x1A'),
    ]
    
    for name, pat in patterns:
        pos1 = data1.find(pat)
        pos2 = data2.find(pat)
        if pos1 != -1 and pos2 != -1:
            delta = pos2 - pos1
            print("{}: {} @ 0x{:X}, {} @ 0x{:X}, delta: {:+X}".format(
                name, name1, pos1, name2, pos2, delta))
        elif pos1 != -1:
            print("{}: Found in {} @ 0x{:X}, not in {}".format(name, name1, pos1, name2))
        elif pos2 != -1:
            print("{}: Not in {}, found in {} @ 0x{:X}".format(name, name1, name2, pos2))

def main():
    if len(sys.argv) < 3:
        print("Usage: {} <firmware_v1> <firmware_v2> [name1] [name2]".format(sys.argv[0]))
        print("")
        print("Compare two iLO firmware versions to identify offset shifts")
        print("for porting patches between versions.")
        sys.exit(1)
    
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    name1 = sys.argv[3] if len(sys.argv) > 3 else "v1"
    name2 = sys.argv[4] if len(sys.argv) > 4 else "v2"
    
    if not os.path.exists(file1):
        print("Error: File not found: {}".format(file1))
        sys.exit(1)
    if not os.path.exists(file2):
        print("Error: File not found: {}".format(file2))
        sys.exit(1)
    
    compare_binaries(file1, file2, name1, name2)

if __name__ == '__main__':
    main()
