#!/usr/bin/env python3
"""
Implementiert einen 16bpp Fast-Path für vga_graphic_refresh.

Wenn VBE aktiv ist und der Gast 16bpp verwendet, können wir ganze Zeilen
mit memcpy kopieren statt Pixel-für-Pixel zu konvertieren.

Dies sollte vga_step von 42ms auf ~5-10ms reduzieren.
"""

print("=== Implementiere 16bpp Fast-Path ===\n")

with open('vga.c', 'r', encoding='utf-8') as f:
    content = f.read()

# Finde die for-Schleife in vga_graphic_refresh
for_loop_marker = '    for (int y = 0; y < h; y++) {'
if for_loop_marker not in content:
    print("✗ FEHLER: for-Schleife nicht gefunden")
    exit(1)

# Erstelle den Fast-Path Code
fast_path_code = '''    // Fast-Path: 16bpp VBE mit direktem memcpy
    // Bedingungen: VBE aktiv, 16bpp Gast, 16bpp Ziel, keine komplexe Skalierung
#if BPP == 16
    if (vbe_enabled(s) && bpp == 16 && 
        (s->cr[0x17] & 3) == 3 &&  // Normaler addressing mode
        multi_scan == 0 &&          // Kein double scan
        xdiv == 1) {                // Kein pixel division
        
        // Berechne Start-Adresse im VGA-RAM
        uint32_t src_offset = 4 * start_addr;
        
        // Kopiere ganze Zeilen mit memcpy
        for (int y = 0; y < h; y++) {
            uint8_t *src = vram + src_offset + y * line_offset;
            uint8_t *dst = fb_dev->fb_data + i0 + y * fb_dev->stride;
            memcpy(dst, src, w * 2);  // 2 bytes per pixel (16bpp)
        }
        
        redraw_func(opaque, 0, 0, fb_dev->width, fb_dev->height);
        return;
    }
#endif
    
'''

# Füge den Fast-Path vor der for-Schleife ein
content = content.replace(for_loop_marker, fast_path_code + for_loop_marker, 1)

# Schreibe die Datei zurück
with open('vga.c', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 16bpp Fast-Path implementiert")
print("\nWas der Fast-Path macht:")
print("  - Prüft ob VBE + 16bpp + einfache Bedingungen")
print("  - Wenn ja: memcpy ganze Zeilen (sehr schnell)")
print("  - Wenn nein: Original langsame Schleife (Fallback)")
print("\nErwartete Verbesserung:")
print("  - vga_step: 42ms → ~5-10ms (bei 16bpp)")
print("  - Kein Risiko: Fallback auf Original-Code wenn Bedingungen nicht passen")
