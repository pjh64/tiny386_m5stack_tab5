#!/usr/bin/env python3
"""
Optimiert Port 0x331 (Floppy Controller Status Register) für Polling.
Ähnliche Strategie wie bei VGA Port 0x3DA.
"""
import re

# Finde die Datei die Port 0x331 behandelt
FLOPPY_FILE = 'i8259.c'  # Floppy-Controller ist typischerweise hier oder in floppy.c

# Prüfe ob floppy.c existiert
import os
if os.path.exists('floppy.c'):
    FLOPPY_FILE = 'floppy.c'
elif os.path.exists('fdc.c'):
    FLOPPY_FILE = 'fdc.c'

print(f"Analysiere {FLOPPY_FILE} für Port 0x331...")

with open(FLOPPY_FILE, 'r') as f:
    content = f.read()
    lines = content.split('\n')

# Suche nach Port 0x331
found = False
for i, line in enumerate(lines):
    if '0x331' in line or '0x330' in line:
        print(f"Zeile {i+1}: {line.strip()}")
        found = True

if not found:
    print(f"Port 0x331 nicht in {FLOPPY_FILE} gefunden!")
    print("Suche in allen .c Dateien...")
    
    import subprocess
    result = subprocess.run(['grep', '-rn', '0x331', '*.c'], 
                          capture_output=True, text=True)
    print(result.stdout)

