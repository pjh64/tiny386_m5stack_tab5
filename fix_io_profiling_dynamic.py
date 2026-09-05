#!/usr/bin/env python3
"""
Ersetzt die statischen 512KB I/O-Profiling-Arrays durch dynamisch
allozierte Buffer in PSRAM (heap_caps_malloc MALLOC_CAP_SPIRAM).
Das umgeht das BSS-Größenproblem komplett.
"""
import re
import sys

PC_FILE = 'pc.c'

with open(PC_FILE, 'r') as f:
    content = f.read()

if 'io_port_read_count' not in content:
    print("FEHLER: io_port_read_count nicht gefunden.")
    sys.exit(1)

# === 1. Ersetze die Array-Deklarationen durch Pointer + Lazy-Init ===

# Finde den gesamten Profiling-Block und ersetze ihn
# Wir suchen die Deklarationen (mit oder ohne EXT_RAM_BSS_ATTR)
old_decl_patterns = [
    r'EXT_RAM_BSS_ATTR static uint32_t io_port_read_count\[MAX_PROFILE_PORTS\];',
    r'static uint32_t io_port_read_count\[MAX_PROFILE_PORTS\] = \{0\};',
    r'static uint32_t io_port_read_count\[MAX_PROFILE_PORTS\];',
]
old_decl_patterns_w = [
    r'EXT_RAM_BSS_ATTR static uint32_t io_port_write_count\[MAX_PROFILE_PORTS\];',
    r'static uint32_t io_port_write_count\[MAX_PROFILE_PORTS\] = \{0\};',
    r'static uint32_t io_port_write_count\[MAX_PROFILE_PORTS\];',
]

for pat in old_decl_patterns:
    content = re.sub(pat, '', content)
for pat in old_decl_patterns_w:
    content = re.sub(pat, '', content)

# Füge die neuen Pointer-Deklarationen + Lazy-Init-Funktion ein
# Finde die Stelle nach "#define MAX_PROFILE_PORTS"
new_decls = '''
// I/O Port Profiling - dynamisch in PSRAM alloziert (vermeidet BSS-Overflow)
static uint32_t *io_port_read_count = NULL;
static uint32_t *io_port_write_count = NULL;
static int io_profiling_initialized = 0;

static void io_profiling_init(void) {
    if (io_profiling_initialized) return;
    io_profiling_initialized = 1;
    // Alloziere in PSRAM (SPIRAM), nicht im knappen internen RAM
    io_port_read_count = (uint32_t*)heap_caps_malloc(MAX_PROFILE_PORTS * sizeof(uint32_t), MALLOC_CAP_SPIRAM);
    io_port_write_count = (uint32_t*)heap_caps_malloc(MAX_PROFILE_PORTS * sizeof(uint32_t), MALLOC_CAP_SPIRAM);
    if (io_port_read_count) memset(io_port_read_count, 0, MAX_PROFILE_PORTS * sizeof(uint32_t));
    if (io_port_write_count) memset(io_port_write_count, 0, MAX_PROFILE_PORTS * sizeof(uint32_t));
    if (!io_port_read_count || !io_port_write_count) {
        printf("WARN: I/O profiling PSRAM alloc failed\\n");
    }
}
'''

# Finde die MAX_PROFILE_PORTS Definition und füge danach ein
define_match = re.search(r'#define MAX_PROFILE_PORTS\s+\d+', content)
if define_match:
    insert_pos = define_match.end()
    content = content[:insert_pos] + new_decls + content[insert_pos:]
    print("  ✓ Neue Pointer-Deklarationen + Lazy-Init eingefügt")
else:
    print("  FEHLER: MAX_PROFILE_PORTS Definition nicht gefunden")
    sys.exit(1)

# === 2. Füge notwendige Includes hinzu ===
if '#include "esp_heap_caps.h"' not in content:
    first_include = content.find('#include')
    if first_include != -1:
        line_end = content.find('\n', first_include) + 1
        content = content[:line_end] + '#include "esp_heap_caps.h"\n' + content[line_end:]
        print("  ✓ esp_heap_caps.h Include hinzugefügt")

if '#include <string.h>' not in content and '#include <string.h>' not in content:
    # memset braucht string.h - prüfe ob schon vorhanden
    if 'memset' in content and 'string.h' not in content:
        first_include = content.find('#include')
        line_end = content.find('\n', first_include) + 1
        content = content[:line_end] + '#include <string.h>\n' + content[line_end:]
        print("  ✓ string.h Include hinzugefügt")

# === 3. Aktualisiere die Zähler-Zugriffe mit Lazy-Init + NULL-Check ===

# pc_io_read: io_port_read_count[addr & 0xFFFF]++;
# Ersetze mit Lazy-Init-Aufruf
old_read_increment = '''    io_port_read_count[addr & 0xFFFF]++;
    io_port_total_reads++;'''
new_read_increment = '''    if (!io_profiling_initialized) io_profiling_init();
    if (io_port_read_count) io_port_read_count[addr & 0xFFFF]++;
    io_port_total_reads++;'''

count = content.count(old_read_increment)
content = content.replace(old_read_increment, new_read_increment)
print(f"  ✓ {count} Lese-Zähler aktualisiert")

# pc_io_write
old_write_increment = '''    io_port_write_count[addr & 0xFFFF]++;
    io_port_total_writes++;'''
new_write_increment = '''    if (!io_profiling_initialized) io_profiling_init();
    if (io_port_write_count) io_port_write_count[addr & 0xFFFF]++;
    io_port_total_writes++;'''

count = content.count(old_write_increment)
content = content.replace(old_write_increment, new_write_increment)
print(f"  ✓ {count} Schreib-Zähler aktualisiert")

# === 4. Aktualisiere print_io_port_stats mit NULL-Checks ===
# Die Funktion greift auf io_port_read_count[i] zu - füge NULL-Check am Anfang ein
old_print_start = 'void print_io_port_stats(void) {\n    printf("\\n=== I/O Port Statistics (Top 20 by reads) ===\\n");'
new_print_start = '''void print_io_port_stats(void) {
    if (!io_profiling_initialized) io_profiling_init();
    if (!io_port_read_count || !io_port_write_count) {
        printf("I/O profiling not available (PSRAM alloc failed)\\n");
        return;
    }
    printf("\\n=== I/O Port Statistics (Top 20 by reads) ===\\n");'''

if old_print_start in content:
    content = content.replace(old_print_start, new_print_start)
    print("  ✓ print_io_port_stats NULL-Check hinzugefügt")
else:
    # Versuche alternatives Pattern
    alt = 'void print_io_port_stats(void) {'
    if alt in content:
        content = content.replace(alt, alt + '\n    if (!io_profiling_initialized) io_profiling_init();\n    if (!io_port_read_count || !io_port_write_count) return;', 1)
        print("  ✓ print_io_port_stats NULL-Check hinzugefügt (alternativ)")

with open(PC_FILE, 'w') as f:
    f.write(content)

print("\n=== Zusammenfassung ===")
print("Die I/O-Profiling-Arrays werden jetzt dynamisch in PSRAM alloziert.")
print("Das umgeht das BSS-Größenproblem komplett.")
print("\nNächster Schritt: cd esp && idf.py build")
