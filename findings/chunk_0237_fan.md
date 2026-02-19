# Research Findings: chunk_0237_00472000

## File Status: NOT FOUND

**Requested File**: `ilosrc/chunk_0237_00472000/chunk_0237_00472000.xml`  
**Status**: Does NOT exist in the repository

### Available Nearby Chunks

| Chunk | Status | Path |
|-------|--------|------|
| chunk_0236_00472000 | EXISTS | `ilosrc/chunk_0236_00472000/chunk_0236_00472000.xml` |
| chunk_0237_00474000 | EXISTS | `ilosrc/chunk_0237_00474000/chunk_0237_00474000.xml` |

### Search Results for chunk_0237_00474000

**Search Criteria**:
1. Functions with "fan" in name or references
2. PWM control code
3. Temperature sensor handling
4. Functions with "tach" or "temp" in references

**Result**: No fan, PWM, tach, or temp references found in chunk_0237_00474000.xml

---

## Comprehensive Fan Control Research Summary

Based on existing research documents in this project:

### Key Addresses - Fan Control System (v2.77)

| Component | Address/Offset | Description |
|----------|---------------|-------------|
| health_ipc_call | `0x3E420` | Main IPC dispatcher for switch values 5-8 |
| health_ipc_call (VA) | `0x00ec2420` | Virtual address in .health module |
| Jump Table | `.health.elf.text:00E04CB4` | Switch dispatch table |
| fn_handler (v2.77) | `0xAFD768` | Patched entry point |
| fn_handler (v2.78) | `0xAF1390` | v2.78 entry point |

### Switch Values

| Switch | Command | Function |
|--------|---------|----------|
| 5 | `h` | Health info |
| 6 | `fan` | **Fan control** |
| 7 | `ocsd` | On-chip sensors |
| 8 | `ocbb` | On-chip battery/broadband |

### .health Module Memory Layout

| Section | Virtual Address | Size |
|---------|----------------|------|
| `.health.elf.text` | `0x00ea8000` | `0x000a7e78` |
| `.health.elf.data` | `0x00f50000` | `0x00001914` |
| `health_device_readings` | `0x01063000` | `0x00002000` |

### Fan Command Strings (v2.77)

```
fan
fan info
fan temp
fan speed
fan start
fan stop
fan tach
fan pwm
fan pid
health_ipc_call
```

### Version Differences

**v2.77**: Fully functional fan control via switch values 5-8  
**v2.78/2.79**: HPE removed the actual fan control code but left command infrastructure intact

| Element | v2.77 Offset | v2.78 Offset | Delta |
|---------|--------------|---------------|-------|
| fn_handler | `0xAFD768` | `0xAF1390` | `-0xC3D8` |

---

## Functions Analyzed

### chunk_0237_00474000.xml Functions

This chunk contains 60+ functions with generic IDA Pro naming:

| Entry Point | Function Name |
|-------------|---------------|
| 010f7288 | FUN_010f7288 |
| 010f72d4 | FUN_010f72d4 |
| 010f75c8 | FUN_010f75c8 |
| 010f7658 | FUN_010f7658 |
| 010f7680 | FUN_010f7680 (large, multi-range) |
| 010f8e00 | FUN_010f8e00 |
| 010f8f40 | FUN_010f8f40 |
| 010f9328 | FUN_010f9328 |
| 010f9530 | FUN_010f9530 |
| 010f95d0 | FUN_010f95d0 |
| 010f993c | FUN_010f993c |
| 010f9c90 | FUN_010f9c90 |
| 010fa570 | FUN_010fa570 |
| 010fa9b0 | FUN_010fa9b0 |
| 010fabe4 | FUN_010fabe4 |
| 010fac2c | FUN_010fac2c |
| 010fad6c | FUN_010fad6c |
| 010fb26c | FUN_010fb26c |
| 010fb420 | FUN_010fb420 |
| 010fb998 | FUN_010fb998 |
| 010fba78 | FUN_010fba78 |
| 010fbe50 | FUN_010fbe50 |
| 010fbe84 | FUN_010fbe84 |
| 010fbf1c | FUN_010fbf1c |
| 010fbffc | FUN_010fbffc |
| 010fc444 | FUN_010fc444 |
| 010fd014 | FUN_010fd014 |
| 010fd378 | FUN_010fd378 |
| 010fd594 | FUN_010fd594 |
| 010fd5e4 | FUN_010fd5e4 |
| 010fd6c0 | FUN_010fd6c0 |
| 010fd6dc | FUN_010fd6dc |
| 010fd7c0 | FUN_010fd7c0 |
| 010fd80c | FUN_010fd80c |
| 010fd9e0 | FUN_010fd9e0 |
| 010fdbb4 | FUN_010fdbb4 |
| 010fe354 | FUN_010fe354 |
| 010fe3d4 | FUN_010fe3d4 |
| 010fec98 | FUN_010fec98 |
| 010ff54c | FUN_010ff54c |
| 010ff724 | FUN_010ff724 |
| 010ffc50 | FUN_010ffc50 |
| 010ffe14 | FUN_010ffe14 (very large) |
| 01100850 | FUN_01100850 |
| 011009c8 | FUN_011009c8 |
| 01100b74 | FUN_01100b74 |
| 01100f18 | FUN_01100f18 |
| 01101138 | FUN_01101138 |

---

## Conclusions

1. **chunk_0237_00472000 does not exist** - The requested file was not found in the repository

2. **No fan-related code in chunk_0237_00474000** - This chunk contains general-purpose functions without fan/PWM/tach references

3. **Fan control is in the .health module** - The actual fan control code is in the `.health.elf.text` section with handlers accessed via IPC switch value 6

4. **Fan control was removed in v2.78+** - HPE removed the underlying fan control code while keeping the command infrastructure

---

## References

- `plans/research_fan_code_locations.md` - Comprehensive fan control addresses
- `plans/plan_reimplement_fan_control.md` - Reimplementation strategy
- `plans/plan_copy_function_pointers.md` - Function pointer porting approach
- `findings/chunk_0229_fan.md` - Previous chunk analysis in .health module

---

*Generated: 2026-02-19*
*Research only - No modifications made*
