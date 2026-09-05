#!/bin/bash
#
# I/O-Port-Profiling für tiny386
# Fügt Zähler in pc_io_read/pc_io_write ein um zu sehen,
# welche Ports Windows 95 am häufigsten pollt.
#
set -e

PC_FILE="pc.c"
BACKUP="${PC_FILE}.backup_$(date +%Y%m%d_%H%M%S)"

echo "=== Erstelle Backup: $BACKUP ==="
cp "$PC_FILE" "$BACKUP"

echo "=== Füge I/O-Port-Profiling in $PC_FILE ein ==="

python3 << 'PYEOF'
import re

with open('pc.c', 'r') as f:
    content = f.read()

# Prüfe ob bereits Profiling vorhanden
if 'io_port_read_count' in content:
    print("  Profiling bereits vorhanden, überspringe")
    exit(0)

# 1. Füge die Zähler-Arrays am Anfang ein (nach den Includes)
profiling_vars = '''
// === I/O PORT PROFILING ===
#define MAX_PROFILE_PORTS 65536
static uint32_t io_port_read_count[MAX_PROFILE_PORTS] = {0};
static uint32_t io_port_write_count[MAX_PROFILE_PORTS] = {0};
static uint32_t io_port_total_reads = 0;
static uint32_t io_port_total_writes = 0;

void print_io_port_stats(void) {
    printf("\\n=== I/O Port Statistics (Top 20 by reads) ===\\n");
    
    // Finde Top-20 Ports nach Reads
    int top_ports[20] = {0};
    uint32_t top_counts[20] = {0};
    
    for (int i = 0; i < MAX_PROFILE_PORTS; i++) {
        if (io_port_read_count[i] > 0) {
            // Insertion in sortierte Liste
            for (int j = 0; j < 20; j++) {
                if (io_port_read_count[i] > top_counts[j]) {
                    // Schiebe nach unten
                    for (int k = 19; k > j; k--) {
                        top_ports[k] = top_ports[k-1];
                        top_counts[k] = top_counts[k-1];
                    }
                    top_ports[j] = i;
                    top_counts[j] = io_port_read_count[i];
                    break;
                }
            }
        }
    }
    
    printf("  Reads:\\n");
    for (int i = 0; i < 20 && top_counts[i] > 0; i++) {
        printf("    Port 0x%04x: %u reads (%.1f%%)\\n", 
               top_ports[i], top_counts[i],
               100.0 * top_counts[i] / (io_port_total_reads ? io_port_total_reads : 1));
    }
    
    // Top-20 nach Writes
    for (int i = 0; i < 20; i++) { top_ports[i] = 0; top_counts[i] = 0; }
    for (int i = 0; i < MAX_PROFILE_PORTS; i++) {
        if (io_port_write_count[i] > 0) {
            for (int j = 0; j < 20; j++) {
                if (io_port_write_count[i] > top_counts[j]) {
                    for (int k = 19; k > j; k--) {
                        top_ports[k] = top_ports[k-1];
                        top_counts[k] = top_counts[k-1];
                    }
                    top_ports[j] = i;
                    top_counts[j] = io_port_write_count[i];
                    break;
                }
            }
        }
    }
    
    printf("  Writes:\\n");
    for (int i = 0; i < 20 && top_counts[i] > 0; i++) {
        printf("    Port 0x%04x: %u writes (%.1f%%)\\n", 
               top_ports[i], top_counts[i],
               100.0 * top_counts[i] / (io_port_total_writes ? io_port_total_writes : 1));
    }
    
    printf("  Total: %u reads, %u writes\\n\\n", io_port_total_reads, io_port_total_writes);
}
// === END I/O PORT PROFILING ===

'''

# Finde eine gute Stelle zum Einfügen (nach den Includes, vor der ersten Funktion)
# Suche nach "static u8 pc_io_read" und füge davor ein
insert_pos = content.find('static u8 pc_io_read')
if insert_pos == -1:
    insert_pos = content.find('static u16 pc_io_read16')
if insert_pos == -1:
    print("  FEHLER: Konnte pc_io_read nicht finden!")
    exit(1)

content = content[:insert_pos] + profiling_vars + content[insert_pos:]
print("  ✓ Profiling-Variablen eingefügt")

# 2. Füge Zähler in pc_io_read ein
# Pattern: static u8 pc_io_read(void *o, int addr)
read_pattern = r'(static u8 pc_io_read\(void \*o, int addr\)\s*\{)'
read_replacement = r'''\1
    io_port_read_count[addr & 0xFFFF]++;
    io_port_total_reads++;'''
content = re.sub(read_pattern, read_replacement, content)
print("  ✓ Zähler in pc_io_read eingefügt")

# 3. Füge Zähler in pc_io_read16 ein
read16_pattern = r'(static u16 pc_io_read16\(void \*o, int addr\)\s*\{)'
read16_replacement = r'''\1
    io_port_read_count[addr & 0xFFFF]++;
    io_port_total_reads++;'''
