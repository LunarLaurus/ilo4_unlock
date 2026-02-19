# Research Findings: chunk_0235_00470000.xml

## File Information
- **Requested File**: `chunk_0235_0046a000.xml` (NOT FOUND)
- **Actual File**: `ilosrc/chunk_0235_00470000/chunk_0235_00470000.xml`
- **Chunk ID**: 235
- **Address Range**: `0x0106f518` - `0x010xxxxx` (flash memory mapping)

---

## Search Results

### 1. Requested File Status
**STATUS: FILE NOT FOUND**

The file `chunk_0235_0046a000` does not exist in the repository. Only `chunk_0235_00470000` exists.

---

### 2. Dispatcher/Switch Handler Functions

**No dispatcher or switch handlers found in chunk_0235_00470000**

The functions in this chunk use generic IDA Pro naming conventions (`FUN_XXXXXXXX`) and do not contain explicit switch/case statements in the XML metadata.

However, the **actual IPC dispatcher** is located elsewhere:

| Function | Offset | Virtual Address | Description |
|----------|--------|-----------------|-------------|
| `health_ipc_call` | `0x3E420` | `0x00ec2420` | Main IPC dispatcher for health module |

---

### 3. Switch Values 5, 6, 7, 8

**Found in existing research documents:**

The switch values 5-8 are mapped to specific handlers in the `.health` module:

| Switch Value | Handler | Description |
|--------------|---------|-------------|
| 5 | health | Health monitoring |
| 6 | fan | Fan control |
| 7 | ocsd | OCS daemon |
| 8 | ocbb | OCBB (Onboard Certificate Bar) |

**Jump Table Location**: `.health.elf.text:00E04CB4`

---

### 4. IPC Communication Functions

**Located in chunk_0229 (not chunk_0235)**

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

### 5. Jump Table Patterns

**Jump table found in existing research:**

```
Offset +0x00: Handler for switch 5 (health)
Offset +0x04: Handler for switch 6 (fan)
Offset +0x08: Handler for switch 7 (ocsd)
Offset +0x0C: Handler for switch 8 (ocbb)
```

---

## Summary

This chunk (0235_00470000) does **not** contain the IPC dispatcher or switch handler code. Those components are located in:

1. **Chunk 0229**: Contains the `.health.elf.text` module with:
   - `health_ipc_call` at offset `0x3E420`
   - Jump table at `0x00e04cb4`

2. **Module**: `.health` (health monitoring and fan control)

The chunk 0235 appears to contain general utility functions without explicit switch handling or IPC-related code in the XML metadata.

---

## References

- `findings/chunk_0229_fan.md` - Contains detailed IPC handler analysis
- `plans/research_fan_code_locations.md` - Fan control research
- `plans/research_code_extraction_methodology.md` - Code extraction methodology

---

*Generated: Research analysis of chunk_0235_00470000*
