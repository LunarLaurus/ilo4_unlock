# iLO4 Fan Control Investigation Plan

## Executive Summary

This document tracks the investigation into restoring fan control functionality to iLO4 v2.78+. 

**CRITICAL FINDING**: HPE completely removed all fan control code from v2.78+. There is no IPMI interface left to exploit - the entire subsystem was deleted.

---

## Current State

| Version | Status | Fan Control |
|---------|--------|-------------|
| 2.77 | Working with patches | **Functional** |
| 2.78 | Patched | **REMOVED - COMPLETELY DELETED** |
| 2.79 | Latest | **REMOVED - COMPLETELY DELETED** |

### v2.78 Analysis Results

| String | v2.77 | v2.78 | Status |
|--------|-------|-------|--------|
| EH_INTF_TYPE_FAN | 3 | 0 | DELETED |
| fan: dispatcher | 1 | 0 | DELETED |
| fan_process_pwm | 1 | 0 | DELETED |
| fan_process_temp | 2 | 0 | DELETED |
| smifpkt blowout | 1 | 0 | DELETED |
| PlatDef | 278 | ~10 | GUTTED |

---

## Investigation Checklist

### Phase 1: Code Location Analysis

| # | Task | Target | Status | Notes |
|---|------|--------|--------|-------|
| 1.1 | Locate fan dispatcher | 0x00ec3d48 | **COMPLETE** | String: "fan: dispatcher: error" |
| 1.2 | Locate PWM control | 0x00ec4be8 | **COMPLETE** | String: "fan_process_pwm" |
| 1.3 | Locate temperature control | 0x00ec78dc | **COMPLETE** | String: "fan_process_temps" |
| 1.4 | Locate PID controller | 0x00ed00f8 | **COMPLETE** | String: "fanpid: drive limited" |
| 1.5 | Locate blowout trigger | 0x00ec4c58 | **COMPLETE** | String: "setting fans to blowout" |
| 1.6 | Locate OCSD associations | 0x00ec8b48 | **COMPLETE** | String: "do_ocsd_associations" |

### Phase 2: Code Structure Analysis

| # | Task | Target | Status | Notes |
|---|------|--------|--------|-------|
| 2.1 | Find code blocks for dispatcher | chunk_0004 | **COMPLETE** | 0x00ec3xxx - gap in function defs |
| 2.2 | Find code blocks for PWM | chunk_0004 | **COMPLETE** | 0x00ec4970-0x00ec4bcb |
| 2.3 | Find code blocks for temps | chunk_0004 | **COMPLETE** | 0x00ec74e0-0x00ec786b |
| 2.4 | Find code blocks for PID | chunk_0004 | **COMPLETE** | 0x00ecfd9c-0x00ed00ef |
| 2.5 | Map string data locations | chunk_0044 | **COMPLETE** | All fan strings defined here |
| 2.6 | Verify v2.78 code removal | binaries | **COMPLETE** | CONFIRMED: All fan code deleted |

### Phase 3: v2.78 Analysis

| # | Task | Status | Result |
|---|------|--------|--------|
| 3.1 | Search v2.78 for IPMI interface | **COMPLETE** | NOT FOUND |
| 3.2 | Search v2.78 for fan strings | **COMPLETE** | Only fragmented remnants |
| 3.3 | Verify code removal | **COMPLETE** | COMPLETELY REMOVED |

### Phase 4: Documentation

| # | Task | Status | Output |
|---|------|--------|--------|
| 4.1 | Create technical reference | **COMPLETE** | docs/fan_code_reference.md |
| 4.2 | Create porting guide | **COMPLETE** | docs/fan_porting_guide.md |
| 4.3 | Document IPMI discovery | **COMPLETE** | Documented (but unusable) |

---

## Key Findings Summary

### Code to Port: ~25 KB

| Component | Size | VA Range |
|-----------|------|----------|
| Dispatcher | 1.3 KB | 0x00ec3d48-0x00ec4278 |
| FAN_SET | 2.4 KB | 0x00ec4278-0x00ec4be8 |
| PWM Control | 11.5 KB | 0x00ec4be8-0x00ec78dc |
| Temperature | 4.4 KB | 0x00ec78dc-0x00ec8a00 |
| OCSD | 4.6 KB | 0x00ec8a00-0x00ec9c00 |
| PID | 1.0 KB | 0x00ed00f8-0x00ed0500 |

### Recommended Path Forward

