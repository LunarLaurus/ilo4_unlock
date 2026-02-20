# Work Plan: Porting Fan Control to iLO4 v2.78/2.79
## Strategy: Copy Function Pointers from v2.77

**Created:** 2026-02-17  
**Objective:** Restore fan control functionality in iLO4 v2.78/2.79 by copying working function pointers from v2.77  
**Status:** Research Complete - Execution Ready

---

## Executive Summary

This plan documents the methodology for porting fan control from iLO4 v2.77 (where it works) to v2.78/2.79 (where HPE removed the underlying functionality). The approach involves identifying the function pointer table in the .health userland component and copying working function addresses from v2.77 to replace NULL/stub handlers in v2.78+.

### Why This Works

- **v2.77**: Has fully functional fan control via switch values 5-8 in the health IPC handler
- **v2.78/2.79**: HPE removed the actual fan control code but left the command infrastructure (renamed commands, function handler injection) intact
- **Solution**: Find the function pointers in v2.77 health module and copy them to v2.78/2.79

---

## Part 1: Background Research

### 1.1 Current State of Patches

| Version | Signature Bypass | CLI Commands | Fan Functions |
|---------|-----------------|--------------|---------------|
| 2.77    | Working         | Working      | Working       |
| 2.78    | Working         | Working      | Removed       |
| 2.79    | Working         | Working      | Removed       |

### 1.2 Key Offsets (Verified from Existing Patches)



| Patch Element     | v2.77 Offset  | v2.78 Offset  | Delta    |

|-------------------|---------------|---------------|----------|

| Sig Bypass        | 0x96EDE8      | 0x964ADC      | -0x9A2C  |

| quit -> OCBB      | 0xB80348      | 0xB73F70      | -0xC3D8  |

| VSPR -> h         | 0xB8045C      | 0xB74084      | -0xC3D8  |

| DEBUG -> OCSD     | 0xB80474      | 0xB7409C      | -0xC3D8  |

| NULL_CMD -> FAN   | 0xB804D0      | 0xB740F8      | -0xC3D8  |

| fn_handler        | 0xAFD768      | 0xAF1390      | -0xC3D8  |



### 1.3 The Switch-Case Handler System

The fan commands use switch values 5-8:
- **Switch 5**: Health info (h)
- **Switch 6**: Fan control (fan)
- **Switch 7**: On-chip sensors (ocsd)
- **Switch 8**: On-chip battery/broadband (ocbb)

These map to a jump table in .health.elf.text that dispatches to the appropriate handler function.

Reference: From research/2022-02-17-docs.md - ".health call traced back; uses jumptable w/ 5/6/7/8 value to call fan"

### 1.4 Function Handler Injection (fn_handler.S)

In v2.77, patched function handler at 0xAFD768 (patches/277/asm/fn_handler.S):

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
    ADD     R0, R7, #0x1000     ; Move R0 to start of input arg
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

Key insight: The handler calls health_ipc_call() at offset 0x3E420 (v2.77), which then uses a switch/jump table to dispatch to the actual fan/health/ocsd/ocbb functions.

---

## Part 2: Step-by-Step Methodology

### Phase 1: Extraction and Preparation

#### Step 1.1: Download Firmware Images
```bash
# Using existing build.sh infrastructure
./build.sh init
```

#### Step 1.2: Extract Firmware
```bash
# Extract v2.77 (reference)
python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py binaries/ilo4_277.bin build/277_ref

# Extract v2.78 (target)
python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py binaries/ilo4_278.bin build/278_target

# Extract v2.79 (target)
python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py binaries/ilo4_279.bin build/279_target
```

This produces:
- build/*/elf.bin - Userland component
- build/*/kernel_main.bin - Kernel component

#### Step 1.3: Identify ELF Sections
```bash
# Use existing compare_fw.py tool
python2 util/compare_fw.py build/277_ref/elf.bin build/278_target/elf.bin 277 278
```

---

### Phase 2: Finding the Handler Table

#### Step 2.1: Locate health_ipc_call Function

The key function is health_ipc_call() which contains the switch-case dispatcher.

**Method A: From fn_handler Reference**
The patched fn_handler calls BL 0x3E420 which is health_ipc_call in v2.77.

