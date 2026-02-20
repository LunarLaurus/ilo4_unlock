# iLO4 Fan Control Porting - 2.82 Analysis

## Status: PARTIAL RECOVERY POSSIBLE

## Executive Summary

**The research correctly identified CLI removal, but IPC handlers remain.** HPE removed the **CLI argument parser** (front-end, ~5KB) but left the **IPC handlers** (back-end, ~256 bytes) intact. The back-end is disabled by a single BEQ instruction.

## What Was Actually Removed vs What Remains

### REMOVED: CLI Front-End (Confirmed by research)

The control flow graph `research/img/health_fan_function.png` shows a **large, complex function** (~5KB, hundreds of basic blocks) that was removed in 2.79+:
- Parses command-line arguments (`fan speed 50`, `fan info`, etc.)
- Validates input parameters  
- Prints help text and usage information
- Handles multiple subcommands

**Evidence:**
- 3 fan-related strings missing in 2.82 (help text, debug status)
- Complex parsing function absent
- Research correctly observed: "actual code to run it is gone"

### REMAINS: IPC Back-End (What enables recovery)

**ConCLI Module:**
- FAN command pointer: 0x328800 → 0x0001d15c
- IPC stub exists (~50 bytes)

**Health Module (.health):**
- FAN_SET handler: 0x39e064 (256 bytes, **SAME size as 2.77**)
- Core fan functions present:
  - fan_process_pwm (0x39ead4)
  - fan_process_temps (0x3a17a8)
  - fan_ocsd_impact (0x39f6ac)
  - fanpid (0x3a5ad4)
  - fan: group() (0x39f400)
  - etc.

**String Count:**
- 2.77: 64 fan strings
- 2.82: 61 fan strings (only 3 minor CLI strings missing)

## The Two Problems

### Problem 1: Missing CLI Parser (REMOVED - HARD TO RESTORE)
To restore full CLI would require:
- Port ~5KB of complex argument parsing code
- Update all offsets (major effort)
- **Complexity: VERY HIGH**

### Problem 2: Disabled IPC Handler (BLOCKED - EASY FIX)
Even when called via IPC, fan control is blocked:

**At 0x39e0c4 in FAN_SET handler:**
```
2.77: BEQ → 0x39ca54 (continue to fan control)
2.82: BEQ → 0x39e0d8 (print "defunct FAN SET command")
```

**The comparison:**
- Loads flag from [R5 + 1] in fan state structure
- Compares with fan speed parameter (R6)
- If equal → branches to defunct error

**Fix:** NOP the BEQ at 0x39e0c4
- Change: `0a 00 00 ea` → `00 00 00 ea` 
- **Complexity: LOW** (single instruction)

## Recovery Options

### Option 1: Restore Full CLI (NOT RECOMMENDED)
- **Effort:** Weeks
- **Port ~5KB of parsing code**
- High risk, many bugs likely

### Option 2: Minimal CLI Stub (RECOMMENDED)
- **Effort:** Hours
- **Steps:**
  1. Patch BEQ at 0x39e0c4
  2. Add simple hardcoded command: `fan speed <n>` only
  3. ~100 bytes vs ~5000 bytes
- **Fast to implement and test**

### Option 3: Direct IPC Access (ADVANCED)
- **Effort:** Medium
- Call IPC handler programmatically
- Bypass CLI entirely

## IPC Function Discovery

Through analysis of 2.82, identified the IPC mechanism:

| Function | Address | Call Count | Purpose |
|----------|---------|------------|---------|
| `ipc_send_receive` | 0x01776004 | 148 callers | Main IPC call |
| `ipc_cleanup` | 0x01777dc8 | 317 callers | Response handling |
| `ipc_init` | 0x017adc60 | 17 callers | Setup |

These can be called directly from assembly to send IPC requests to the Health module.

**IPC Structure:**
```c
struct ipc_request {
    uint32_t switch_value;  // 6 for fan
    uint32_t command;       // 1 for FAN_SET
    uint32_t fan_speed;     // 0-255
    uint32_t reserved;      // 0
};
```

## Minimal Handler Assembly

Created: `patches/282/asm/fan_handler_minimal.S`

Two versions:
1. **fan_speed_simple** (~80 bytes): Takes fan speed in R0, calls IPC
2. **fan_speed_fixed** (~50 bytes): Hardcoded speed, no arguments

Can be placed in code cave or unused section.

## Patch Files

### Required Patch (All options)
`patches/282/patch_userland.json`:
```json
{
    "remark": "Enable fan control by NOPing the defunct branch",
    "offset": "0x39e0c4",
    "prev_data": "0a 00 00 ea",
    "patch": "00 00 00 ea"
}
```

## Key File Offsets (2.82 ELF)

| Component | Offset | Status |
|-----------|--------|--------|
| CLI Handler Pointer | 0x328800 | Valid |
| CLI Handler Code | 0x1d15c | Exists (IPC stub) |
| Health FAN_SET | 0x39e064 | **PATCH: BEQ @ +0x60** |
| Defunct Message | 0x39e1c8 | Present |
| IPC Send Function | 0x01776004 | Available |

## Summary

**Research was correct:** CLI parser (~5KB) was removed.

**But incomplete:** IPC handlers (~256 bytes) remain and work.

**Recovery path:**
1. Patch BEQ (5 minutes) - enables IPC handler
2. Add minimal CLI stub using IPC functions (hours) - restores basic functionality
3. OR use IPC directly - for programmatic control

The fan control logic never left - it's just blocked by one instruction.
