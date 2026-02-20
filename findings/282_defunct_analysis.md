# iLO4 Fan Control Porting - 2.82 Complete Analysis

## Executive Summary

**Fan code EXISTS in 2.82** - 61 of 64 fan strings present. The "defunct" behavior is caused by a single BEQ instruction that was modified to point to the defunct error path instead of the normal fan control flow.

## Key Findings

### 1. Fan Code is Present
```
Unique fan strings in 2.77: 64
Unique fan strings in 2.82: 61

Missing in 2.82 (only 3):
  - fan:\n (label)
  - fan: Debug Status:\n
  - fan: unsupported.\n
```

All core fan functions exist in 2.82.

### 2. Root Cause Found!

The defunct message is NOT due to removed code - it's a **single instruction change** in the BEQ branch target.

**Location:** File offset 0x39e0c4 in extracted ELF

**The Problem:**
- In **2.77**: BEQ at offset 0x39ca40 targets 0x39ca54 (continues to normal fan control)
- In **2.82**: BEQ at offset 0x39e0c4 targets 0x39e0d8 (**goes to defunct error path!**)

The comparison logic loads a flag byte from the fan state structure, compares it with the fan speed parameter, and branches to defunct if equal. In 2.82, this branch now goes to the defunct error handler instead of continuing to fan control.

### 3. Code Flow Analysis

```
At 0x39e0bc: LDRB R1, [R5, #1]   ; Load flag from fan state structure
At 0x39e0c0: CMP R6, R1            ; Compare with fan speed parameter
At 0x39e0c4: BEQ 0x39e0d8          ; IF EQUAL -> defunct (WRONG TARGET!)
```

The BEQ at 0x39e0c4 should skip the defunct path, but instead it jumps to the defunct error handler.

### 4. The Fix

Simple patch: NOP out the BEQ at offset 0x39e0c4

**Current:** `0a 00 00 ea` (BEQ to defunct)
**Patch:**   `00 00 00 ea` (NOP - always continue to fan control)

### 5. Flag Initialization

The flag at [R5+1] is initialized to 0 in both 2.77 and 2.82:
- At 0x39dc00: `MOV R0, #0`
- At 0x39dc04: `STRB R0, [R5, #1]`

This is identical in both versions - not the cause of the issue.

## File Offsets (2.82 Extracted ELF)

| Component | File Offset |
|----------|-------------|
| FAN_SET handler start | 0x39e064 |
| **BEQ (THE PATCH)** | **0x39e0c4** |
| MOV R1, #0x8c | 0x39e0cc |
| Defunct message | 0x39e1c8 |
| fan: dispatcher | 0x39dd10 |
| fan: FAN_SET | 0x39e164 |

## Patch File

Location: `patches/282/patch_userland.json`

```json
{
    "offset": "0x39e0c4",
    "prev_data": "0a 00 00 ea",
    "patch": "00 00 00 ea"
}
```

**Note:** This offset is in the extracted ELF (build/282/elf.bin). The offset in the compressed firmware will differ.