1. **STAY ON v2.77** - Working patches exist
2. **Port code to v2.78** - Requires ~25KB assembly port
3. **New implementation** - Write custom handler

---

## Deliverables Created

| File | Description |
|------|-------------|
| `docs/fan_code_reference.md` | Complete technical reference (~600 lines) |
| `docs/fan_porting_guide.md` | Porting guide with steps (~150 lines) |

---

*Document updated: 2026-02-19*
*Status: Investigation Complete - Porting Required*

### Phase 4: Hardware Interface Analysis

| # | Task | VA | Status | Notes |
|---|------|--------|--------|-------|
| 4.1 | Find platdef table format | 0x00eb16c8 | **FOUND** | "Fan table primitive convert" |
| 4.2 | Locate I2C bus code | 0x00fbd9f0 | **FOUND** | "Hardware I2C access blocked" |
| 4.3 | Identify fan controller chip | TBD | **PENDING** | Likely SMSC/EC |
| 4.4 | Find blowout mode trigger | 0x00fbd9c9 | **FOUND** | smifpkt_008c_dev_blowout_fans |

### Phase 5: IPMI Interface Discovery (NEW - HIGH PRIORITY)

| # | Discovery | VA | Status | Notes |
|---|-----------|-----|--------|-------|
| 5.1 | Fan GET interface | 0x00ebaeb9 | **FOUND** | EH_INTF_TYPE_FAN_GET |
| 5.2 | Fan SET interface | 0x00ebb0a1 | **FOUND** | EH_INTF_TYPE_FAN_SET |
| 5.3 | Fan DO NOT USE | 0x00ebb0bd | **FOUND** | EH_INTF_TYPE_FAN_DO_NOT_USE |
| 5.4 | Host blowout cmd | 0x00fbd9c9 | **FOUND** | smifpkt_008c_dev_blowout_fans |
| 5.5 | Host resume cmd | TBD | **FOUND** | smifpkt_008c_dev_resume_fans |
| 5.6 | Fan SDR generation | 0x014eba62 | **FOUND** | bmc_sen_gen_fan (hidden from IPMI) |

### Phase 6: Implementation Options

| # | Approach | Description | Complexity |
|---|----------|-------------|------------|
| A | Reimplement CLI | Port v2.77 fan code to v2.78+ | Very High |
| B | IPMI Direct | Call EH_INTF_TYPE_FAN_SET directly | High |
| C | SMIF Host | Use host->iLO protocol for blowout | Medium |
| D | Hybrid | Combine approaches for maximum control | High |

---

## Key Addresses Reference

### Fan Function Code Blocks (from chunk_0004)

| VA Range | Size | Likely Function | String Reference |
|----------|------|----------------|------------------|
| 0x00ec3c14-0x00ec40f3 | ~4KB | [GAP] | Dispatcher area |
| 0x00ec418c-0x00ec4277 | 0xEB | FAN_SET handler | "fan: FAN_SET" @ 0x00ec4278 |
| 0x00ec4970-0x00ec4bcb | ~0x2FB | PWM control | "fan_process_pwm" @ 0x00ec4be8 |
| 0x00ec74e0-0x00ec786b | ~0x38B | Temp control | "fan_process_temps" @ 0x00ec78dc |
| 0x00ec795c-0x00ec7da7 | ~0x44B | Temp errors | "activating blowout" @ 0x00ec7e50 |
| 0x00ec8b90-0x00ec8eef | ~0x35F | OCSD | "do_ocsd_associations" @ 0x00ec8b48 |
| 0x00ecfd9c-0x00ed00ef | ~0x353 | PID | "fanpid" @ 0x00ed00f8 |

### IPMI/Health Interface (NEW DISCOVERY)

| VA | Function | Description |
|----|----------|-------------|
| 0x00ebaeb9 | EH_INTF_TYPE_FAN_GET | IPMI fan status reading |
| 0x00ebb0a1 | EH_INTF_TYPE_FAN_SET | IPMI fan speed control |
| 0x00ebb0bd | EH_INTF_TYPE_FAN_SET | Extended fan control |
| 0x00eb16c8 | fan_table_primitive_convert | Fan table mapping |
| 0x00eb1a78 | fan_table_mask_convert | PWM mask conversion |
| 0x00eb1af4 | fan_table_pwm_convert | PWM offset conversion |

### Host-iLO Communication (SMIF)

