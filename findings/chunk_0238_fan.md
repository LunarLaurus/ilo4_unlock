# Research Findings: chunk_0238_00474000.xml

## File Information

**Status: FILE NOT FOUND**

The requested file `ilosrc/chunk_0238_00474000/chunk_0238_00474000.xml` does not exist in the archive.

### Available Alternatives

| Chunk Number | Address Offset | Exists | Notes |
|-------------|----------------|--------|-------|
| chunk_0237 | 00474000 | YES | At exact requested address |
| chunk_0238 | 00476000 | YES | Same chunk number, different offset |

### This Report

This report covers the analysis of **chunk_0237_00474000** (the available chunk at the requested address) as the substitute for the non-existent chunk_0238_00474000.

---

## Search Results for chunk_0237_00474000

### 1. Functions with "fan" in the name
**Result: NONE FOUND**

No functions containing "fan", "Fan", or "FAN" were found in this chunk.

---

### 2. PWM Control Code
**Result: NONE FOUND**

No PWM-related code or references found in this chunk.

---

### 3. Temperature Sensor Handling
**Result: NONE FOUND**

No temperature sensor functions or references found in this chunk.

---

### 4. Functions with "tach" or "temp" references
**Result: NONE FOUND**

No tachometer or temperature-related functions found in this chunk.

---

## Chunk Analysis Details

### File Analyzed (Substitute)
- **File**: `ilosrc/chunk_0237_00474000/chunk_0237_00474000.xml`
- **Lines**: 2000
- **Chunk ID**: 237
- **Address Range**: `010f7288` - `0110xxxx`

### Module Context

This chunk is in the **0x010fxxxx memory region**, which is different from the `.health` module where fan control code is located:

| Module | Address Range | Contains Fan Control |
|--------|---------------|---------------------|
| `.health.elf.text` | 0x00ea8000 - 0x00f27xxx | YES |
| This chunk (0237) | 0x010f7288+ | NO |

The fan control code for iLO 4 is located in the `.health` module at approximately:
- Jump table at `0x00E04CB4` (switch dispatch)
- `health_ipc_call` at offset `0x3E420` (virtual address `0x00ec2420`)
- Switch value 6 handles fan commands

---

## Functions in This Chunk

| Address Range | Function Name Pattern |
|---------------|----------------------|
| 010f7288 - 010f72d3 | FUN_010f7288 |
| 010f72d4 - 010f731f | FUN_010f72d4 |
| 010f75c8 - 010f764f | FUN_010f75c8 |
| 010f7658 - 010f767f | FUN_010f7658 |
| 010f7680 - 010f88df | FUN_010f7680 (complex, multiple ranges) |
| 010f8e00 - 010f8f3f | FUN_010f8e00 |
| 010f8f40 - 010f9093 | FUN_010f8f40 |
| 010f9328 - 010f952f | FUN_010f9328 |
| 010f9530 - 010f95cf | FUN_010f9530 |
| 010f95d0 - 010f993b | FUN_010f95d0 (complex) |
| 010f993c - 010f9c8f | FUN_010f993c |
| 010f9c90 - 010fa56f | FUN_010f9c90 (complex) |
| 010fa570 - 010fa607 | FUN_010fa570 |
| 010fa9b0 - 010faa6b | FUN_010fa9b0 |
| 010fabe4 - 010fac2b | FUN_010fabe4 |
| 010fac2c - 010fad6b | FUN_010fac2c |
| 010fad6c - 010fb26b | FUN_010fad6c |
| 010fb26c - 010fb41f | FUN_010fb26c |
| 010fb420 - 010fb84b | FUN_010fb420 (complex) |
| 010fb998 - 010fba77 | FUN_010fb998 |
| 010fba78 - 010fbb3f | FUN_010fba78 |
| 010fbe50 - 010fbe83 | FUN_010fbe50 |
| 010fbe84 - 010fbf1b | FUN_010fbe84 |
| 010fbf1c - 010fbffb | FUN_010fbf1c |
| 010fbffc - 010fc443 | FUN_010fbffc (complex) |
| 010fc444 - 010fc547 | FUN_010fc444 |
| 010fd014 - 010fd377 | FUN_010fd014 (complex) |
| 010fd378 - 010fd45f | FUN_010fd378 |
| 010fd594 - 010fd5e3 | FUN_010fd594 |
| 010fd5e4 - 010fd6bf | FUN_010fd5e4 |
| 010fd6c0 - 010fd6db | FUN_010fd6c0 |
| 010fd6dc - 010fd7bf | FUN_010fd6dc |
| 010fd7c0 - 010fd80b | FUN_010fd7c0 |
| 010fd80c - 010fd9df | FUN_010fd80c |
| 010fd9e0 - 010fdbb3 | FUN_010fd9e0 |
| 010fdbb4 - 010fe353 | FUN_010fdbb4 (complex) |
| 010fe354 - 010fe3d3 | FUN_010fe354 |
| 010fe3d4 - 010fe897 | FUN_010fe3d4 (complex) |
| 010fec98 - 010fed5b | FUN_010fec98 |
| 010ff54c - 010ff723 | FUN_010ff54c |
| 010ff724 - 010ff763 | FUN_010ff724 |
| 010ffc50 - 010ffe13 | FUN_010ffc50 |
| 010ffe14 - 0110084f | FUN_010ffe14 (complex, multiple ranges) |
| 01100850 - 0110093f | FUN_01100850 |
| 011009c8 - 01100b0b | FUN_011009c8 |
| 01100b74 - 01100f17 | FUN_01100b74 |
| 01100f18 - 01101137 | FUN_01100f18 |
| 01101138 - 011014e3 | FUN_01101138 (complex) |

---

## Summary

**This chunk does NOT contain fan control, PWM, temperature sensor, or tachometer code.**

The fan control code in iLO 4 is located in the `.health` module at lower memory addresses (0x00ea-0x00ec range). The relevant chunks for fan control research are:

- `chunk_0228_00456000` - Part of `.health.elf.text`
- `chunk_0229_00458000` - Contains `health_ipc_call` area

See `plans/research_fan_code_locations.md` for complete fan control code locations.

---

## References

- `plans/research_fan_code_locations.md` - Fan control code research (shows fan is at switch value 6)
- `findings/chunk_0228_fan.md` - Analysis of .health module code
- `findings/chunk_0229_fan.md` - Analysis containing health_ipc_call area

---

*Generated: Research analysis - chunk_0238_fan.md (substituted with chunk_0237_00474000)*
