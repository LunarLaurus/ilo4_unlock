# iLO4 Fan Control Porting Guide: v2.77 to v2.78+

## Overview

This document provides a technical guide for porting fan control functionality from iLO4 v2.77 to v2.78+.

**Critical Finding**: HPE completely removed all fan control code from v2.78+. The strings remain but are unreferenced. Porting requires copying ~25KB of assembly code from v2.77.

---

## Quick Reference

### Code Size Summary
| Component | Size |
|-----------|------|
| Dispatcher | 1.3 KB |
| FAN_SET handler | 2.4 KB |
| PWM Control | 11.5 KB |
| Temperature | 4.4 KB |
| OCSD | 4.6 KB |
| PID | 1.0 KB |
| **TOTAL** | **~25 KB** |

### Key Addresses (v2.77)
| Function | VA |
|----------|-----|
| Fan dispatcher | 0x00ec3d48 |
| FAN_SET | 0x00ec4278 |
| PWM control | 0x00ec4be8 |
| Temperature | 0x00ec78dc |
| PID | 0x00ed00f8 |

---

## Porting Steps

### Step 1: Extract Fan Code from v2.77

The fan code is in the .health.elf.text section:

```
Base: 0x00ea1000
File offset: 0x358f4c
Size: 0xa8e98
```

Extract bytes from offset 0x0037bc94 to 0x00388044 (approximately)

### Step 2: Translate Addresses

Version delta for most functions: **-0xC3D8**

However, the .health module may have shifted differently. Verify by:
1. Finding the health_ipc_call function
2. Checking string references

### Step 3: Fix Absolute References

Scan for hardcoded addresses in the extracted code:
- String pointers
- Function pointers
- Table references
- Jump table entries

### Step 4: Re-create Hooks

The fan CLI is accessed via:
- IPC switch value: 6
- Jump table at: .health.elf.text + offset (find via "fan: dispatcher" string)

Patch the handler for switch 6 to point to ported code.

---

## Code Regions to Port

### Region 1: Dispatcher (0x00ec3d48 - 0x00ec4300)
**Size**: ~1.3 KB
**Purpose**: Routes fan commands to sub-handlers

Functions:
- Main dispatcher entry
- FAN_SET handler
- Command validation

### Region 2: PWM Control (0x00ec4be8 - 0x00ec78dc)  
**Size**: ~11.5 KB
**Purpose**: PWM calculation and application

Functions:
- fan_process_pwm
- PWM force min/max/zero
- PWM locking mechanisms
- External adjustment handling

### Region 3: Temperature Control (0x00ec78dc - 0x00ec8a00)
**Size**: ~4.4 KB
**Purpose**: Temperature-based fan speed

Functions:
- fan_process_temps
- Zone blowout control
- OCSD sensor processing

### Region 4: OCSD (0x00ec8a00 - 0x00ec9c00)
**Size**: ~4.6 KB
**Purpose**: Optimal Cooling System Diagnostics

Functions:
- fan_ocsd_impact
- do_ocsd_associations
- fan_set_OCSD_sensor_ACR

### Region 5: PID Controller (0x00ed00f8 - 0x00ed0500)
**Size**: ~1.0 KB
**Purpose**: Proportional-Integral-Derivative control

Functions:
- fanpid calculation
- Setpoint adjustment

### Region 6: Support Functions

| Address | Function |
|---------|----------|
| 0x00ec9cac | fan_rundown (cleanup) |
| 0x00ec9870 | Monitor start/stop |
| 0x00eab558 | Redundancy handling |

---

## Dependencies

### Semaphores
- `fan_sem` - Fan register access protection
- `platdef_access_sem` - Platform definition access

### I2C Bus
The fan hardware is controlled via I2C. The code uses:
- I2C read/write functions
- Fan controller chip registers
- PWM duty cycle mapping

### Sensor Infrastructure
- Temperature sensors
- Tachometer inputs
- OCSD sensors

---

## Testing Checklist

### Pre-Port Testing (v2.77 baseline)
- [ ] Document current fan behavior
- [ ] Record PWM values at various temperatures
- [ ] Test all fan commands

### Post-Port Testing (v2.78+)
- [ ] Verify fan commands respond
- [ ] Test temperature-based control
- [ ] Verify redundancy handling
- [ ] Test PWM control
- [ ] Monitor thermal limits

### Safety Tests
- [ ] Run with elevated server temperature
- [ ] Test fan failure scenarios
- [ ] Verify redundancy transitions
- [ ] Check watchdog timeout behavior

---

## Alternative: Stay on v2.77

Given the complexity of porting ~25KB of assembly, consider:

1. **Remain on v2.77** - Working patches exist
2. **Use v2.78+ without fan control** - No fan CLI but system remains stable
3. **Hybrid approach** - Keep v2.77 for fan control, upgrade other components

---

## References

- `plans/plan_fan_investigation.md` - Investigation findings
- `findings/fan_function_addresses.md` - Address mapping
- `docs/fan_code_reference.md` - Complete technical reference

---

*Document Version: 1.0*
*Created: 2026-02-19*
