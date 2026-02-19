# Firmware Jump Table Comparison

## Key Finding

**All fan control strings are present in ALL versions including 2.82!**

This means the fan control CODE may still exist - it's just not being called.

## String Locations

| String | 2.77 | 2.78 | 2.79 | 2.82 |
|--------|------|------|------|-------|
| FAN | 0xae738 | 0xae868 | 0xae868 | 0xae970 |
| OCBB | 0x3daccd | 0x3d0abd | 0x3d0abd | 0x3d53fd |
| fan: dispatcher | 0x39c68c | 0x399590 | 0x399590 | 0x39dd10 |
| fan: FAN_SET | 0x39cae0 | 0x3999e4 | 0x3999e4 | 0x39e164 |
| temperature | 0x386b16 | 0x383a1a | 0x383a1a | 0x387ff2 |
| pwm | 0x389dc6 | 0x386cca | 0x386cca | 0x38b2a2 |

## Analysis

1. **2.77**: Working fan control - all strings and code present
2. **2.78**: All strings present at shifted offsets - CODE LIKELY PRESENT
3. **2.79**: Same as 2.78 - CODE LIKELY PRESENT  
4. **2.82**: All strings present - CODE LIKELY PRESENT

## Next Steps

The jump table that routes IPC switch value 6 to the fan handler needs to be found and patched.

The handler is likely still present - we just need to find where the IPC dispatch routes to it and ensure the pointer is valid.

## Command Table Offsets (from patches)

| Command | 2.77 Offset | 2.78 Offset | Delta |
|---------|-------------|-------------|-------|
| NULL_CMD->FAN | 0xB804D0 | 0xB740F8 | -C3D8 |
| fn_handler | 0xAFD768 | 0xAF1390 | -C3D8 |
