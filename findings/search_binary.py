import re
import os

# Read binary file
filepath = r"C:\Users\Lauren\Documents\git projects\ilo4_unlock\elf.bin.bytes"
with open(filepath, 'rb') as f:
    data = f.read()

# Convert to ASCII-only string (replace non-ASCII with .)
ascii_data = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)

# Search patterns
patterns = {
    'fan': re.compile(r'fan|Fan|FAN', re.IGNORECASE),
    'temp': re.compile(r'temp|temperature', re.IGNORECASE),
    'pwm_tach': re.compile(r'pwm|tach', re.IGNORECASE),
    'ocsd': re.compile(r'ocsd|OCSD', re.IGNORECASE),
    'ocbb': re.compile(r'ocbb|OCBB', re.IGNORECASE),
}

results = {k: [] for k in patterns}

# Find all matches and their positions
for pattern_name, pattern in patterns.items():
    for match in pattern.finditer(ascii_data):
        start = match.start()
        # Extract full string around the match
        context_start = max(0, start - 30)
        context_end = min(len(ascii_data), start + 50)
        context = ascii_data[context_start:context_end].strip()
        results[pattern_name].append((start, match.group(), context))

# Output to file
output_path = r"C:\Users\Lauren\Documents\git projects\ilo4_unlock\findings\binary_fan_strings.md"

with open(output_path, 'w', encoding='utf-8') as f:
    f.write('# Binary Fan Strings Search Results\n\n')
    f.write('Search results from: elf.bin.bytes\n\n')
    
    for pattern_name in ['fan', 'temp', 'pwm_tach', 'ocsd', 'ocbb']:
        f.write(f'## {pattern_name.upper()} Strings\n\n')
        matches = results[pattern_name]
        if matches:
            unique = {}
            for offset, matched_str, context in matches:
                if offset not in unique:
                    unique[offset] = (matched_str, context)
            for offset in sorted(unique.keys()):
                matched_str, context = unique[offset]
                ctx_display = context[:120] + '...' if len(context) > 120 else context
                f.write(f'- **Offset {offset}**: `{matched_str}`\n')
                f.write(f'  Context: `{ctx_display}`\n\n')
        else:
            f.write('None found\n\n')
    
    f.write('## Summary\n\n')
    for pattern_name in ['fan', 'temp', 'pwm_tach', 'ocsd', 'ocbb']:
        f.write(f'- {pattern_name.upper()}: {len(set(o for o, _, _ in results[pattern_name]))} unique offsets\n')

print('File written to:', output_path)
print('Total FAN:', len(set(o for o, _, _ in results['fan'])))
print('Total TEMP:', len(set(o for o, _, _ in results['temp'])))
print('Total PWM/TACH:', len(set(o for o, _, _ in results['pwm_tach'])))
print('Total OCSD:', len(set(o for o, _, _ in results['ocsd'])))
print('Total OCBB:', len(set(o for o, _, _ in results['ocbb'])))
