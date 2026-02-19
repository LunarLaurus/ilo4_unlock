# Research Methodology: Extracting and Reinserting Fan Control Code from iLO4 v2.77 to v2.78/2.79

**Date:** 2026-02-19  
**Purpose:** Document step-by-step methodology for extracting fan control functionality from iLO4 v2.77 and reinserting it into v2.78/2.79  
**Status:** Research Complete - Ready for Execution

---

## Executive Summary

This document outlines a comprehensive methodology for extracting fan control code from iLO4 v2.77 and reinserting it into v2.78/2.79. The core challenge is that HPE completely removed the fan control logic between these versions while leaving the command infrastructure partially intact.

### Why This Works

| Version | Signature Bypass | CLI Commands | Fan Functions |
|---------|-----------------|--------------|---------------|
| 2.77    | Working         | Working      | Working       |
| 2.78    | Working         | Working      | REMOVED       |
| 2.79    | Working         | Working      | REMOVED       |

The solution involves either:
1. **Function Pointer Restoration**: Copy working handler pointers from v2.77 to v2.78/2.79
2. **Code Extraction and Reinsertion**: Extract actual fan control assembly from v2.77 and inject into v2.78/2.79

---

## Part 1: Architecture Overview

### 1.1 Command Flow Architecture

```
User SSH Command
       |
       v
fn_handler.S (patched entry point)
       |
       v (switch value 5-8)
health_ipc_call() at offset 0x3E420 (v2.77)
       |
       v
.health module jump table
       |
       v
Fan Control Functions (REMOVED in v2.78+)
```

### 1.2 Key Components

| Component | v2.77 Offset | v2.78 Offset | Purpose |
|-----------|-------------|--------------|---------|
| Signature Bypass | 0x96EDE8 | 0x964ADC | Enable custom firmware |
| fn_handler | 0xAFD768 | 0xAF1390 | Parse CLI input |
| Command Table | 0xB80348 | 0xB73F70 | Command name mappings |
| health_ipc_call | 0x3E420 | Different | IPC dispatcher |
| Jump Table | Various | NULL/stub | Handler pointers |

### 1.3 Switch Values

| Value | Command | Function | Status in v2.78+ |
|-------|---------|----------|-------------------|
| 5 | h | Health info | Working |
| 6 | fan | Fan control | REMOVED |
| 7 | ocsd | On-chip sensors | Working |
| 8 | ocbb | On-chip battery | Working |

---

## Part 2: Extraction Phase (v2.77 Analysis)

### 2.1 Firmware Extraction

```bash
# Extract v2.77 (reference) using ilo4_toolbox
python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py binaries/ilo4_277.bin build/277_extract

# This produces:
# - build/277_extract/elf.bin      (userland)
# - build/277_extract/kernel_main.bin (kernel)
# - build/277_extract/bl.bin       (bootloader)
```

### 2.2 Identifying Code to Extract

#### 2.2.1 The fn_handler.S Analysis

From `patches/277/asm/fn_handler.S`:

```assembly
h:
    MOV     r0, #5      ; entrypoint for health (call switch #5)
    B       start

fan:
    MOV     r0, #6      ; entrypoint for fan (call switch #6)
    B       start

ocsd:
    MOV     r0, #7      ; entrypoint for ocsd (call switch #7)
    B       start

ocbb:
    MOV     r0, #8      ; entrypoint for ocbb (call switch #8)

start:
    MOV     R12, SP
    PUSH    {R11, R12, LR, PC}
    SUB     R11, R12, #4
    SUB     SP, SP, #0xA00     ; Allocate space on stack for IPC struct
    STR     R0, [SP]           ; Store R0 as first value in struct (switch value)
    MOV     R3, #0
    ADD     R2, SP, #4
    ADD     R0, R7, #0x1000    ; Move R0 to start of input arg
loop:
    LDRB    R1, [R0], #1
    CMP     R1, #0x20
    STRBEQ  R3, [R2], #1
    STRBNE  R1, [R2], #1
    CMP     R1, #0
    BNE     loop
    STRB    R3, [R2]
    MOV     R0, SP
    ADD     R1, SP, #0x500
    BL      0x3E420             ; health_ipc_call(SP, SP+500)
    LDR     R0, [SP, #0x500]
    LDMDB   R11, {R11, SP, PC}
```

