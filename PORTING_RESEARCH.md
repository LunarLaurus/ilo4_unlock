# iLO4/5 Fan Control Porting Research

## Executive Summary

Porting fan controls to newer iLO4 (2.78/2.79) and iLO5 versions requires addressing two distinct challenges:

1. **iLO4 2.78/2.79**: Signature bypass works, but underlying fan control functions were **removed by HPE**
2. **iLO5**: Completely different architecture, requires full reverse engineering

---

## Part 1: iLO4 2.78/2.79 Analysis

### Current State

| Version | Signature Bypass | Command Names | Fan Functions |
|---------|------------------|---------------|---------------|
| 2.77 | ✅ Working | ✅ Working | ✅ Working |
| 2.78 | ✅ Working | ✅ Working | ❌ Removed |
| 2.79 | ✅ Working | ✅ Working | ❌ Removed |

The existing patches for 2.78/2.79 already include:
- Signature check bypass (offsets differ from 2.77)
- Command renaming (FAN, OCSD, OCBB, h)
- Function handler injection

However, the **underlying IPC calls** that control fans were stripped by HPE.

### The Problem

The patched commands call into `health_ipc_call()` with switch values 5-8:
- Switch 5: Health info (`h`)
- Switch 6: Fan control (`fan`) 
- Switch 7: On-chip sensors (`ocsd`)
- Switch 8: On-chip battery/broadband (`ocbb`)

In 2.77 and earlier, these switch values triggered actual fan control logic. In 2.78+, the handlers exist but perform no operations.

### Recovery Strategy

#### Option A: Reimplement Fan Logic (Hard)
1. Extract kernel from 2.77 (where fan control works)
2. Identify the exact fan control function addresses
3. Port that assembly code to 2.78/2.79 kernel
4. Patch the new switch handlers to call our reimplemented functions

**Challenges:**
- ARM assembly must be carefully ported (register usage, addresses)
- Function addresses will differ between versions
- Must understand the IPC protocol for fan commands

#### Option B: Copy Function Pointers (Medium)
1. Extract both 2.77 and 2.78 firmwares
2. Find the function pointer table in userland
3. In 2.78, locate where the NULL handlers are for switches 5-8
4. Patch to point to the same function addresses used in 2.77

**Challenges:**
- Function addresses change between versions
- May require signature bypass to still work

#### Option C: Find Disabled Code (Easier)
1. Search 2.78 kernel for the fan control functions (they may be present but not linked)
2. Look for dead code, unreferenced functions
3. Re-enable by fixing up branch targets and function pointers

**Challenges:**
- Code may be completely removed, not just disabled

---

## Part 2: Signature Bypass Methodology

### How It Works

The patches modify three components:

1. **Bootloader** (`patch_bootloader.json`): Changes `BNE` to `MOV R0, #0` at offset 0x38BC
2. **Kernel** (`patch_kernel.json`): Changes `BEQ` to `B` at offset 0x1FBB0  
3. **Userland** (`patch_userland.json`): Changes `BEQ` to `B` at offset 0x96EDE8

### Finding Offsets in New Versions

**Method 1: Pattern Matching**
```bash
# Search for the signature check pattern in extracted binaries
# Original ARM instruction: "1D 00 00 0A" (BEQ + offset)
# Patched: "1D 00 00 00 EA" (B unconditional)

# Use binwalk or hexdump to find similar patterns
binwalk -A bootloader.bin | grep -i "branch"
```

**Method 2: String/Reference Search**
1. Find strings like "signature", "verify", "cert" in the binary
2. Cross-reference with function that calls them
3. Find the conditional branch that validates

**Method 3: Compare with Working Version**
1. Extract 2.77 and 2.78 firmwares
2. Use bindiff or similar to compare identical components
3. Identify what changed in the signature verification code

### Automated Finding Script

```python
#!/usr/bin/env python2
# find_sig_check.py - Find signature check bypass location

import sys

def find_pattern_in_file(filepath, pattern):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Find all occurrences
    offsets = []
    start = 0
    while True:
        idx = data.find(pattern, start)
        if idx == -1:
            break
        offsets.append(hex(idx))
        start = idx + 1
    
    return offsets

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: find_sig_check.py <binary> <pattern_hex>")
        sys.exit(1)
    
    pattern = sys.argv[2].replace(' ', '').decode('hex')
    results = find_pattern_in_file(sys.argv[1], pattern)
    print("Found at: " + ", ".join(results))
```

---

## Part 3: iLO5 Porting Strategy

### Architecture Differences

| Component | iLO4 | iLO5 |
|-----------|------|------|
| Architecture | ARMv7 | ARMv8 (64-bit) |
| Bootloader | Single stage | Dual stage (BL1/BL2) |
| Secure Boot | Optional | Always enabled |
| Extraction | ilo4_extract.py | ilo5_extract.py |

### Existing iLO5 Research

The Airbus toolbox already provides:
- `ilo5_extract.py` - Firmware extraction
- `ilo5_fw_decrypt.py` - Firmware decryption
- `ilo5_PoC_fum_sig_bypass.py` - FUM signature bypass PoC
- `ilo5_PoC_secure_boot_bypass.py` - Secure boot bypass PoC

### iLO5 Research Required

1. **Extract iLO5 firmware** using the toolbox
2. **Identify command handler table** - likely similar structure to iLO4
3. **Find signature verification** - ARM64 instruction encoding differs
4. **Locate fan control functions** - may have different implementation
5. **Create extraction/patching pipeline** - similar to iLO4 build.sh

### Key Differences for ARM64

- 64-bit registers (X0-X30, W0-W30 for lower 32 bits)
- Different branch encoding (B vs BL, PC-relative offsets)
- Function calling convention may differ
- Stack alignment requirements

---

## Part 4: Practical Steps

### Step 1: Download Firmware

```bash
./build.sh init
```

This downloads all configured firmware versions to `binaries/`

### Step 2: Extract and Analyze

```bash
# Extract 2.77 (working reference)
python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py binaries/ilo4_277.bin build/277_ref

# Extract 2.78 (target)
python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py binaries/ilo4_278.bin build/278_target

# Compare
diff -q build/277_ref/ build/278_target/
```

### Step 3: Find New Offsets

Use the methodology in Part 2 to find:
- Signature check in bootloader
- Signature check in kernel  
- Signature check in userland
- Command string table location
- Handler function pointers

### Step 4: Test Signature Bypass First

Only after signature bypass works, proceed to fan control.

### Step 5: Implement Fan Control

Either:
- Port the 2.77 function handlers to 2.78, OR
- Find and enable the disabled code

---

## References

- Airbus iLO4 Toolbox: https://github.com/airbus-seclab/ilo4_toolbox
- SSTIC 2018: "Subverting your server through its BMC: the HPE iLO4 case"
- ARM Architecture Reference Manual (for instruction encoding)

---

## Appendix: Patch Comparison

### 2.77 vs 2.78 Userland Offsets

| Patch Element | 2.77 Offset | 2.78 Offset | Delta |
|--------------|-------------|-------------|-------|
| Sig Bypass | 0x96EDE8 | 0x964ADC | -9A2C |
| quit->OCBB | 0xB80348 | 0xB73F70 | -C3D8 |
| VSPR->h | 0xB8045C | 0xB74084 | -C3D8 |
| DEBUG->OCSD | 0xB80474 | 0xB7409C | -C3D8 |
| NULL_CMD->FAN | 0xB804D0 | 0xB740F8 | -C3D8 |
| fn_handler | 0xAFD768 | 0xAF1390 | -C3D8 |

The consistent delta suggests the userland binary is very similar but has been slightly reorganized.