The health module (.health.elf) is loaded at specific virtual addresses. From ilo4_toolbox/scripts/iLO4/log/dissection.log:
```
.health.elf.text at 0x00ea8000, size 0x000a7e78
.health.elf.data at 0x00f50000, size 0x00001914
```

**Method B: Find in ELF Symbol Table**
```bash
# Search for health_ipc_call string in elf.bin
strings build/277_ref/elf.bin | grep -i health_ipc
```

**Method C: Pattern Search**
```bash
# Look for the BL instruction pattern in the injected handler
# BL 0x3E420 = 0xEBxxxxxx (ARM branch with offset)
```

#### Step 2.2: Find the Jump Table

The switch-case jump table is typically:
1. A table of function pointers (4 bytes each on ARM, little-endian)
2. Located near the health_ipc_call function
3. Indexed by the switch value (5-8)

**Search Pattern in Binary:**
```bash
# Look for NULL pointers in a row (likely removed handlers)
xxd build/278_target/elf.bin | grep -A2 "0000 0000"

# Look for function pointer patterns (non-NULL addresses)
# Typical ARM: 0x00XXXXXX or 0x01XXXXXX
```

**In IDA Pro/Ghidra:**
1. Load the v2.78 elf.bin as ARM little-endian
2. Navigate to health_ipc_call function (search for 0x3E420 reference)
3. Look for CMP R0, #max followed by LDR PC, [PC, R0, LSL #2]
4. The jump table follows this instruction pattern

#### Step 2.3: Map Switch Values to Handler Table Entries

The switch values map to table entries (0-indexed):
- Switch 5 (health): table + 0x00
- Switch 6 (fan):    table + 0x04
- Switch 7 (ocsd):   table + 0x08
- Switch 8 (ocbb):  table + 0x0C

---

### Phase 3: Identifying NULL Handlers in v2.78/2.79

#### Step 3.1: Compare Handler Tables Between Versions

Use binary diff to find differences in the handler table region:

```python
import struct

def compare_handlers(v277_path, v278_path, table_offset):
    with open(v277_path, "rb") as f:
        v277 = f.read()
    with open(v278_path, "rb") as f:
        v278 = f.read()
    
    print("Comparing handler table at offset 0x{:X}".format(table_offset))
    print("v2.77          v2.78")
    print("-" * 40)
    
    for i, switch_val in enumerate([5, 6, 7, 8]):
        off = table_offset + (i * 4)
        v277_ptr = struct.unpack("<I", v277[off:off+4])[0]
        v278_ptr = struct.unpack("<I", v278[off:off+4])[0]
        print("Switch {}: 0x{:08X}  0x{:08X}".format(switch_val, v277_ptr, v278_ptr))
```

#### Step 3.2: Identify NULL/Stub Patterns

In v2.78/2.79, expect one of these patterns for removed handlers:

1. **NULL pointers**: 00 00 00 00
2. **Stub functions**: Very small function (5-10 bytes) that returns immediately
3. **Error handlers**: Function that returns error code

**Verify with Disassembly:**
In IDA/Ghidra:
1. Load v2.78 elf.bin
2. Go to where handler pointers should be (v2.77 offset + delta)
3. Disassemble what the pointers reference
4. Check if they are NULL or stub code

---

### Phase 4: Locating Working Function Addresses in v2.77

#### Step 4.1: Extract Handler Addresses from v2.77

```python
import struct

def read_arm_pointer(data, offset):
    """Read 4-byte little-endian ARM pointer"""
    return struct.unpack("<I", data[offset:offset+4])[0]

# Read handler addresses from v2.77 jump table
v277_table_offset = 0xXXXXXX  # TO BE DETERMINED

handler_health = read_arm_pointer(v277_data, v277_table_offset + 0x00)  # Switch 5
handler_fan     = read_arm_pointer(v277_data, v277_table_offset + 0x04)  # Switch 6
handler_ocsd    = read_arm_pointer(v277_data, v277_table_offset + 0x08)  # Switch 7
handler_ocbb    = read_arm_pointer(v277_data, v277_table_offset + 0x0C)  # Switch 8

print("v2.77 Working Handler Addresses:")
print("  Switch 5 (health): 0x{:08X}".format(handler_health))
print("  Switch 6 (fan):    0x{:08X}".format(handler_fan))
print("  Switch 7 (ocsd):  0x{:08X}".format(handler_ocsd))
print("  Switch 8 (ocbb):  0x{:08X}".format(handler_ocbb))
```

