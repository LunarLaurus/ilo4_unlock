# Python 2.7 to Python 3.10+ Migration Plan
# ilo4_unlock Project

## Executive Summary

This document outlines a comprehensive migration plan to upgrade the ilo4_unlock project from Python 2.7 to Python 3.10+. The codebase contains 34 Python files with extensive Python 2-specific syntax patterns that require systematic modernization.

**Recommendation**: DROP Python 2 support entirely. Python 2 reached end-of-life in January 2020, and maintaining dual compatibility introduces significant complexity with minimal benefit. The ilo5lib.py file already demonstrates that modern Python 3 patterns work correctly with this codebase.

---

## 1. Complete File Inventory

### 1.1 Core Library Files (Priority: HIGH)
| File Path | Python 2 Syntax Count | Priority |
|-----------|----------------------|----------|
| ilo4_toolbox/scripts/iLO4/ilo4lib.py | ~50 print statements, xrange(3), .encode(hex) | HIGH |
| ilo4_toolbox/scripts/iLO5/ilo5lib.py | Already modernized | LOW |
| util/common.py | print statements, xrange(1), e.message | HIGH |
| util/patch.py | print statements, import imp, sys.getsizeof | HIGH |
| util/repl.py | print statements, raw_input(1) | HIGH |

### 1.2 iLO4 Scripts (Priority: HIGH)
| File Path | Issues | Priority |
|-----------|--------|----------|
| ilo4_toolbox/scripts/iLO4/ilo4_extract.py | ~30 print, .encode(hex), .iteritems() | HIGH |
| ilo4_toolbox/scripts/iLO4/ilo4_repack.py | ~15 print statements | HIGH |
| ilo4_toolbox/scripts/iLO4/parse_mr.py | 3 print statements | MEDIUM |
| ilo4_toolbox/scripts/iLO4/secinfo4.py | 4 print statements | MEDIUM |
| ilo4_toolbox/scripts/iLO4/patch_bootloader_250.py | 4 print, .encode(hex) | HIGH |
| ilo4_toolbox/scripts/iLO4/patch_kernel_250.py | 4 print, .encode(hex) | HIGH |
| ilo4_toolbox/scripts/iLO4/patch_webserver_250.py | 4 print, e.message | HIGH |
| ilo4_toolbox/scripts/iLO4/backdoor_client.py | 3 print, xrange(1) | HIGH |

### 1.3 iLO4 Notpetya Scripts
| File Path | Issues | Priority |
|-----------|--------|----------|
| notpetya/patch_mem_ilo.py | 4 print, .encode(hex), raw_input, .decode(hex) | HIGH |
| notpetya/mod_backdoor.py | 1 xrange | MEDIUM |
| notpetya/remap_bootloader.py | None detected | LOW |

### 1.4 iLO4 Exploits
| File Path | Issues | Priority |
|-----------|--------|----------|
| exploits/exploit_write_flash.py | 1 xrange | MEDIUM |
| exploits/exploit_helpers.py | 2 chr() usages | MEDIUM |
| exploits/exploit_ssh.py | Already Python 3 | LOW |
| exploits/exploit_check_flash.py | None | LOW |
| exploits/exploit_offsets.py | None | LOW |

### 1.5 iLO5 Scripts
| File Path | Issues | Priority |
|-----------|--------|----------|
| ilo5_extract.py | Already modernized | LOW |
| ilo5_PoC_secure_boot_bypass.py | ~20 print statements | HIGH |
| ilo5_PoC_fum_sig_bypass.py | ~15 print statements | HIGH |
| ilo5_image_decrypt.py | Modernized | LOW |
| ilo5_fw_decrypt.py | Modernized | LOW |
| secinfo5.py | IDA Pro only | N/A |
| parse_mr.py | IDA Pro only | N/A |

### 1.6 Utility Scripts
| File Path | Issues | Priority |
|-----------|--------|----------|
| util/find_sig_check.py | Python 2 shebang | MEDIUM |
| util/compare_fw.py | Python 2 shebang | MEDIUM |
| misc/extract-after-compile.py | ~20 print, .encode(hex), .iteritems() | HIGH |

