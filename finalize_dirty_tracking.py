#!/usr/bin/env python3

print("=== Finalisiere Dirty-Tracking ===\n")

with open('vga.c', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Schritt 1: Ersetze for-Schleife bei Zeile 1112 (Index 1111)
print("Schritt 1: Ersetze for-Schleife bei Zeile 1112...")
if 'for (int y = 0; y < h; y++)' in lines[1111]:
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
    lines[1111] = optimized_loop
    print("  ✓ for-Schleife mit Dirty-Check ersetzt")
else:
    print(f"  ✗ FEHLER: Erwartete for-Schleife nicht gefunden")
    print(f"  Zeile 1112 enthält: {lines[1111].strip()}")
    exit(1)

# Schritt 2: Füge Dirty-Reset vor redraw_func bei Zeile 1286 (Index 1285) ein
print("\nSchritt 2: Füge Dirty-Reset vor redraw_func ein...")
reset_dirty = '''    // Clear dirty flags for processed lines
    if (!full_update && s->dirty_lines) {
        int max_lines = (h < s->dirty_lines_size) ? h : s->dirty_lines_size;
        memset(s->dirty_lines, 0, max_lines);
    }
    
'''

if 'redraw_func(opaque, 0, 0, fb_dev->width, fb_dev->height);' in lines[1285]:
    lines.insert(1285, reset_dirty)
    print("  ✓ Dirty-Reset vor redraw_func eingefügt")
else:
    print(f"  ✗ FEHLER: Erwarteter redraw_func Aufruf nicht gefunden")
    print(f"  Zeile 1286 enthält: {lines[1285].strip()}")
    exit(1)

# Schreibe die Datei zurück
with open('vga.c', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n=== ✓✓✓ Dirty-Tracking komplett implementiert! ✓✓✓ ===")
print("\nZusammenfassung aller Änderungen:")
print("  1. ✓ dirty_lines Felder in VGAState (Zeilen 162-163)")
print("  2. ✓ Initialisierung in vga_init (Zeilen 2164-2166)")
print("  3. ✓ mark_line_dirty Funktion vor vga_mem_write")
print("  4. ✓ mark_line_dirty Aufruf in vga_mem_write")
print("  5. ✓ Optimierte for-Schleife mit Dirty-Check")
print("  6. ✓ Dirty-Reset vor redraw_func")
print("\nErwartete Verbesserungen:")
print("  - vga_step: 42ms → ~5ms (80-90% schneller)")
print("  - FPS: 6 → 10+")