#### Step 4.2: Verify Handlers Are Functional

Check that pointers in v2.77:
1. Point to code (not data or zero)
2. Have valid ARM function prologs (PUSH, SUB instructions)
3. Match expected behavior

```python
def verify_handler_is_code(data, ptr, base_vaddr, text_offset):
    """Verify pointer references valid code"""
    # Convert virtual address to file offset
    # This depends on ELF section layout
    
    # Check for valid ARM function prolog patterns
    code_patterns = [
        b"\x0D\xC0\xA0\xE1",  # MOV R12, SP
        b"\x2D\xE9",            # PUSH {..}
        b"\x04\x00",            # SUB SP, SP, #..
    ]
    
    return any(pattern in code_at_offset for pattern in code_patterns)
```

---

### Phase 5: Patching v2.78/2.79

#### Step 5.1: Calculate Patch Offsets

Using delta -0xC3D8 as starting point:

| Element           | v2.77 File Offset | v2.78 File Offset (estimated) |
|-------------------|-------------------|------------------------------|
| Jump Table Base   | TBD               | TBD                          |
| Handler 5 (h)     | TBD               | TBD                          |
| Handler 6 (fan)   | TBD               | TBD                          |
| Handler 7 (ocsd)  | TBD               | TBD                          |
| Handler 8 (ocbb)  | TBD               | TBD                          |

Note: File offsets differ from virtual addresses due to ELF section layout.

#### Step 5.2: Virtual Address to File Offset Conversion

```python
# Convert handler VA to file offset using ELF section headers
def va_to_offset(elf_data, va):
    """Convert ARM virtual address to file offset"""
    # Parse ELF header to find .text section
    # offset = va - section_vaddr + section_file_offset
    
    # Simplified: assume linear mapping for health module
    # Actual conversion requires parsing section headers
    pass
```

#### Step 5.3: Create Patch JSON

```json
[
    {
        "remark": "Patch fan handler (switch 6) to v2.77 function",
        "offset": "0xXXXXXXXX",
        "size": 4,
        "prev_data": "00 00 00 00",
        "patch": "AA BB CC DD"
    }
]
```

**Important Notes:**
- Use Little-Endian byte order for ARM pointers
- Verify prev_data matches before patching
- The patched value is the VIRTUAL ADDRESS from v2.77, stored as 4 bytes little-endian

#### Step 5.4: Alternative - Redirect to Injected Handler

Instead of fixing the jump table, could redirect to the injected function handler at 0xAF1390:

The v2.78 fn_handler patch (patches/278/patch_userland.json) already injects a custom handler:
```assembly
05 00 A0 E3    ; MOV R0, #5
04 00 00 EA    ; B to next
06 00 A0 E3    ; MOV R0, #6
02 00 00 EA    ; B to next
...
```

This handler could be modified to call fan functions directly, bypassing the health_ipc_call switch table entirely.

---

## Part 6: Verification and Testing

### Step 6.1: Pre-Flash Verification

Before flashing:
1. Verify patch bytes match expected values
2. Check no adjacent data corrupted
3. Recalculate checksums if applicable

```bash
# Verify patch application
xxd -l 32 -s 0xXXXXXXXX build/278_target/elf.bin.patched
```

### Step 6.2: Build Complete Firmware

Follow existing build process for v2.78:
```bash
cd patches/278
./build.sh
# or
../../build.sh
```

### Step 6.3: Functional Testing Sequence

Connect via SSH or Serial:
```bash
# Test basic connectivity
ping <ilo-ip>
ssh admin@<ilo-ip>

# Test fan commands
fan
help fan
fan info
fan temp
fan speed 25
fan start
fan stop
```

### Expected Results

Success indicators:
- fan command recognized (not "Unknown command")
- fan info returns controller information
- fan temp shows temperature sensors
- fan speed XX changes fan speed
- fan start enables auto fan control

---

## Part 7: Risks and Mitigations

### 7.1 Address Relocation

