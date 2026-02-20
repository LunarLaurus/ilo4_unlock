#!/usr/bin/env python3
"""
Chunk the entire elf.bin.xml into manageable segments for parallel analysis.
Each chunk contains ~2000 lines mapped to address ranges.
"""

import os
import json
from pathlib import Path

SOURCE_FILE = "elf.bin.xml"
OUTPUT_DIR = "ilosrc"
LINES_PER_CHUNK = 2000

def create_chunks():
    print(f"Reading {SOURCE_FILE}...")
    
    with open(SOURCE_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    print(f"Total lines: {total_lines}")
    
    num_chunks = (total_lines + LINES_PER_CHUNK - 1) // LINES_PER_CHUNK
    print(f"Creating {num_chunks} chunks...")
    
    chunks = []
    
    for chunk_num in range(num_chunks):
        start_line = chunk_num * LINES_PER_CHUNK
        end_line = min(start_line + LINES_PER_CHUNK, total_lines)
        
        # Calculate approximate address range
        # Based on XML: functions start around line 390955
        # Memory addresses in 0x00000000 - 0x00xxxxxx range
        addr_base = start_line * 256  # Rough approximation
        
        chunk_name = f"chunk_{chunk_num:04d}_{start_line:08d}"
        
        chunk_dir = Path(OUTPUT_DIR) / chunk_name
        chunk_dir.mkdir(parents=True, exist_ok=True)
        
        chunk_file = chunk_dir / f"{chunk_name}.xml"
        
        with open(chunk_file, 'w', encoding='utf-8') as cf:
            cf.write(f'<?xml version="1.0" standalone="yes"?>\n')
            cf.write(f'<CHUNK id="{chunk_num}">\n')
            cf.write(f'<!-- Chunk {chunk_num}: Lines {start_line+1} - {end_line} -->\n')
            
            for line in lines[start_line:end_line]:
                cf.write(line)
            
            cf.write('</CHUNK>\n')
        
        chunks.append({
            "name": chunk_name,
            "chunk_num": chunk_num,
            "start_line": start_line + 1,
            "end_line": end_line,
            "lines": end_line - start_line,
            "file": str(chunk_file)
        })
        
        if (chunk_num + 1) % 10 == 0:
            print(f"Progress: {chunk_num + 1}/{num_chunks} chunks created")
    
    index = {
        "source_file": SOURCE_FILE,
        "total_lines": total_lines,
        "lines_per_chunk": LINES_PER_CHUNK,
        "num_chunks": num_chunks,
        "chunks": chunks,
        "output_dir": OUTPUT_DIR
    }
    
    index_file = Path(OUTPUT_DIR) / "INDEX.json"
    with open(index_file, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"\nDone! Created {len(chunks)} chunks")
    print(f"Index saved to: {index_file}")
    
    return chunks

if __name__ == "__main__":
    create_chunks()
