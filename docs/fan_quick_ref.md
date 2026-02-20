# Fan Control Quick Reference Card

## v2.77 -> v2.78+ Porting

### The Problem
HPE completely removed fan control from v2.78+. No IPMI interface remains.

### The Solution  
~25 KB of assembly code needs to be ported from v2.77.

---

## Key Addresses (v2.77)

| Component | VA | Size |
|-----------|-----|------|
| Dispatcher | 0x00ec3d48 | 1.3 KB |
| FAN_SET | 0x00ec4278 | 2.4 KB |
| PWM Control | 0x00ec4be8 | 11.5 KB |
| Temp Control | 0x00ec78dc | 4.4 KB |
| OCSD | 0x00ec8b48 | 4.6 KB |
| PID | 0x00ed00f8 | 1.0 KB |

---

## Version Delta
- General: -0xC3D8
- Fan code: Verify per-function

---

## Files Created
- `docs/fan_code_reference.md` - Full technical reference
- `docs/fan_porting_guide.md` - Porting steps

---

## Recommendation
**Stay on v2.77** - Working patches, proven stable.