**Risk:** Function addresses differ between v2.77 and v2.78 due to binary reorganization.

**Mitigation:**
1. Use delta table (-0xC3D8) as starting point for searching
2. Verify each handler address is valid in target
3. May need to find corresponding functions by behavior, not direct address

### 7.2 ASLR/Position Independence

**Risk:** iLO may use ASLR or PIC.

**Analysis:**
- Existing patches work, so ASLR is NOT active
- Delta between versions is consistent (-0xC3D8)
- Function addresses are static between boots

### 7.3 Signature Validation

**Risk:** Modified firmware triggers signature validation failure.

**Mitigation:**
- Existing signature bypass patches MUST be applied first:
  - Bootloader patch: Bypass first-stage validation
  - Kernel patch: Bypass kernel-stage validation
  - Userland patch: Bypass elf validation
- Execution order: Apply all existing v2.78 patches FIRST, THEN apply handler table patches

### 7.4 Hardware Damage

**Risk:** Improper fan control causes server overheating.

**Mitigation:**
1. Test with server monitoring active
2. Keep fan start command ready to restore auto control
3. Never set fans to 0% for extended periods
4. Consider adding thermal protection in custom handler

### 7.5 iLO Brick

**Risk:** Bad firmware flash leaves iLO unusable.

**Mitigation:**
1. Ensure iLO Security Override switch is ON before flashing
2. Have recovery procedure (FIRMWARE RECOVERY mode)
3. Test on non-production hardware first
4. Keep original firmware backup

---

## Part 8: Tools and References

### 8.1 Required Tools

| Tool | Purpose |
|------|---------|
| ilo4_extract.py | Extract firmware components |
| IDA Pro / Ghidra | Reverse engineer binaries |
| ARM disassembler | Analyze handler code |
| hexdump/xxd | Binary inspection |
| patch.py | Apply JSON patches |
| compare_fw.py | Compare firmware versions |

### 8.2 Reference Documents

- PORTING_RESEARCH.md - Existing research notes
- patches/277/patches.md - v2.77 patch documentation
- patches/277/asm/fn_handler.S - Function handler assembly
- research/2022-02-17-docs.md - Jump table research
- research/2022-02-18-building-279.md - v2.79 build notes

### 8.3 Key Strings to Search

In extracted elf.bin:
- health_ipc_call
- fan
- ocsd
- ocbb
- h (health)

### 8.4 Key Binary Patterns

```bash
# Signature bypass (BEQ -> B)
1D 00 00 0A  ->  BEQ (original)
1D 00 00 EA  ->  B (patched)

# Handler table NULL entries
00 00 00 00

# Function prolog
0D C0 A0 E1  ->  MOV R12, SP
20 D8 2D E9  ->  PUSH {R4,R5,R6,R7,R11,R12,LR,PC}
```

---

## Part 9: Execution Checklist

- [ ] Extract v2.77 firmware (reference)
- [ ] Extract v2.78 firmware (target)
- [ ] Verify existing patches apply correctly
- [ ] Locate health_ipc_call in both versions
- [ ] Find jump/handler table in v2.77
- [ ] Identify NULL handlers in v2.78
- [ ] Extract working function addresses from v2.77
- [ ] Calculate file offsets for v2.78
- [ ] Create handler table patch JSON
- [ ] Test patch application locally
- [ ] Build complete v2.78 firmware
- [ ] Flash and test on hardware (non-production first)
- [ ] Verify all fan commands work
- [ ] Document final offsets for future versions

---

## Appendix A: Quick Reference Commands

```bash
# Extract firmware
python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py <firmware.bin> <output_dir>

# Compare binaries  
python2 util/compare_fw.py build/277_ref/elf.bin build/278_target/elf.bin 277 278

# Apply patches
python2 util/patch.py build/elf.bin patches/278/patch_userland.json build/elf.bin.patched

# Find patterns in binary
xxd build/278_target/elf.bin | grep "pattern"
```

---

## Appendix B: Failure Mode Reference

| Symptom | Likely Cause |
|---------|--------------|
| Command not found | Command renaming patch failed |
| Command hangs | health_ipc_call routing issue |
| Fans dont respond | Handler table not patched correctly |
| iLO wont boot | Signature bypass not applied |

---

**End of Plan**

