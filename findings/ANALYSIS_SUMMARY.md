# iLO4 v2.77 Analysis - Findings Summary

## Chunk Analysis Results

### Health Module Location
- **.health.elf.text**: Virtual Address 0x00ea1000 - 0x00f49e97 (~680KB)
- **.health.elf.data**: Virtual Address 0x00f4a000 - 0x00f4b913 (~6KB)

### Key Functions Identified

| Component | Address | Notes |
|-----------|---------|-------|
| health_ipc_call | 0x00ec2420 (offset 0x3E420) | Main IPC dispatcher |
| Jump Table | 0x00ef04b4 | Switch values 5-8 dispatch |

### Switch Handler Mapping
- **Switch 5**: Health info handler
- **Switch 6**: Fan control handler
- **Switch 7**: OCSd (on-chip sensors)
- **Switch 8**: OCBB (on-chip battery/broadband)

### IPC Struct Layout
- SP+0x0: Switch value (5-8)
- SP+0x4: Arguments
- SP+0x500: Response buffer

### Findings from Chunk Analysis

| Chunk | Address Range | Findings |
|-------|---------------|----------|
| 0227 | 0x00d8xxxx | Generic functions, no fan code |
| 0228 | 0x00eaxxxx | .health module starts here |
| 0229 | 0x00ebxxxx | Contains health_ipc_call |
| 0230-0234 | 0x00f0xxxx | Utility functions |

### Key Addresses for Fan Porting

1. **Handler injection point**: fn_handler at 0xAFD768 (userland)
2. **IPC dispatcher**: health_ipc_call at 0x3E420 (in .health)
3. **Jump table**: Switch dispatch at 0x00ef04b4

### Problem Statement

In v2.78/2.79:
- Command infrastructure remains (fan command recognized)
- Jump table pointers for switches 5-8 are NULL or stub functions
- Actual fan control code was removed

### Solution Approach

1. **Option A**: Find and copy working function pointers from 2.77 jump table to 2.78/2.79
2. **Option B**: Code hole fan code from 2.77 into 2.78/2.79 at new location
3. **Option C**: Reimplement fan handlers from scratch

## Next Steps

1. Extract actual binary strings from elf.bin_bytes
2. Locate fan command handlers in .health module
3. Compare with 2.78/2.79 to identify removed code
