# iLO4 v2.77 Fan Control Code Research

**Research Date:** 2026-02-19  
**Target Version:** iLO4 v2.77  
**Objective:** Document fan control code locations for porting to v2.78+

---

## Executive Summary

This document contains all known addresses and code locations related to fan control in iLO4 v2.77. The fan control system uses a switch-case IPC mechanism through the `.health` module with switch values 5-8.

---

## 1. Key Function Addresses in v2.77

### 1.1 health_ipc_call Function

| Attribute | Value |
|----------|-------|
| **Function Offset** | `0x3E420` |
| **Location** | Within `.health.elf.text` module |
| **Purpose** | Main IPC handler that dispatches switch values 5-8 to appropriate handlers |

**Reference:** Called from patched `fn_handler` at `0xAFD768`:
```assembly
BL  0x3e420    ; health_ipc_call(SP, SP+500)
```

### 1.2 fn_handler (Patched Entry Point)

| Attribute | Value |
|----------|-------|
| **File Offset** | `0xAFD768` (v2.77) |
| **v2.78 Offset** | `0xAF1390` |
| **Delta** | `-0xC3D8` |
| **Purpose** | Parses CLI arguments and calls health_ipc_call with switch value |

**Source:** `patches/277/asm/fn_handler.S`

### 1.3 Switch Values

| Switch Value | Command | Function |
|-------------|---------|----------|
| 5 | `h` | Health info |
| 6 | `fan` | **Fan control** |
| 7 | `ocsd` | On-chip sensors |
| 8 | `ocbb` | On-chip battery/broadband |

---

## 2. .health Module Memory Locations

### 2.1 Module Virtual Addresses

From `ilo4_toolbox/scripts/iLO4/log/dissection.log`:

| Section | Virtual Address | Size |
|---------|----------------|------|
| `.health.elf.text` | `0x00ea8000` | `0x000a7e78` |
| `.health.elf.data` | `0x00f50000` | `0x00001914` |
| `.health.Initial.stack` | `0x00ffe000` | `0x00005000` |
| `.health.heap` | `0x01003000` | `0x00030000` |
| `health_device_readings` | `0x01063000` | `0x00002000` |

### 2.2 File Offsets

From dissection log (raw binary file offsets):

| Section | File Offset | Size |
|---------|------------|------|
| `.health.elf.text` | `0x0036ce5c` | `0x000a7e78` |
| `.health.elf.data` | `0x00414cd4` | `0x00001914` |

---

## 3. Jump Table Locations

### 3.1 Primary Jump Table

**Location:** `.health.elf.text:00E04CB4` (v2.73 reference)

This jump table dispatches switch values 5-8 to their respective handler functions.

**Table Structure (4 entries, 4 bytes each):**
```
Offset +0x00: Handler for switch 5 (health)
Offset +0x04: Handler for switch 6 (fan)
Offset +0x08: Handler for switch 7 (ocsd)
Offset +0x0C: Handler for switch 8 (ocbb)
```

### 3.2 Jump Table Search Pattern

In IDA Pro/Ghidra:
1. Navigate to `health_ipc_call` function
2. Look for `CMP R0, #max_value` followed by `LDR PC, [PC, R0, LSL #2]`
3. The jump table follows this instruction pattern

---

## 4. IPC Structure Layout

When calling `health_ipc_call(SP, SP+0x500)`:

| Stack Offset | Content |
|-------------|---------|
| `SP+0x00` | Switch value (5-8) |
| `SP+0x04` | Parsed command arguments (null-terminated strings) |
| `SP+0x500` | Return value from handler |

---

## 5. Version Comparison: v2.77 vs v2.78

### 5.1 Offset Deltas

| Element | v2.77 Offset | v2.78 Offset | Delta |
|---------|--------------|---------------|-------|
| Signature Bypass | `0x96EDE8` | `0x964ADC` | `-0x9A2C` |
| quit -> OCBB | `0xB80348` | `0xB73F70` | `-0xC3D8` |
| VSPR -> h | `0xB8045C` | `0xB74084` | `-0xC3D8` |
| DEBUG -> OCSD | `0xB80474` | `0xB7409C` | `-0xC3D8` |
| NULL_CMD -> FAN | `0xB804D0` | `0xB740F8` | `-0xC3D8` |
| fn_handler | `0xAFD768` | `0xAF1390` | `-0xC3D8` |

### 5.2 Key Difference

In v2.78/2.79:
- The function handler injection still works (switch values 5-8 are passed)
- The IPC call to `health_ipc_call` still executes
- **The handler pointers in the jump table are NULL or stub functions**
- HPE removed the actual fan control code

---

## 6. Command String Table

### 6.1 Command Names in v2.77

| Original Command | New Command | File Offset (v2.77) |
|-----------------|-------------|---------------------|
| quit | OCBB | `0xB80348` |
| VSPR | h | `0xB8045C` |
| DEBUG | OCSD | `0xB80474` |
| NULL_CMD | FAN | `0xB804D0` |

### 6.2 Search Pattern for Command Table

**AOB Pattern:**
```
00 00 00 00 71 75 69 74 00 00 00 00 6F 65 6D 68
```

---

## 7. Key Strings for Fan Control

Search in extracted `elf.bin`:

```bash
strings build/277_extract/elf.bin | grep -i fan
```

Expected strings in v2.77:
- `fan`
- `fan info`
- `fan temp`
- `fan speed`
- `fan start`
- `fan stop`
- `fan tach`
- `fan pwm`
- `fan pid`
- `health_ipc_call`

---

## 8. Function Handler Assembly (fn_handler.S)

Full source: `patches/277/asm/fn_handler.S`

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
    BL      0x3e420             ; health_ipc_call(SP, SP+500)
    LDR     R0, [SP, #0x500]
    LDMDB   R11, {R11, SP, PC}
```

---

## 9. Related Research Files

| File | Description |
|------|-------------|
| `research/2022-02-17-docs.md` | Jump table research (5/6/7/8 values) |
| `research/2022-02-15-initial-findings.md` | Initial firmware analysis |
| `PORTING_RESEARCH.md` | Full porting strategy document |
| `patches/277/patches.md` | v2.77 patch documentation |
| `patches/277/asm/fn_handler.S` | Function handler assembly |
| `plans/plan_copy_function_pointers.md` | Copy function pointers strategy |
| `plans/plan_reimplement_fan_control.md` | Reimplement fan control strategy |

---

## 10. Next Steps for Porting to v2.78+

### Option A: Copy Function Pointers
1. Extract v2.77 and v2.78 firmwares
2. Find the jump table in v2.77 (at ~0x00E04CB4 + load base)
3. Read the 4 handler pointers
4. Find corresponding NULL/stub pointers in v2.78
5. Copy v2.77 pointers to v2.78

### Option B: Find Dead Code in v2.78
1. Search v2.78 for fan-related strings
2. Check if any unreferenced code still exists
3. Re-enable by fixing branch targets

### Option C: Reimplement
1. Extract fan control functions from v2.77 kernel
2. Port assembly to v2.78
3. Patch the switch 6 handler to call new code

---

## 11. References

- Airbus iLO4 Toolbox: https://github.com/airbus-seclab/ilo4_toolbox
- SSTIC 2018: "Subverting your server through its BMC: the HPE iLO4 case"
- ARM Architecture Reference Manual

---

**End of Research Document**
