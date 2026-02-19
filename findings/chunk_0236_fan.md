# Fan Control Research Findings - chunk_0236_00470000

**Research Date:** 2026-02-19  
**Target File:** chunk_0236_00470000  
**Status:** FILE NOT FOUND

---

## 1. File Availability

### Requested File
- **Path:** `ilosrc/chunk_0236_00470000/chunk_0236_00470000.xml`
- **Status:** DOES NOT EXIST

### Available Alternative
- **Path:** `ilosrc/chunk_0236_00472000/chunk_0236_00472000.xml`
- **Status:** EXISTS (analyzed below)

---

## 2. Search Results Summary

### Patterns Searched
| Pattern | Matches Found |
|---------|--------------|
| `fan` / `FAN` | 0 |
| `pwm` / `PWM` | 0 |
| `tach` / `TACH` | 0 |
| `temp` / `TEMP` | 0 |

### Analysis of chunk_0236_00472000

The file contains functions in the address range `0108a5b0` - `01092128` (virtual addresses within .health.elf.text module). This chunk does NOT contain explicit fan control code strings.

---

## 3. Existing Fan Control Research

Extensive fan control research already exists in this project. Refer to:

### Key Documents
| Document | Path | Description |
|----------|------|-------------|
| Fan Code Locations | `plans/research_fan_code_locations.md` | Comprehensive fan control addresses |
| Fan Control Plan | `plans/plan_reimplement_fan_control.md` | Reimplementation strategy |
| Fan Research ASM | `util/asm/fan_research.S` | Assembly research code |

---

## 4. Known Fan Control Addresses (from existing research)

### IPC Handler
| Component | Address/Offset | Notes |
|-----------|---------------|-------|
| health_ipc_call | `0x3E420` | Main IPC dispatcher |
| Switch 6 Handler | (in jump table) | Fan control handler |

### Module Locations (.health module)
| Section | Virtual Address | Size |
|---------|----------------|------|
| .health.elf.text | `0x00ea8000` | `0x000a7e78` |
| .health.elf.data | `0x00f50000` | `0x00001914` |
| health_device_readings | `0x01063000` | `0x00002000` |

### Jump Table (v2.73 reference)
| Offset | Handler |
|--------|---------|
| +0x00 | Switch 5 (health) |
| +0x04 | Switch 6 (fan) |
| +0x08 | Switch 7 (ocsd) |
| +0x0C | Switch 8 (ocbb) |

**Jump Table Location:** `.health.elf.text:00E04CB4`

---

## 5. Expected Fan Command Strings

Based on existing research, the following strings should exist in firmware:

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

---

## 6. Recommendations

1. **File Not Found**: The chunk_0236_00470000 file does not exist. The analysis should use chunk_0236_00472000 or search the full XML dataset.

2. **String Search**: Use `strings` command on extracted `elf.bin` to find fan-related strings, then cross-reference with XML chunks.

3. **Version Comparison**: The fan control code was removed in v2.78+. See `plans/research_fan_code_locations.md` for porting strategies.

---

## 7. Related Files in Project

```
plans/research_fan_code_locations.md    - Main fan research document
plans/plan_reimplement_fan_control.md   - Reimplementation plan
util/asm/fan_research.S                - Research assembly code
patches/277/asm/fn_handler.S            - Handler patch assembly
research/img/health_fan_function.png   - Fan function screenshot
```

---

**End of Findings**
