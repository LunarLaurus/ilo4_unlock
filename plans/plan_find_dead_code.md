# iLO4 Fan Control Recovery: Dead Code Search Work Plan
## Version Target: iLO4 2.78/2.79

**Mission Objective:** Recover fan control functionality in iLO4 v2.78/2.79 by locating disabled, unreferenced, or dead code that HPE may have left behind during the fan control feature removal.

**Commander:** Fleet Commander Lauren
**Planning Unit:** Meridian Lex
**Date:** February 2026

---

## Executive Summary

### The Problem
- iLO4 2.77: Fan control works completely (signature bypass + functional IPC handlers)
- iLO4 2.78/2.79: Signature bypass works, command renaming works, but IPC handlers for fan control are stripped

### Why This Matters
HPE intentionally removed the fan control IPC logic between 2.77 and 2.78. However, based on firmware development patterns, portions of this code may still exist in the binary but be:
1. Unlinked (not in the call graph)
2. Disabled via branch nops or jumps to ret
3. Present but unreferenced in the function pointer tables

---

## Phase 1: Firmware Extraction and Preparation

### 1.1 Acquire Firmware Binaries
Using existing build.sh infrastructure:
./build.sh init

Expected output in binaries/:
- ilo4_277.bin (working reference)
- ilo4_278.bin (target)
- ilo4_279.bin (target)

### 1.2 Extract Firmware Components
python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py binaries/ilo4_277.bin build/277_ref
python2 ilo4_toolbox/scripts/iLO4/ilo4_extract.py binaries/ilo4_278.bin build/278_target

### 1.3 Analysis Tools Recommended
- IDA Pro (with ARMv7 disassembler)
- Ghidra (free, supports ARM)
- Binary Ninja (with Firmware Ninja plugin)
- Radare2 (command-line, excellent for scripting)

---

## Phase 2: Binary Analysis Methodology

### 2.1 Entropy Analysis
Tool: binwalk

Purpose: Identify code vs data regions, find compressed/encrypted sections

binwalk -E build/278_target/kernel_main.bin

High entropy = compressed/encrypted
Low entropy (~1.0-2.0) = code

### 2.2 String Analysis
Tool: strings + grep

strings -el build/278_target/kernel_main.bin > strings.txt
grep -i fan strings.txt

Target strings from 2.77:
- fan, fan info, fan p, fan t, fan pid, fan g
- health_ipc_call
- switch values 5-8

### 2.3 Function Call Graph Analysis
In IDA/Ghidra:
1. Filter functions by number of cross-references (Xrefs)
2. Identify unreferenced functions
3. Exclude: exception handlers, interrupt handlers, thread entry points

---

## Phase 3: Identifying Unreferenced Functions

### 3.1 Detection Strategies

Strategy A: Compare 2.77 vs 2.78 Function Lists
python2 util/compare_fw.py build/277_ref/kernel_main.bin build/278_target/kernel_main.bin 277 278

Strategy B: Binary Diffing (BinDiff/Diaphora)
Compare elf.bin from 2.77 vs 2.78

Strategy C: Function Prologue Search
Search for ARM function prologues in unclassified regions
binwalk -A kernel.bin

### 3.2 Key Offsets from Patch Analysis

2.77 Userland:
- Signature bypass: 0x96EDE8
- Command strings: 0xB80348 - 0xB804D0
- Function handler: 0xAFD768

2.78 Userland:
- Signature bypass: 0x964ADC
- Command strings: 0xB73F70 - 0xB740F8
- Function handler: 0xAF1390

Delta of -0xC3D8 suggests similar code layout with minor reorganization.

---

## Phase 4: Specific Search Targets

### 4.1 Primary Targets (Kernel)

- health_ipc_call: Main IPC handler function
- Fan switch handler: Code handling switch=6
- Temperature reading: Reading CPU/ambient sensors
- PWM output: Writing fan speeds
- Fan zone logic: Managing multiple fan zones

### 4.2 Search Algorithm
1. Extract all strings from 2.77 and 2.78 kernels
2. Identify strings present in 2.77 but missing in 2.78
3. Search 2.78 for partial matches or similar strings
4. Locate any code references to fan-related strings in 2.78
5. Cross-reference with function call graphs

---

## Phase 5: Verification and Testing

### 5.1 Code Verification Checklist
- Code has valid ARM branch instructions
- Function prologues are intact (not NOPs)
- All external calls point to valid addresses
- No obvious infinite loops

### 5.2 Testing Approach
After signature bypass applied:
1. Test: ssh fan info (should display info)
2. Test: fan p 0 min 30 (should change speed)
3. If CLI works but fans dont respond: IPC layer issue

---

## Phase 6: Fallback Approaches

If NO Dead Code Found:

Option A: Port from 2.77 Kernel
1. Extract fan control function from 2.77 kernel
2. Analyze all dependencies
3. Port assembly to 2.78 kernel address space

Option B: Use Function Pointer Table
1. Find function pointer table in userland
2. Locate entries for switches 5-8
3. Compare 2.77 vs 2.78 table entries

Option C: Reimplement from Documentation
- ARM Cortex-A9 technical reference
- HP ProLiant hardware documentation
- IPMI fan control specifications

---

## Phase 7: Implementation

Once dead code located:
1. Create JSON patch following existing format
2. Test in isolated environment
3. Update build.sh or create new patch set

---

## Tools and Resources

### Required Tools
- binwalk: Firmware extraction, entropy
- IDA Pro/Ghidra: Disassembly/analysis
- Radare2: Scriptable analysis
- ARM toolchain: Assembly/disassembly

### Reference Files in This Project
- ilo4_toolbox/scripts/iLO4/ilo4_extract.py
- ilo4_toolbox/scripts/iLO4/ilo4lib.py
- util/compare_fw.py
- patches/277/ (working 2.77 patches)
- util/asm/fan_research.S (fan research payload 2.77)

---

## Success Criteria
1. Dead code located in 2.78 kernel and/or userland
2. Code is functional when re-enabled
3. Fan control works via SSH CLI after patching
4. Documentation of findings for future porting

---

## Timeline Estimate
- Phase 1-2: 3 hours
- Phase 3-4: 8-16 hours
- Phase 5-6: 4 hours
- Phase 7: 8-16 hours

Total: 23-39 hours

---

## Appendix: ARM Thumb Instruction Patterns

Function Prologue (Thumb):
B5 00: PUSH {R4,R5,R7,LR}
B0 09: SUB SP, #0x24

Common NOP:
46 00: MOV R0, R0
00 20: MOVS R0, #0

Branch (unconditional):
F7F7 xxxx: B.W #offset (Thumb-2)
EAxx xxxx: B #offset (ARM)

Identifying Disabled Code:
- MOVS R0, #0 + POP: Function returns immediately
- Multiple NOPs: Code NOP-ed out
- BX LR: Early return stub

---

Plan Version: 1.0
Last Updated: February 2026
Author: Meridian Lex
Status: Ready for Execution