content = re.sub(read16_pattern, read16_replacement, content)
print("  ✓ Zähler in pc_io_read16 eingefügt")

# 4. Füge Zähler in pc_io_read32 ein
read32_pattern = r'(static u32 pc_io_read32\(void \*o, int addr\)\s*\{)'
read32_replacement = r'''\1
    io_port_read_count[addr & 0xFFFF]++;
    io_port_total_reads++;'''
content = re.sub(read32_pattern, read32_replacement, content)
print("  ✓ Zähler in pc_io_read32 eingefügt")

# 5. Füge Zähler in pc_io_write ein
write_pattern = r'(static void pc_io_write\(void \*o, int addr, u8 val\)\s*\{)'
write_replacement = r'''\1
    io_port_write_count[addr & 0xFFFF]++;
    io_port_total_writes++;'''
content = re.sub(write_pattern, write_replacement, content)
print("  ✓ Zähler in pc_io_write eingefügt")

# 6. Füge Zähler in pc_io_write16 ein
write16_pattern = r'(static void pc_io_write16\(void \*o, int addr, u16 val\)\s*\{)'
write16_replacement = r'''\1
    io_port_write_count[addr & 0xFFFF]++;
    io_port_total_writes++;'''
content = re.sub(write16_pattern, write16_replacement, content)
print("  ✓ Zähler in pc_io_write16 eingefügt")

# 7. Füge Zähler in pc_io_write32 ein
write32_pattern = r'(static void pc_io_write32\(void \*o, int addr, u32 val\)\s*\{)'
write32_replacement = r'''\1
    io_port_write_count[addr & 0xFFFF]++;
    io_port_total_writes++;'''
content = re.sub(write32_pattern, write32_replacement, content)
print("  ✓ Zähler in pc_io_write32 eingefügt")

with open('pc.c', 'w') as f:
    f.write(content)

print("\n✓ I/O-Port-Profiling in pc.c aktiviert")
print("  Hinweis: print_io_port_stats() muss noch aufgerufen werden")
print("  (entweder periodisch oder über einen Button/Key)")
PYEOF

echo ""
echo "=== Füge periodischen Aufruf von print_io_port_stats ein ==="

python3 << 'PYEOF'
# Füge den Aufruf in i386.c ein (nach dem Opcode-Stats-Print)
with open('i386.c', 'r') as f:
    content = f.read()

if 'print_io_port_stats' in content:
    print("  Aufruf bereits vorhanden")
    exit(0)

# Deklaration hinzufügen (nach den anderen Deklarationen)
if 'void print_opcode_stats(void);' not in content:
    # Füge Deklaration am Anfang ein
    decl_pos = content.find('#include "i386.h"')
    if decl_pos != -1:
        decl_end = content.find('\n', decl_pos) + 1
        decl = '\n// I/O Port Profiling\nvoid print_io_port_stats(void);\n'
        content = content[:decl_end] + decl + content[decl_end:]
        print("  ✓ Deklaration eingefügt")

# Aufruf nach dem Opcode-Stats-Print einfügen
if 'if ((total_opcodes & 0xFFFFFF) == 0)' in content:
    old_call = '''#ifdef PROFILE_OPCODES
\tif ((total_opcodes & 0xFFFFFF) == 0) {
\t\tprint_opcode_stats();
\t}
#endif'''
    
    new_call = '''#ifdef PROFILE_OPCODES
\tif ((total_opcodes & 0xFFFFFF) == 0) {
\t\tprint_opcode_stats();
\t\tprint_io_port_stats();
\t}
#endif'''
    
    content = content.replace(old_call, new_call)
    print("  ✓ print_io_port_stats() nach print_opcode_stats() eingefügt")
else:
    print("  WARNUNG: Konnte den Opcode-Stats-Aufruf nicht finden")
    print("  Möglicherweise ist das Format anders")

with open('i386.c', 'w') as f:
    f.write(content)

print("\n✓ Periodischer Aufruf aktiviert")
PYEOF

echo ""
echo "=== Zusammenfassung ==="
echo "Das Profiling wurde aktiviert. Beim nächsten Build werden"
echo "die Top-20 I/O-Ports angezeigt (alle ~16M Opcodes)."
echo ""
echo "Nächste Schritte:"
echo "  1. cd esp && idf.py build"
echo "  2. idf.py -p /dev/ttyACM0 -b 921600 flash monitor"
echo "  3. Windows 95 booten und die I/O-Statistiken beobachten"
echo ""
echo "Wichtige Ports die wir erwarten:"
echo "  0x3DA: VGA Input Status Register 1 (VBI-Polling!)"
echo "  0x3C0-0x3DF: VGA-Ports"
echo "  0x1F0-0x1F7: IDE/Festplatte"
echo "  0x40-0x43: PIT Timer"
echo "  0x20-0x21: PIC Interrupt Controller"