---

## 2. Python 2->3 Incompatibilities Found

### Print Statements: ~250 occurrences
All files: print without parentheses

### xrange(): 7 occurrences
- ilo4lib.py: lines 41, 261, 273
- util/common.py: line 45
- notpetya/mod_backdoor.py: line 90
- backdoor_client.py: line 115
- exploit_write_flash.py: line 74

### raw_input(): 2 occurrences
- util/repl.py: line 228
- notpetya/patch_mem_ilo.py: line 31

### encode/decode hex: 10 occurrences
- ilo4lib.py: line 100
- patch_kernel_250.py: line 19
- patch_bootloader_250.py: line 19
- notpetya/patch_mem_ilo.py: lines 26, 28, 38
- ilo4_extract.py: line 104
- misc/extract-after-compile.py: line 59
- util/patch.py: lines 48, 63

### dict.iteritems(): 2 occurrences
- ilo4_extract.py: line 249
- misc/extract-after-compile.py: line 208

### e.message: 2 occurrences
- patch_webserver_250.py: line 18
- util/common.py: line 37

### import imp: 1 occurrence
- util/patch.py: line 21

### sys.getsizeof: 1 occurrence
- util/patch.py: line 64

---

## 3. Dependencies

### Current (requirements.txt)
- keystone-engine==0.9.2
- paramiko==2.9.2

### Required Updates
- keystone-engine: 0.9.2 -> 1.0.0+ (Python 3 required)
- paramiko: 2.9.2 -> 2.12.0+ (Python 3 support)
- requests: Add for notpetya scripts

---

## 4. Testing Strategy

1. **Syntax Check**: python3 -m py_compile <file.py>
2. **Import Testing**: Test modules in isolation
3. **Functional Testing**: Extract/repack operations
4. **Integration Testing**: Run build.sh
5. **Docker Testing**: Build container

---

## 5. Python 2 Support Decision

**DROP Python 2 Support Entirely**

Rationale:
- Python 2 EOL: January 2020
- Modern dependencies require Python 3
- ilo5lib.py shows Python 3 works
- Dual compatibility = maintenance burden

---

## 6. Build Script Updates

### build.sh
Change all python to python3 in calls

### Shebangs
Update all from #!/usr/bin/env python to #!/usr/bin/env python3

---

## 7. Docker Updates

### Current
- Uses Python 2.7 with debian:bullseye-slim

### Required
- Base: python:3.10-slim-bookworm
- Remove virtualenv steps
- Update pip commands

---

## 8. Implementation Roadmap

| Week | Tasks |
|------|-------|
| 1 | Core libs: ilo4lib.py, common.py, patch.py |
| 1-2 | iLO4 scripts: extract, repack, patch files |
| 2 | iLO5 scripts, misc scripts |
| 2 | Notpetya and exploits |
| 3 | build.sh, Dockerfile, requirements.txt |
| 3-4 | Testing and validation |

---

## 9. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breaking functionality | HIGH | Comprehensive testing |
| Keystone API changes | MEDIUM | Review docs |
| Bytes vs strings | HIGH | Careful testing |
| Docker failures | MEDIUM | Test build |

---

## 10. Success Criteria

1. All files pass python3 -m py_compile
2. build.sh works with Python 3
3. Docker builds successfully
4. No Python 2 syntax remains (except IDA)

---

## Appendix: Quick Reference

| Python 2 | Python 3 |
|----------|----------|
| print x | print(x) |
| xrange | range |
| raw_input | input |
| .encode(hex) | .hex() |
| .decode(hex) | bytes.fromhex() |
| .iteritems() | .items() |
| e.message | str(e) |
| import imp | remove |

---

## Summary

- Total Python Files: 34
- Major Changes Needed: ~15
- Already Compatible: ~5
- IDA Pro (cannot migrate): 4
- Estimated Effort: 3-4 weeks
