#!/usr/bin/env python3
"""
Verschiebt die I/O-Profiling-Arrays in PSRAM (EXT_RAM_BSS_ATTR),
da 512KB BSS den internen RAM des ESP32-P4 übersteigen.
"""
import re
import sys

PC_FILE = 'pc.c'

with open(PC_FILE, 'r') as f:
    content = f.read()

# Prüfe ob die Arrays existieren
if 'io_port_read_count' not in content:
    print("FEHLER: io_port_read_count nicht gefunden. Profiling nicht aktiv?")
    sys.exit(1)

changes = []

# 1. Füge esp_attr.h Include hinzu (für EXT_RAM_BSS_ATTR)
if '#include "esp_attr.h"' not in content:
    # Finde die erste #include Zeile und füge danach ein
    first_include = content.find('#include')
    if first_include != -1:
        line_end = content.find('\n', first_include) + 1
        content = content[:line_end] + '#include "esp_attr.h"\n' + content[line_end:]
        changes.append("esp_attr.h Include hinzugefügt")

# 2. Verschiebe die Arrays in PSRAM mit EXT_RAM_BSS_ATTR
# Pattern: static uint32_t io_port_read_count[MAX_PROFILE_PORTS] = {0};
old_read = 'static uint32_t io_port_read_count[MAX_PROFILE_PORTS] = {0};'
new_read = 'EXT_RAM_BSS_ATTR static uint32_t io_port_read_count[MAX_PROFILE_PORTS];'

old_write = 'static uint32_t io_port_write_count[MAX_PROFILE_PORTS] = {0};'
new_write = 'EXT_RAM_BSS_ATTR static uint32_t io_port_write_count[MAX_PROFILE_PORTS];'

if old_read in content:
    content = content.replace(old_read, new_read)
    changes.append("io_port_read_count -> PSRAM (EXT_RAM_BSS_ATTR)")
else:
    # Versuche alternatives Pattern (ohne = {0})
    alt_read = 'static uint32_t io_port_read_count[MAX_PROFILE_PORTS];'
    if alt_read in content and 'EXT_RAM_BSS_ATTR static uint32_t io_port_read_count' not in content:
        content = content.replace(alt_read, new_read)
        changes.append("io_port_read_count -> PSRAM (alternatives Pattern)")

if old_write in content:
    content = content.replace(old_write, new_write)
    changes.append("io_port_write_count -> PSRAM (EXT_RAM_BSS_ATTR)")
else:
    alt_write = 'static uint32_t io_port_write_count[MAX_PROFILE_PORTS];'
    if alt_write in content and 'EXT_RAM_BSS_ATTR static uint32_t io_port_write_count' not in content:
        content = content.replace(alt_write, new_write)
        changes.append("io_port_write_count -> PSRAM (alternatives Pattern)")

# 3. Reduziere die Array-Größe als zusätzliche Sicherheitsmaßnahme
# 65536 Ports sind überkill - die meisten I/O-Ports sind < 0x1000
# Aber wir behalten 65536 für Vollständigkeit, da es jetzt in PSRAM ist

with open(PC_FILE, 'w') as f:
    f.write(content)

print("=== Änderungen angewendet ===")
for c in changes:
    print(f"  ✓ {c}")

if not changes:
    print("  Keine Änderungen nötig (bereits angewendet?)")

print("\nHinweis: EXT_RAM_BSS_ATTR verschiebt die Arrays in PSRAM.")
print("PSRAM-BSS wird beim Boot automatisch mit 0 initialisiert.")
