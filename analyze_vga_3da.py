#!/usr/bin/env python3
"""
Analysiert wie VGA Port 0x3DA (Input Status Register 1) in vga.c
emuliert wird. Das ist der Schlüssel zur Performance-Optimierung.
"""
import re

VGA_FILE = 'vga.c'

with open(VGA_FILE, 'r') as f:
    content = f.read()
    lines = content.split('\n')

print("=== Suche nach Port 0x3DA / 0x3DA / 0x03da ===")

# Suche nach 0x3da in verschiedenen Schreibweisen
patterns = ['0x3da', '0x3DA', '0x03da', '0x03DA', '3da', '3DA']
found_lines = []

for i, line in enumerate(lines):
    line_lower = line.lower()
    if '0x3da' in line_lower or '0x03da' in line_lower:
        found_lines.append((i+1, line.strip()))

if found_lines:
    print(f"  {len(found_lines)} Zeilen mit 0x3DA gefunden:")
    for lineno, line in found_lines[:10]:
        print(f"    Zeile {lineno}: {line}")
else:
    print("  Keine direkten 0x3DA-Referenzen gefunden")

# Suche nach Input Status Register, Vertical Retrace, VBI
print("\n=== Suche nach VBI / Vertical Retrace / Status Register ===")
vbi_patterns = ['vbe', 'vertical', 'retrace', 'vbi', 'input_status', 'status_1', 
                'status1', 'st01', 'in1sr', 'in1', 'display_enable', 'display_disabled']

found_vbi = []
for i, line in enumerate(lines):
    line_lower = line.lower()
    for pat in vbi_patterns:
        if pat in line_lower:
            found_vbi.append((i+1, line.strip(), pat))
            break

if found_vbi:
    print(f"  {len(found_vbi)} Zeilen mit VBI-bezogenen Begriffen:")
    for lineno, line, pat in found_vbi[:20]:
        print(f"    Zeile {lineno} [{pat}]: {line}")
else:
    print("  Keine VBI-bezogenen Begriffe gefunden")

# Suche nach der I/O-Read-Funktion für VGA
print("\n=== Suche nach VGA I/O-Read-Funktionen ===")
io_read_patterns = ['vga_io_read', 'vga_read', 'ioport_read', 'read.*port', 
                    'case.*0x3', 's->read', 'port.*read']

found_io = []
for i, line in enumerate(lines):
    line_lower = line.lower()
    if any(p in line_lower for p in ['vga_io', 'vga_read', 'port_read', 'port_readb']):
        found_io.append((i+1, line.strip()))

if found_io:
    print(f"  {len(found_io)} Zeilen mit VGA I/O-Funktionen:")
    for lineno, line in found_io[:10]:
        print(f"    Zeile {lineno}: {line}")

# Suche nach Timing-bezogenen Variablen
print("\n=== Suche nach Timing-Variablen ===")
timing_patterns = ['timer', 'time', 'cycle', 'tick', 'frame', 'refresh', 
                   'hz', '60', 'vsync', 'hsync']

found_timing = []
for i, line in enumerate(lines):
    line_lower = line.lower()
    if any(p in line_lower for p in ['vsync', 'hsync', 'frame_count', 'refresh_rate', 
                                      'vertical_total', 'retrace_count']):
        found_timing.append((i+1, line.strip()))

if found_timing:
    print(f"  {len(found_timing)} Zeilen mit Timing:")
    for lineno, line in found_timing[:10]:
        print(f"    Zeile {lineno}: {line}")
else:
    print("  Keine expliziten Timing-Variablen gefunden")

# Zeige die Funktion die Port 0x3DA behandelt (wahrscheinlich ein switch/case)
print("\n=== Suche nach dem I/O-Dispatch (switch/case für Ports) ===")
for i, line in enumerate(lines):
    if 'switch' in line.lower() and ('addr' in line.lower() or 'port' in line.lower()):
        print(f"  Zeile {i+1}: {line.strip()}")
        # Zeige die nächsten 30 Zeilen für Kontext
        for j in range(i+1, min(i+31, len(lines))):
            print(f"    {lines[j]}")
        break

