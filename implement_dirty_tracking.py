#!/usr/bin/env python3
import sys

print("=== Implementiere Dirty-Tracking ===\n")

with open('vga.c', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Schritt 1: mark_line_dirty Funktion vor vga_mem_write einfügen
print("Schritt 1: Füge mark_line_dirty Funktion ein...")
mark_func = '''
static inline void mark_line_dirty(VGAState *s, uint32_t addr) {
    if (!s->dirty_lines || s->dirty_lines_size == 0) return;
    
    // Calculate line from address
    int bpp = s->vbe_regs[VBE_DISPI_INDEX_BPP];
    int width = s->vbe_regs[VBE_DISPI_INDEX_XRES];
    if (width == 0) width = 640;
    if (bpp == 0) bpp = 8;
    
    int bytes_per_line = width * (bpp / 8);
    int line = addr / bytes_per_line;
    
    if (line < s->dirty_lines_size) {
        s->dirty_lines[line] = 1;
    }
}

'''

# Finde vga_mem_write
for i, line in enumerate(lines):
    if 'void IRAM_ATTR vga_mem_write(VGAState *s, uint32_t addr, uint8_t val8)' in line:
        lines.insert(i, mark_func)
        print(f"  ✓ mark_line_dirty bei Zeile {i+1} eingefügt")
        break
else:
    print("  ✗ FEHLER: vga_mem_write nicht gefunden")
    sys.exit(1)

# Schritt 2: Aufruf von mark_line_dirty am Ende von vga_mem_write
print("\nSchritt 2: Füge mark_line_dirty Aufruf in vga_mem_write ein...")
found_end = False
for i, line in enumerate(lines):
    if 'void IRAM_ATTR vga_mem_write(VGAState *s, uint32_t addr, uint8_t val8)' in line:
        # Suche nach dem Ende der Funktion (nächstes } auf Spalte 0)
        for j in range(i+1, min(i+200, len(lines))):
            if lines[j].strip() == '}' and lines[j].startswith('}'):
                # Füge mark_line_dirty vor dem schließenden } ein
                mark_call = '    mark_line_dirty(s, addr);\n'
                lines.insert(j, mark_call)
                print(f"  ✓ mark_line_dirty Aufruf bei Zeile {j+1} eingefügt")
                found_end = True
                break
        break

if not found_end:
    print("  ✗ FEHLER: Ende von vga_mem_write nicht gefunden")
    sys.exit(1)

# Schritt 3: Optimierte Schleife in vga_graphic_refresh
print("\nSchritt 3: Optimiere Schleife in vga_graphic_refresh...")
optimized_loop = '''    // Mark all lines dirty if full_update
    if (full_update && s->dirty_lines) {
        int max_lines = (h < s->dirty_lines_size) ? h : s->dirty_lines_size;
        memset(s->dirty_lines, 1, max_lines);
    }
    
    for (int y = 0; y < h; y++) {
        // Skip non-dirty lines unless full_update
        if (!full_update && s->dirty_lines && !s->dirty_lines[y]) {
            continue;
        }
'''

found_loop = False
for i, line in enumerate(lines):
    if 'for (int y = 0; y < h; y++)' in line and 'vga_graphic_refresh' in ''.join(lines[max(0,i-100):i]):
        lines[i] = optimized_loop
        print(f"  ✓ Optimierte Schleife bei Zeile {i+1} eingefügt")
        found_loop = True
        break

if not found_loop:
    print("  ✗ FEHLER: for-Schleife nicht gefunden")
    sys.exit(1)

# Schritt 4: Dirty-Reset vor redraw_func
print("\nSchritt 4: Füge Dirty-Reset vor redraw_func ein...")
reset_dirty = '''    // Clear dirty flags for processed lines
    if (!full_update && s->dirty_lines) {
        int max_lines = (h < s->dirty_lines_size) ? h : s->dirty_lines_size;
        memset(s->dirty_lines, 0, max_lines);
    }
    
'''

found_redraw = False
for i, line in enumerate(lines):
    if 'redraw_func(opaque, 0, 0, fb_dev->width, fb_dev->height);' in line:
        # Prüfe ob dies in vga_graphic_refresh ist
        if 'vga_graphic_refresh' in ''.join(lines[max(0,i-300):i]):
            lines.insert(i, reset_dirty)
            print(f"  ✓ Dirty-Reset bei Zeile {i+1} eingefügt")
            found_redraw = True
            break

if not found_redraw:
    print("  ✗ FEHLER: redraw_func nicht gefunden")
    sys.exit(1)

# Schreibe die Datei zurück
with open('vga.c', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n=== ✓✓✓ Alle Änderungen erfolgreich implementiert! ✓✓✓ ===")
print("\nErwartete Verbesserungen:")
print("  - vga_step: 42ms → ~5ms (80-90% schneller)")
print("  - FPS: 6 → 10+")
print("  - Flimmer-Problem: behoben")