Key observations:
- Input string parsed from R7+0x1000 (command line args in connection record)
- Switch value (5-8) stored at SP+0x00
- Arguments stored at SP+0x04 onwards (null-terminated strings)
- Response returned at SP+0x500
- Calls health_ipc_call at BL 0x3E420

#### 2.2.2 IPC Struct Layout

| Offset | Size | Description |
|--------|------|-------------|
| 0x00 | 4 bytes | Switch value (5-8) |
| 0x04 | ~0x4FC bytes | Parsed arguments (null-terminated strings) |
| 0x500 | 4 bytes | Return value from handler |

### 2.3 Locating the Jump Table in v2.77

The jump table is a 4-entry table (for switches 5, 6, 7, 8) of ARM function pointers:

```
table + 0x00 -> Handler for switch 5 (health)
table + 0x04 -> Handler for switch 6 (fan)
table + 0x08 -> Handler for switch 7 (ocsd)
table + 0x0C -> Handler for switch 8 (ocbb)
```

#### Method A: Find from health_ipc_call Reference
```bash
# The patched fn_handler calls BL 0x3E420
# Search for this pattern in the binary
xxd build/277_extract/elf.bin | grep -i "20 e4"
```

#### Method B: Search in Ghidra/IDA Pro
1. Load elf.bin as ARM little-endian
2. Navigate to 0x3E420 (virtual address)
3. Find switch-case pattern:
   - CMP R0, #max_value
   - LDR PC, [PC, R0, LSL #2]
4. Jump table follows these instructions

#### Method C: Binary Pattern Search
```python
import struct

def find_jump_table(elf_data, health_ipc_call_va):
    """Search for jump table near health_ipc_call"""
    # Typical pattern: 4 consecutive function pointers
    # Look for non-NULL pointers in a row
    pass
```

### 2.4 Extracting Handler Addresses

```python
import struct

def read_arm_pointer(data, offset):
    """Read 4-byte little-endian ARM pointer"""
    return struct.unpack("<I", data[offset:offset+4])[0]

# Example: Extract from known offset (TBD after analysis)
v277_table_offset = 0xXXXXXX

handler_health = read_arm_pointer(v277_data, v277_table_offset + 0x00)  # Switch 5
handler_fan     = read_arm_pointer(v277_data, v277_table_offset + 0x04)  # Switch 6
handler_ocsd    = read_arm_pointer(v277_data, v277_table_offset + 0x08)  # Switch 7
handler_ocbb    = read_arm_pointer(v277_data, v277_table_offset + 0x0C)  # Switch 8

print("v2.77 Working Handler Addresses:")
print("  Switch 5 (health): 0x{:08X}".format(handler_health))
print("  Switch 6 (fan):    0x{:08X}".format(handler_fan))
print("  Switch 7 (ocsd):   0x{:08X}".format(handler_ocsd))
print("  Switch 8 (ocbb):   0x{:08X}".format(handler_ocbb))
```

---

## Part 3: Dependency Analysis

### 3.1 Identifying External Dependencies

The extracted code depends on several external components:

#### 3.1.1 Kernel Calls

Fan control ultimately communicates with hardware. Key dependencies:

| Function | Purpose | Location |
|----------|---------|----------|
| health_ipc_call | IPC to .health module | .text offset 0x3E420 |
| VSPCHANNEL | Output logging | Referenced in stdout.S |
| libc_* | String operations | libC functions |

#### 3.1.2 Library Calls

The v2.77 stdout patch (`patches/277/asm/stdout.S`) shows:

```assembly
BL      0x1718b34      ; libc call (string processing)
BL      0x17e6cb4      ; VSPCHANNEL IPC call
```

These addresses differ between versions due to library relocation.

#### 3.1.3 Tracking Relocations

**Key Finding from patches/277/patches.md:**

> "This is the only patch I had to change. It makes some calls to relative libraries in memory (libc & VCom Shared), whose positions moved (I guess if the local memory got shifted due to changes of library sizes, etc)."

This means:
- Library call addresses change between versions
- Must update BL targets when porting code
- Use AOB (Array of Bytes) patterns to find new locations

### 3.2 Finding New Library Addresses in Target Versions

```bash
# Method: Find library function by behavior, not address
# Example: Find VSPCHANNEL string reference
strings build/278_extract/elf.bin | grep -i VSPCHANNEL

# Then find callers of this string
xxd build/278_extract/elf.bin | grep -A2 -B2 "<offset>"
```

### 3.3 Data Structure Dependencies

The connection record structure (from research/2022-02-17-docs.md):

```
ConnectionRecord {
    0x00: various fields
    0x264: first argument string
    0x364: second argument string
    0x1000: command line input (R7+0x1000)
    0x1570: some pointer
}
```

Ensure 
Ensure extracted code accesses these offsets correctly in target version.

---

## Part 4: Address Relocation Strategy

### 4.1 Virtual Address to File Offset Conversion

ARM binaries use virtual addresses (VAs). To convert to file offsets:

```python
def va_to_file_offset(elf_data, va):
    """Convert ARM virtual address to file offset using ELF headers"""
    import struct
    
    # Parse ELF header
    e_shoff = struct.unpack('<I', elf_data[32:36])[0]
    e_shentsize = struct.unpack('<H', elf_data[46:48])[0]
    e_shnum = struct.unpack('<H', elf_data[48:50])[0]
    
    # Find .text section
    for i in range(e_shnum):
        section_offset = e_shoff + (i * e_shentsize)
        sh_addr = struct.unpack('<I', elf_data[section_offset+12:section_offset+16])[0]
        sh_offset = struct.unpack('<I', elf_data[section_offset+16:section_offset+20])[0]
        sh_size = struct.unpack('<I', elf_data[section_offset+20:section_offset+24])[0]
        
        if sh_addr <= va < (sh_addr + sh_size):
            return va - sh_addr + sh_offset
    
    return None
```

### 4.2 Calculating Relocation Deltas

From existing patch analysis:

| Element | v2.77 Offset | v2.78 Offset | Delta |
|---------|--------------|--------------|-------|
| Sig Bypass | 0x96EDE8 | 0x964ADC | -0x9A2C |
| quit->OCBB | 0xB80348 | 0xB73F70 | -0xC3D8 |
| VSPR->h | 0xB8045C | 0xB74084 | -0xC3D8 |
| DEBUG->OCSD | 0xB80474 | 0xB7409C | -0xC3D8 |
| NULL_CMD->FAN | 0xB804D0 | 0xB740F8 | -0xC3D8 |
| fn_handler | 0xAFD768 | 0xAF1390 | -0xC3D8 |

**Note:** Delta -0xC3D8 is consistent for most userland patches, but library calls may differ.

### 4.3 Relocation Workflow

1. Calculate approximate offset using delta (-0xC3D8)
2. Verify with binary pattern search (AOB)
3. Confirm by disassembly
4. Apply patch

---

## Part 5: Code Injection (Reinsertion) Methods

### 5.1 Method A: Function Pointer Patching (Simplest)

If the jump table still exists but entries are NULL/stubs:

```json
[
    {
        "remark": "Patch fan handler (switch 6) to v2.77 function",
        "offset": "0xXXXXXXXX",
        "size": 4,
        "prev_data": "00 00 00 00",
        "patch": "<v2.77_handler_va_le>"
    }
]
```

**Steps:**
1. Find NULL entries in v2.78 jump table
2. Copy working handler VA from v2.77
3. Convert VA to file offset in v2.78
4. Patch the entry

### 5.2 Method B: Code Holing (For New Code Injection)

If complete code extraction is needed:

#### 5.2.1 Finding Code Cave

"Code holing" = finding unused space in binary for injection.

```bash
# Find regions of zeros/unused space
# Look for large blocks of 0x00 or 0xCC (uninitialized)
```

#### 5.2.2 Common Code Cave Locations

- Between functions (check for NOP padding)
- Unused data sections
- After existing patches (fn_handler is at 0xAFD768, could extend)

#### 5.2.3 Injection Process

1. Find suitable code cave (minimum ~200 bytes for fan handler)
2. Write ARM assembly for fan control
3. Update external calls (BL addresses)
4. Create jump from original handler location
5. Update jump table to point to new code

### 5.3 Method C: Modified fn_handler (Recommended)

Looking at `patches/278/patch_userland.json`, the v2.78 already has a modified fn_handler:

```assembly
05 00 A0 E3    ; MOV R0, #5
04 00 00 EA    ; B to next
06 00 A0 E3    ; MOV R0, #6
02 00 00 EA    ; B to next
07 00 A0 E3    ; MOV R0, #7
00 00 00 EA    ; B to next
08 00 A0 E3    ; MOV R0, #8
0D C0 A0 E1    ; MOV R12, SP (start of original)
...
```

This can be extended to include fan control logic directly, bypassing health_ipc_call entirely.

---

## Part 6: Jump Table Patching

### 6.1 Identifying Jump Tables

Jump tables in ARM typically appear as:

```assembly
CMP    R0, #8           ; Compare switch value with max
LDRLS  PC, [PC, R0, LSL #2]  ; Load handler from table
B      default_case     ; Branch to default
nop                   ; Padding (if needed)
; Jump table starts here
DCD    handler_5
DCD    handler_6
DCD    handler_7
DCD    handler_8
```

### 6.2 Searching for Jump Tables

```python
def find_jump_tables(elf_data):
    """Find all switch-case jump tables"""
    tables = []
    
    # Search for CMP followed by LDR PC pattern
    # Pattern: CMP Rx, #N + LDRLS PC, [PC, Rx, LSL #2]
    
    for i in range(len(elf_data) - 8):
        # Look for CMP instruction
        if elf_data[i:i+4] == b'\x00\x00\x50\xE3':  # CMP R0, #N
            # Check for LDR PC pattern nearby
            # Extract potential table entries
            pass
    
    return tables
```

### 6.3 Patching Jump Table Entries

```python
def patch_jump_table_entry(elf_path, table_offset, entry_index, new_handler_va):
    """Patch a single jump table entry"""
    import struct
    
    entry_offset = table_offset + (entry_index * 4)
    
    with open(elf_path, 'r+b') as f:
        f.seek(entry_offset)
        
        # Read current value for verification
        old_value = struct.unpack('<I', f.read(4))[0]
        print("Old entry: 0x{:08X}".format(old_value))
        
        # Write new handler VA (little-endian)
        f.seek(entry_offset)
        f.write(struct.pack('<I', new_handler_va))
        
        print("Patched entry {} to 0x{:08X}".format(entry_index, new_handler_va))
```

---

## Part 7: Step-by-Step Execution Methodology

### Phase 1: Preparation

```
1.1 Obtain firmware binaries
    - ilo4_277.bin (reference, working)
    - ilo4_278.bin (target)
    - ilo4_279.bin (target)

1.2 Extract firmware
    python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py ilo4_277.bin build/277
    python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py ilo4_278.bin build/278

1.3 Verify existing patches apply
    - Apply 277 patches to 277 -> should work
    - Apply 278 patches to 278 -> current state
```

### Phase 2: Analysis

```
2.1 Load v2.77 in Ghidra
    - Create new project
    - Import elf.bin as ARM Little-Endian
    - Set base address: 0x10000

2.2 Locate health_ipc_call
    - Search for string "health_ipc_call"
    - Navigate to function

2.3 Find jump table
    - In health_ipc_call, find switch-case code
    - Identify table base address

2.4 Extract handler addresses
    - Read 4 pointers at table+0x00, +0x04, +0x08, +0x0C
    - Convert VAs to file offsets
    - Verify they point to valid code (non-NULL, valid prolog)
```

### Phase 3: Target Analysis

```
3.1 Load v2.78 in Ghidra
    - Same settings as v2.77

3.2 Find corresponding locations
    - Apply delta (-0xC3D8) as starting point
    - Search for AOB patterns to confirm

3.3 Identify missing handlers
    - Check if jump table entries are NULL
    - Check if handlers are stubs (return immediately)
    - Document what needs to be added
```

### Phase 4: Implementation

```
4.1 Option A: Pointer Copy (if handlers exist but are NULL)
    - Copy v2.77 handler VAs
    - Calculate v2.78 file offsets
    - Create patch JSON

4.2 Option B: Code Extraction (if handlers removed)
    - Extract handler code from v2.77
    - Find code cave in v2.78
    - Update BL targets for library calls
    - Create injection patch
    - Update jump table
```

### Phase 5: Testing

```
5.1 Pre-flight checks
    - Verify all patch offsets
    - Check for conflicts
    - Validate assembly syntax

5.2 Build firmware
    cd patches/278
    ./build.sh

5.3 Flash and test (on non-production hardware)
    - Test: fan
    - Test: fan info
    - Test: fan temp
    - Test: fan speed 25
    - Test: fan start
```

---

## Part 8: Key Reference Data

### Existing Patch Offsets

From `patches/277/patch_userland.json`:

| Patch | Offset | Size | Description |
|-------|--------|------|-------------|
| Sig Bypass | 0x96EDE8 | 4 | BEQ->B |
| quit->OCBB | 0xB80348 | 4 | String rename |
| VSPR->h | 0xB8045C | 5 | String rename |
| DEBUG->OCSD | 0xB80474 | 5 | String rename |
| NULL_CMD->FAN | 0xB804D0 | 8 | String rename |
| fn_handler | 0xAFD768 | 116 | Function injection |
| Health Break | 0x404394 | 4 | Jump to logging |
| Logging Patch | 0x404784 | 172 | stdout replacement |
| OCBB Entry | 0xB97634 | 4 | Command table |
| Health Entry | 0xB97848 | 4 |
| Health Entry | 0xB97848 | 4 | Command table |
| OCSD Entry | 0xB9789C | 4 | Command table |
| Fan Entry | 0xB9797C | 4 | Command table |

### Key AOB Patterns

From `patches/277/patches.md`:

```
# Signature bypass
1D 00 00 0A -> BEQ (original)
1D 00 00 EA -> B (patched)

# Function entrypoint
0D C0 A0 E1 20 D8 2D E9 04 B0 4C E2 8B 13 00 EB 9A

# Command function calls
74 9E 01 00 -> OCBB (second match)
7C C8 01 00 -> health (first match)
C8 CE 01 00 -> OCSD (second match)
5C D1 01 00 -> Fan (last match)

# Kernel patch
30 10 95 E5 00 00 50 E3 04 00 00 0A 00 00 51 E3
```

### Function Prolog Patterns

```
MOV R12, SP             -> 0D C0 A0 E1
PUSH {..}               -> 2D E9
SUB SP, SP, #N          -> 04 00 ( Thumb: 00 B0 )
```

---

## Part 9: Risk Analysis and Mitigations

### 9.1 Address Relocation

**Risk:** Function addresses differ between versions.

**Mitigation:**
- Use delta table (-0xC3D8) as starting point
- Verify with AOB patterns
- May need to find functions by behavior

### 9.2 Library Call Updates

**Risk:** Library addresses change between versions.

**Mitigation:**
- Find library functions by string references
- Update BL targets in injected code
- Test thoroughly

### 9.3 Hardware Safety

**Risk:** Improper fan control causes overheating.

**Mitigation:**
- Always test with monitoring
- Keep "fan start" command available
- Never set fans to 0% for extended periods

### 9.4 Brick Recovery

**Risk:** Bad firmware flash leaves iLO unusable.

**Mitigation:**
- Ensure iLO Security Override switch is ON
- Have FIRMWARE RECOVERY mode ready
- Test on non-production hardware first

---

## Part 10: Tools and References

### Required Tools

| Tool | Purpose |
|------|---------|
| Ghidra | Binary analysis |
| IDA Pro | Advanced reverse engineering |
| ilo4_toolbox | Firmware extraction |
| arm-none-eabi-* | ARM toolchain |
| python2 | Legacy tooling |

### Reference Documents

- `patches/277/patch_userland.json` - Working v2.77 patches
- `patches/277/asm/fn_handler.S` - Function handler assembly
- `patches/277/asm/stdout.S` - Logging patch assembly
- `research/2022-02-17-docs.md` - Jump table research
- `research/2022-02-19-onto-277.md` - Build notes
- `plans/plan_copy_function_pointers.md` - Alternative approach

### Key Strings to Search

```
health_ipc_call
VSPCHANNEL
fan
ocsd
ocbb
h (health)
```

---

## Appendix A: Quick Reference Commands

```bash
# Extract firmware
python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py <firmware.bin> <output_dir>

# Find patterns
xxd build/elf.bin | grep "pattern"

# Compare binaries
python2 util/compare_fw.py build/277/elf.bin build/278/elf.bin 277 278

# Apply patches
python2 util/patch.py build/elf.bin patches/278/patch_userland.json build/elf.bin.patched
```

---

## Appendix B: Failure Mode Reference

| Symptom | Likely Cause |
|---------|--------------|
| Command not found | Command renaming patch failed |
| Command hangs | health_ipc_call routing issue |
| Fans don't respond | Handler table not patched |
| iLO won't boot | Signature bypass not applied |
| Output garbled | Library call addresses wrong |

---

**End of Methodology Document**