| VA | Function | Description |
|----|----------|-------------|
| 0x00fbd9c9 | smifpkt_008c_dev_blowout_fans | Host triggers max fan |
| 0x00fbd9f0 | I2C access handler | Hardware I2C blocked message |
| 0x00fbd964 | blowout notification | "Fan speed temporarily increased" |

### SDR Sensor Generation

| VA | Function | Description |
|----|----------|-------------|
| 0x014eba62 | bmc_sen_gen_fan | Hidden from IPMI |
| 0x014ebaa8 | bmc_sen_gen_fan_hp | Fan with tach/counter |
| 0x014ebf0c | bmc_sen_gen_fan_duty_cycle | PWM duty cycle |
| 0x014ec764 | bmc_sen_gen_fan_presence | Fan presence detection |

---

## BREAKTHROUGH: IPMI Interface Could Bypass CLI

The discovery of `EH_INTF_TYPE_FAN_SET` and `EH_INTF_TYPE_FAN_GET` at the firmware level is significant:

1. **This is NOT the CLI** - It's the internal IPMI interface that the CLI calls
2. **Still exists in v2.78+?** - Need to verify if these functions remain
3. **Direct access path** - If these entry points still work, we can bypass the removed CLI entirely

## CRITICAL FINDING: v2.78 Analysis

**Analyzed v2.78 firmware (ilo4_278.bin):**

| String | v2.77 | v2.78 |
|--------|-------|-------|
| EH_INTF_TYPE_FAN | 3 | **0** |
| fan: dispatcher | 1 | **0** |
| fan_process_pwm | 1 | **0** |
| fan_process_temp | 2 | **0** |
| smifpkt_008c_dev_blowout | 1 | **0** |
| fanpid: | 2 | **0** |
| PlatDef | 278 | **~10 (fragmented)** |

**CONCLUSION**: HPE completely removed ALL fan control code from v2.78+. There are no IPMI interfaces left to exploit - the entire subsystem was deleted.

---

## Potential Recovery Options

| # | Approach | Feasibility | Notes |
|---|----------|-------------|-------|
| 1 | Copy v2.77 code to v2.78 | **HIGH** | Port ~50KB of assembly |
| 2 | Reimplement from scratch | MEDIUM | New code, no IPMI hooks |
| 3 | Use v2.77 firmware | **RECOMMENDED** | Stay on v2.77 with working patch |

---

## Next Steps

1. **Verify IPMI presence in v2.78+**: Search for EH_INTF strings in v2.78 firmware
2. **Map function pointers**: Find the actual function addresses for FAN_SET/GET
3. **Test approach**: Determine which interface is most viable
4. **Implement**: Write custom handler using discovered interfaces

### String Data Locations (from chunk_0044)

| VA | String |
|----|--------|
| 0x00ec3d48 | "fan: dispatcher: error" |
| 0x00ec3de4 | "fan_register_clear: releasing semaphore" |
| 0x00ec4278 | "fan: FAN_SET: %u, %u" |
| 0x00ec42e4 | "fan: dispatch(): invalid command" |
| 0x00ec4be8 | "fan_process_pwm: AUX FAN: using %u" |
| 0x00ec4c58 | "fan_process_pwm: setting fans to blowout" |
| 0x00ec78dc | "fan_process_temps: turning zone blowout ON" |
| 0x00ec8aa8 | "fan_set_OCSD_sensor_ACR" |
| 0x00ec8b48 | "do_ocsd_associations" |
| 0x00ed00f8 | "fanpid: drive limited (by high)" |

---

## Code Organization Summary

| Chunk | Contains | Address Range |
|-------|----------|---------------|
| chunk_0004 | Code blocks | 0x00ec5xxx - 0x00ed2xxx |
| chunk_0044 | String data | Throughout .health module |
| chunk_0229 | Function definitions | 0x00ec2xxx - 0x00ecfxxx |

---

## Next Steps

1. **Immediate**: Load v2.77 firmware in Ghidra/IDA
2. **Disassemble** the code blocks in the 0x00ec3xxx-0x00ed1xxx range
3. **Identify** the platdef table structure for FanPWM/FanDevice
4. **Find** the I2C/SMBus write functions for fan control
5. **Choose** implementation approach (reimplement or direct HW)

---

## Tools Required

- Ghidra (recommended) or IDA Pro
- v2.77 firmware binary (extracted)
- ARM disassembler knowledge
- Serial console for testing

---

*Document created: 2026-02-19*
*Last updated: 2026-02-19*
