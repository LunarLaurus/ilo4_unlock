# Work Plan: Reimplementing Fan Control for iLO4 v2.78/2.79

## Executive Summary

This document outlines a comprehensive methodology for porting fan control functions from iLO4 v2.77 to v2.78/2.79 by reimplementing the removed assembly code. The core challenge is that HPE completely removed the fan control logic from .health module in v2.78+, requiring extraction and reimplementation of working code from v2.77.

---

## 1. Background and Problem Analysis

### 1.1 Current State

| Version | Signature Bypass | Command Injection | Fan Functions |
|---------|------------------|-------------------|---------------|
| 2.77    | Working          | Working           | Working       |
| 2.78    | Working          | Working           | REMOVED       |
| 2.79    | Working          | Working           | REMOVED       |

### 1.2 What Was Removed

From the research journal (2022-02-18):
- The .health module's fan CLI tool was completely removed
- Only stub handlers remain that do nothing
- Fan-related strings still exist but are unreferenced

### 1.3 Architecture Overview

User SSH Command -> fn_handler.S (patched at 0xAFD768 in 2.77) -> Command Switch (values 5=health, 6=fan, 7=ocsd, 8=ocbb) -> health_ipc_call (at 0x3e420) -> .health module (REMOVED in 2.78+)

---

## 2. Understanding the Existing Assembly Code

### 2.1 fn_handler.S Analysis (patches/277/asm/fn_handler.S)

The current handler is a simple IPC bridge. Key points:
- Switch values 5-8 route to different handlers in .health
- Input string is parsed from R7+0x1000 (command line args)
- IPC struct: switch at SP+0x0, args at SP+0x4, response at SP+0x500
- health_ipc_call at offset 0x3e420 handles the actual IPC

### 2.2 IPC Struct Layout

Offset 0x00: Switch value (5=health, 6=fan, 7=ocsd, 8=ocbb)
Offset 0x04: Parsed command arguments (null-terminated strings)
Offset 0x500: Return value from handler

---

## 3. Step-by-Step Methodology

### Phase 1: Firmware Extraction and Preparation

Step 1.1: Download Firmware Binaries
```bash
./build.sh init
```

Step 1.2: Extract Firmware Components
```bash
python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py binaries/ilo4_277.bin build/277_extract
python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py binaries/ilo4_278.bin build/278_extract
```

Step 1.3: Identify Key Offsets
| Element           | 2.77 Offset   | 2.78 Offset   | Delta    |
|-------------------|---------------|---------------|----------|
| Sig Bypass        | 0x96EDE8      | 0x964ADC      | -9A2C    |
| NULL_CMD->FAN     | 0xB804D0      | 0xB740F8      | -C3D8    |
| fn_handler        | 0xAFD768      | 0xAF1390      | -C3D8    |

### Phase 2: Reverse Engineering Fan Functions in 2.77

Step 2.1: Locate the .health Module
```bash
arm-none-eabi-readelf -S build/277_extract/userland.elf | grep -i health
strings build/277_extract/userland.elf | grep -i fan
```

Step 2.2: Identify Fan Command Handlers
Search for fan subcommand handlers (temp, tach, pwm, pid)

Step 2.3: Disassemble the health_ipc_call Target
Find the jump table in .health for switches 5-8, navigate to case 6 (fan handler)

### Phase 3: Address Translation Strategy

Step 3.1: Address Space Changes
Delta between versions is approximately -0xC3D8

Step 3.2: Function Pointer Table Recovery
In 2.78+, switch handlers are NULL or return immediately

Step 3.3: Binary Diffing
Use BinDiff to compare 2.77 vs 2.78 to identify removed functions

---

## 4. Implementation Approaches

### Option A: Direct Function Porting
Extract fan control assembly from 2.77, update addresses, patch 2.78 handler

### Option B: IPC Wrapper Approach  
Create wrappers that reconstruct IPC calls for kernel interface

### Option C: Kernel Fan Control
Research whether fan control is in userland or kernel

---

## 5. Tools Required

### Disassembly and Analysis
- IDA Pro (Primary)
- Ghidra (Open-source)
- Binary Ninja
- radare2 (Command-line)

### ARM Analysis Tools
- arm-none-eabi-objdump (Disassembler)
- arm-none-eabi-readelf (ELF analysis)
- arm-none-eabi-strings (String extraction)

### Binary Comparison
- BinDiff
- Diaphora

### Build Tools
- arm-none-eabi-gcc
- arm-none-eabi-as
- python2.7

---

## 6. Testing Approach

### Pre-Flash Testing
1. Verify patch offsets
2. Validate assembly compiles
3. Check for conflicts

### Safe Flash Testing
1. Flash patched firmware
2. Test: h (health)
3. Test: fan (should show menu)
4. Test: fan temp
5. Test: fan tach

### Safety Precautions
- DO NOT test PWM without monitoring
- Have recovery method ready
- Document original fan speeds

---

## 7. Risks and Fallback Options

### Risks
| Risk                   | Severity | Mitigation                          |
|------------------------|----------|-------------------------------------|
| Code completely removed | HIGH   | Reimplement from scratch           |
| Kernel interface changed | MEDIUM | New IPC protocol needed           |
| iLO brick              | HIGH    | Have recovery ready               |

### Fallbacks
1. Stay on 2.77 (stable)
2. Use 2.78/2.79 without fan control
3. Partial implementation (read-only)

---

## 8. Command Switch Reference

| Value | Command | Function |
|-------|---------|----------|
| 5     | h       | Health   |
| 6     | fan     | Fan      |
| 7     | ocsd    | Sensors  |
| 8     | ocbb    | Battery  |

### Key Addresses in 2.77
- 0x3e420: health_ipc_call
- 0xAFD768: fn_handler
- 0xB804D0: Command table

---

## 9. Implementation Checklist

### Phase 1: Preparation
- [ ] Download firmware binaries
- [ ] Extract all versions

### Phase 2: Analysis
- [ ] Locate .health module in 2.77
- [ ] Identify fan control functions
- [ ] Document addresses

### Phase 3: Design
- [ ] Choose approach
- [ ] Design handler architecture

### Phase 4: Development
- [ ] Write fan handler assembly
- [ ] Compile and test
- [ ] Create patch entries

### Phase 5: Testing
- [ ] Build firmware
- [ ] Test health command
- [ ] Test fan read operations

### Phase 6: Documentation
- [ ] Update patches/278/
- [ ] Create readme

---

## 10. References

- iLO4 Toolbox: https://github.com/airbus-seclab/ilo4_toolbox
- SSTIC 2018: HPE iLO4 case study
- ARM Architecture Reference Manual
- Existing patches: patches/277/asm/fn_handler.S
- Research: PORTING_RESEARCH.md
