# Research Findings: chunk_0233_00466000.xml

## File Information
- **Requested File**: `chunk_0233_00466000.xml`
- **Actual File**: `ilosrc/chunk_0233_00466000/chunk_0233_00466000.xml`
- **Chunk ID**: 233
- **Address Range in File**: `0x00f2b6dc` - `0x00f321d8` (functions in this chunk)
- **Memory Region**: `.health.elf.text` (0x00ea1000 - 0x00f49e97)

---

## Search Results

### 1. Dispatcher/Switch Handler Functions

**STATUS: NOT FOUND in this chunk**

The XML file contains only function **metadata** (entry points, addresses, parameter signatures, stack frames) from IDA/Ghidra. The actual switch/case code is not present in the XML format - it's decompiler metadata only.

However, the **actual IPC dispatcher** is known from research:

| Function | Offset | Virtual Address | Description |
|----------|--------|-----------------|-------------|
| `health_ipc_call` | `0x3E420` | `0x00ec2420` | Main IPC dispatcher for health module |

---

### 2. Switch Values 5, 6, 7, 8

**Found in existing research documents:**

The switch values 5-8 are mapped to specific handlers in the `.health` module:

| Switch Value | Handler | Description |
|--------------|---------|-------------|
| 5 | health | Health monitoring |
| 6 | fan | Fan control |
| 7 | ocsd | OCS daemon |
| 8 | ocbb | OCBB (Onboard Certificate Bar) |

**Jump Table Location**: `.health.elf.text:0x00E04CB4`

---

### 3. IPC Communication Functions

**Located elsewhere (chunk_0229)**

The IPC communication system is handled by:

| Component | Address | Notes |
|-----------|---------|-------|
| `health_ipc_call` | `0x00ec2420` | Main IPC dispatcher |
| Jump Table | `0x00e04cb4` | 4 entries for switches 5-8 |

**IPC Struct Layout** (when calling `health_ipc_call(SP, SP+0x500)`):
- `SP+0x0`: Switch value (controls routing)
- `SP+0x4`: Arguments
- `SP+0x500`: Response buffer

---

### 4. Jump Table Patterns

**Jump table structure (from research):**

```
Offset +0x00: Handler for switch 5 (health)
Offset +0x04: Handler for switch 6 (fan)
Offset +0x08: Handler for switch 7 (ocsd)
Offset +0x0C: Handler for switch 8 (ocbb)
```

---

## Functions in This Chunk (0x00f2bxxx range)

This chunk contains 139 functions in the `.health` module text section:

| Address Range | Function Count | Notable Functions |
|---------------|----------------|-------------------|
| 0x00f2b6dc - 0x00f2b767 | 4 | Small utility functions |
| 0x00f2b768 - 0x00f2b833 | 6 | Parameter handling functions |
| 0x00f2b834 - 0x00f2b97f | 4 | Data processing functions |
| 0x00f2b9e8 - 0x00f2c02c | 15 | Mixed utility functions |
| 0x00f2c214 - 0x00f2c667 | 8 | Larger functions with stack frames |
| 0x00f2c668 - 0x00f2c837 | 3 | Data handling |
| 0x00f2d004 - 0x00f2d9e4 | 6 | Complex functions (0x1f90+ stack) |
| 0x00f2dda0 - 0x00f2e3eb | 8 | Large functions |
| 0x00f2e5e4 - 0x00f2f613 | 6 | Complex functions |
| 0x00xf2918 - 0x00xf3510 | ~25 | Various handlers |

---

## Summary

This chunk (0233_00466000) contains **function metadata only** - no actual switch/case code is present in the XML. The IPC dispatcher and jump table are located in:

1. **Chunk 0229**: Contains the `.health.elf.text` module with:
   - `health_ipc_call` at offset `0x3E420` (virtual address 0x00ec2420)
   - Jump table at `0x00e04cb4`

2. **Module**: `.health` (health monitoring and fan control)

The chunk 0233 functions are in the 0x00f2bxxx range which is near the end of the `.health.elf.text` section (ending at 0x00f49e97).

---

## References

- `findings/chunk_0229_fan.md` - Contains detailed IPC handler analysis
- `findings/chunk_0235_health.md` - Similar chunk analysis
- `plans/plan_reimplement_fan_control.md` - Fan control research plan
- `research/2022-02-17-docs.md` - Documents the jump table with values 5/6/7/8

---

*Generated: Research analysis of chunk_0233_00466000*
