# iLO4 Unlock Project Analysis

## Project Overview

**Project Name:** iLO4 Unlock (Silence of the Fans)  
**Repository:** https://github.com/kendallgoto/ilo4_unlock  
**License:** GNU General Public License v3.0

## Purpose

This toolkit patches HPE iLO 4 firmware to unlock hidden administrative utilities, primarily allowing control over server fan curves. The project targets homelab users who need to:
- Control aggressive HP fan curves on DL380p Gen8/Gen9 servers
- Use non-HPE certified PCI-e cards without fans maxing out
- Access hidden system health commands via SSH

## Technical Architecture

### Core Components

```
ilo4_unlock/
├── build.sh                    # Main build orchestration script
├── automatic.sh               # Automated build wrapper
├── ilo4_toolbox/               # Submodule: Airbus Security Lab iLO4 Toolkit
│   └── scripts/iLO4/
│       ├── ilo4_extract.py     # Firmware extraction
│       ├── ilo4_repack.py     # Firmware repacking
│       ├── ilo5_*             # iLO5 support tools
│       └── secinfo4.py        # Security information utilities
├── util/                       # Patching utilities
│   ├── patch.py               # Binary patching engine (JSON-based)
│   ├── common.py              # Shared utilities
│   ├── asm/                   # Assembly snippets for patches
│   └── gcc/                   # GCC cross-compilation for ARM iLO
├── patches/                    # Firmware version patches
│   ├── 250/                   # v2.50 patch set
│   ├── 273/                   # v2.73 patch set
│   ├── 277/                   # v2.77 patch set (latest)
│   ├── 278/                   # v2.78 patch set
│   ├── 279/                   # v2.79 patch set
│   ├── 277-tools/             # v2.77 with additional tools
│   └── 277-memdump/           # v2.77 with memory dump capability
├── scripts/                   # User-facing helper scripts
└── binaries/                  # Downloaded HPE firmware (not in repo)
```

### Patch Structure

Each patch version directory contains:
- `patch_bootloader.json` - Bootloader signature bypass patches
- `patch_kernel.json` - Kernel modifications
- `patch_userland.json` - Userland (elf) modifications
- `config` - Build configuration with binary URLs and SHA1 hashes
- `readme.md` - Version-specific documentation
- `asm/` - Assembly code injections

## Build Process

### Prerequisites
- Python 2.7
- Linux build environment (CentOS 8, Ubuntu 22.04 tested)
- `wget` for downloading firmware
- ARM cross-compiler (for assembly injection)

### Workflow

1. **Initialization**: `./build.sh init` downloads HPE firmware binaries
2. **Extraction**: `ilo4_extract.py` unpacks firmware components
3. **Patching**: Three-stage binary patching via `util/patch.py`
   - Bootloader (signature verification bypass)
   - Kernel (fan controller unlock)
   - Userland (command injection)
4. **Repacking**: `ilo4_repack.py` reconstructs firmware

## Unlocked Features

### SSH Commands via iLO

| Command | Description |
|---------|-------------|
| `h` | System health information |
| `fan` | Fan tuning and control |
| `ocsd` | On-board temperature sensors |
| `ocbb` | Option chip health systems |

### Fan Controller Subcommands

- **Temperature sensors**: Enable/disable, set thresholds
- **Tachometers**: Configure fan speed monitoring
- **PWM control**: Manual fan speed percentage
- **PID algorithm**: Configure proportional-integral-derivative loops

## Supported Firmware Versions

| Version | Status | Notes |
|---------|--------|-------|
| 2.50 | ✅ Working | Original base |
| 2.73 | ✅ Working | Popular choice |
| 2.77 | ✅ Working | **Latest recommended** |
| 2.78 | ⚠️ Limited | Utilities removed by HP |
| 2.79 | ⚠️ Limited | Utilities removed by HP |

## Security Considerations

### Legal Warnings
- Flashing errors can brick iLO (requires hardware programming to recover)
- Using modified firmware may void warranty
- Potential for system damage from improper fan control

### Technical Risks
- No on-board flash recovery (JTAG/desoldering required)
- iLO security override must be physically enabled
- Fan misconfiguration can cause overheating

## Dependencies

### Python Packages
- Python 2.7 runtime
- Configured via `requirements.txt`

### External Tools
- `wget` - Firmware download
- `sha1sum` - Binary verification
- ARM cross-compiler (util/gcc/)

## Usage Example

```bash
# Setup environment
./build.sh init

# Build patched firmware
./build.sh 277

# Flash via USB (requires security override)
sudo ./flash_ilo4 --direct
```

## Related Research

- Airbus Security Lab iLO4 Toolbox
- /u/phoenixdev's original v2.60/v2.73 patches
- SSTIC 2018: "Subverting your server through its BMC: the HPE iLO4 case"

## File Manifest

- **Total files**: ~100+ files across project
- **Patch sets**: 7 distinct firmware versions
- **Languages**: Python (primary), Bash (build), Assembly (injection), C (utilities)
