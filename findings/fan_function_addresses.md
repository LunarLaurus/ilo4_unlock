# Fan Function Virtual Addresses

Analysis of fan control code in iLO4 firmware, based on string references in `binary_fan_strings.md`.

## Memory Mapping

| Section | Virtual Address | File Offset | Size |
|---------|-----------------|-------------|------|
| `.health.elf.text` | 0x00ea1000 | 0x358f4c | 0xa8e98 |

**Conversion formula**: `VA = 0x00ea1000 + (file_offset - 0x358f4c)`

## Summary

All fan control functions are located within the `.health.elf.text` module at virtual addresses between **0x00ea1000** and **0x00f49e97**.

### Key Function Ranges

| Function Category | Virtual Address Range | Description |
|-----------------|----------------------|-------------|
| Fan Event Handlers | 0x00ea9500 - 0x00eaa000 | Inserted/removed/failed handling |
| Fan Redundancy | 0x00eab500 - 0x00eabe00 | Redundancy state management |
| **Main Dispatcher** | **0x00ec3d00 - 0x00ec4300** | Central fan command dispatcher |
| PWM Control | 0x00ec4b00 - 0x00ec4d00 | PWM duty cycle management |
| OCSD Impact | 0x00ec5700 - 0x00ec5e00 | OCSD sensor processing |
| Fan Grouping | 0x00ec5500 - 0x00ec5d00 | Fan grouping logic |
| Temperature Control | 0x00ec7800 - 0x00ec7f00 | Temperature-based fan control |
| OCSD Associations | 0x00ec8a00 - 0x00ec8c00 | OCSD sensor associations |
| Fan Monitor | 0x00ec9800 - 0x00ec9900 | Monitor start/stop control |
| Fan Rundown | 0x00ec9c00 - 0x00ec9e00 | Cleanup and shutdown |
| PID Control | 0x00ed0100 - 0x00ed0500 | PID algorithm for fan speed |

---

## Detailed Function Addresses

### Main Fan Dispatcher

| File Offset (dec) | File Offset (hex) | Virtual Address | String |
|-------------------|-------------------|-----------------|--------|
| 3652756 | 0x0037bc94 | **0x00ec3d48** | fan: dispatcher: error |
| 3654084 | 0x0037c1c4 | **0x00ec4278** | fan: FAN_SET |
| 3654192 | 0x0037c230 | **0x00ec42e4** | fan: dispatch(): invalid command |

**Location**: The main dispatcher is at approximately **0x00ec3d48** - this is where fan commands (FAN_SET, FAN_GET, etc.) are routed.

---

### PWM Control

| File Offset (dec) | File Offset (hex) | Virtual Address | String |
|-------------------|-------------------|-----------------|--------|
| 3656500 | 0x0037cb34 | **0x00ec4be8** | fan_process_pwm: AUX FAN |
| 3656612 | 0x0037cba4 | **0x00ec4c58** | fan_process_pwm: setting fans to blowout |
| 3656632 | 0x0037cbb8 | **0x00ec4c6c** | Fan speed adjusted externally |
| 3661036 | 0x0037dcec | **0x00ec5da0** | fan: PWM re-enabled |

**Location**: PWM control functions are at **0x00ec4be8** - handles Pulse Width Modulation for fan speed control.

---

### Temperature Control

| File Offset (dec) | File Offset (hex) | Virtual Address | String |
|-------------------|-------------------|-----------------|--------|
| 3668008 | 0x0037f828 | **0x00ec78dc** | fan_process_temps: turning zone blowout ON/OFF |
| 3669404 | 0x0037fd9c | **0x00ec7e50** | fan: errors, activating blowout |

**Location**: Temperature-based fan control is at **0x00ec78dc** - adjusts fan speeds based on temperature sensor readings.

---

### OCSD (Optimal Cooling System Diagnostics)

| File Offset (dec) | File Offset (hex) | Virtual Address | String |
|-------------------|-------------------|-----------------|--------|
| 3659560 | 0x0037d728 | **0x00ec57dc** | fan_ocsd_impact: process associated OCSD |
| 3659644 | 0x0037d77c | **0x00ec5830** | fan_ocsd_impact: status check |
| 3660600 | 0x0037db38 | **0x00ec5bec** | fan_ocsd_impact: OK but NOT enabled |
| 3672564 | 0x003809f4 | **0x00ec8aa8** | fan_set_OCSD_sensor_ACR |
| 3672724 | 0x00380a94 | **0x00ec8b48** | do_ocsd_associations |

**Location**: OCSD functions are at **0x00ec57dc** to **0x00ec8b48** - handles OCSD sensor associations and control.

---

### Fan Monitor Control

| File Offset (dec) | File Offset (hex) | Virtual Address | String |
|-------------------|-------------------|-----------------|--------|
| 3676092 | 0x003817bc | **0x00ec9870** | fan: monitor stopped->start |
| 3676124 | 0x003817dc | **0x00ec9890** | fan: monitor running->stop |

**Location**: Fan monitor control at **0x00ec9870** - starts/stops the fan monitoring loop.

---

### Fan Rundown/Cleanup

| File Offset (dec) | File Offset (hex) | Virtual Address | String |
|-------------------|-------------------|-----------------|--------|
| 3652912 | 0x0037bd30 | **0x00ec3de4** | fan_register_clear: releasing semaphore |
| 3677176 | 0x00381bf8 | **0x00ec9cac** | fan_rundown: Waiting for fan_sem |
| 3677280 | 0x00381c60 | **0x00ec9d14** | fan_rundown: PWM state clearing |
| 3677368 | 0x00381cb8 | **0x00ec9d6c** | fan_rundown: releasing fan_sem |

**Location**: Cleanup functions at **0x00ec9cac** - handles graceful shutdown and semaphore management.

---

### Fan Redundancy (eh_rfan)

| File Offset (dec) | File Offset (hex) | Virtual Address | String |
|-------------------|-------------------|-----------------|--------|
| 3552420 | 0x003634a4 | **0x00eab558** | Redundancy rule member not found |
| 3554456 | 0x00363c98 | **0x00eabd4c** | RD -> CO state transition |
| 3554552 | 0x00363cf8 | **0x00eabdac** | fan redundancy rule not found |

**Location**: Redundancy management at **0x00eab558** - handles fan redundancy states (RD=Redundant, CO=Critical, NML=Normal, NR=Non-Redundant).

---

### Fan Event Handlers (eh_fan)

| File Offset (dec) | File Offset (hex) | Virtual Address | String |
|-------------------|-------------------|-----------------|--------|
| 3544192 | 0x00361480 | **0x00ea9534** | fan action: fan inserted |
| 3544204 | 0x0036148c | **0x00ea9540** | fan action: fan removed |
| 3545168 | 0x00361850 | **0x00ea9904** | fan action: fan failed |
| 3545180 | 0x0036185c | **0x00ea9910** | fan action: fan fixed |
| 3545874 | 0x00361b12 | **0x00ea9bc6** | fan_stimuli: device not found |
| 3545915 | 0x00361b3b | **0x00ea9bef** | eh_fan: unknown error for fan_block |

**Location**: Event handlers at **0x00ea9500** - processes fan insertion, removal, failure events.

---

### PID Control (fanpid)

| File Offset (dec) | File Offset (hex) | Virtual Address | String |
|-------------------|-------------------|-----------------|--------|
| 3702852 | 0x00388044 | **0x00ed00f8** | fanpid: drive limited |
| 3702904 | 0x00388078 | **0x00ed012c** | fanpid: Psum calculation |

**Location**: PID controller at **0x00ed00f8** - implements the PID (Proportional-Integral-Derivative) control algorithm for fan speed.

---

### Fan Grouping

| File Offset (dec) | File Offset (hex) | Virtual Address | String |
|-------------------|-------------------|-----------------|--------|
| 3658848 | 0x0037d460 | **0x00ec5514** | fan: group(): illegal weighting set |
| 3660848 | 0x0037dc30 | **0x00ec5ce4** | fan: group(): illegal weighting get |

**Location**: Fan grouping at **0x00ec5514** - manages fan group weighting for cooling zones.

---

### Fan Adjustment

| File Offset (dec) | File Offset (hex) | Virtual Address | String |
|-------------------|-------------------|-----------------|--------|
| 3662460 | 0x0037e27c | **0x00ec6330** | fan: adjustment: error - big i |
| 3663296 | 0x0037e5c0 | **0x00ec6674** | fan: adjustment: modifier for sensor |
| 3703788 | 0x003883ec | **0x00ed04a0** | fan: setpoint adjustment: error |

---

### Sensor Processing

| File Offset (dec) | File Offset (hex) | Virtual Address | String |
|-------------------|-------------------|-----------------|--------|
| 3665356 | 0x0037edcc | **0x00ec6e80** | fan: alg: exp. not implemented |
| 3665484 | 0x0037ee4c | **0x00ec6f00** | fan: sensor: NO reading yet |
| 3667896 | 0x0037f7b8 | **0x00ec786c** | fan: skipping POST sensor |

---

## IPC Dispatch Information

Based on prior analysis, the fan controller is accessed via IPC with:
- **IPC Switch Value**: 6 (for fan control)
- **Jump Table Location**: `.health.elf.text:0x00E04CB4`

The fan dispatcher at **0x00ec3d48** handles commands including:
- FAN_SET (set fan speed/PWM)
- FAN_GET (read fan status)
- Monitor start/stop controls
