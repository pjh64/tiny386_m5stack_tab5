#!/usr/bin/env python3
"""
Fügt eine spezialisierte Fast-Path-Funktion hinzu, die nur unter bestimmten
Bedingungen aufgerufen wird - ohne die bestehende Schleifenstruktur zu brechen.
"""

with open('vga.c', 'r') as f:
    content = f.read()

# 1. Fast-Path-Funktion am Anfang der Datei einfügen (nach den Includes)
fast_path_func = '''
/* Fast-Path für 4bpp Planar VGA Modi (shift_control == 0 oder 1) */
static void vga_draw_4bpp_planar_fast(
    uint8_t *vram, uint32_t addr, uint32_t *palette,
    uint16_t *fb_data, int fb_width, int i0, int x0, int y, int w, int bpp_out)
{
    /* 8-Pixel-Batching: Lade 4 Bytes, extrahiere 8 Pixel parallel */
    for (int x = 0; x < w; x += 8) {
        uint32_t addr_byte = addr + 4 * (x >> 3);
        uint8_t p0 = vram[addr_byte];
        uint8_t p1 = vram[addr_byte + 1];
        uint8_t p2 = vram[addr_byte + 2];
        uint8_t p3 = vram[addr_byte + 3];
        
        int base_i = (bpp_out / 8) * (y * fb_width + x0 + x);
        
        /* 8 Pixel parallel extrahieren */
        for (int bit = 7; bit >= 0; bit--) {
            int k = ((p0 >> bit) & 1) |
                    (((p1 >> bit) & 1) << 1) |
                    (((p2 >> bit) & 1) << 2) |
                    (((p3 >> bit) & 1) << 3);
            
            uint32_t color = palette[k];
            int i = base_i + (bpp_out / 8) * (7 - bit);
            
            if (bpp_out == 16) {
                fb_data[i] = color & 0xFFFF;
            } else if (bpp_out == 32) {
                fb_data[i] = color;
            }
        }
    }
}

'''

# Nach den Includes einfügen
insert_pos = content.find('\n\n', content.find('#include'))
if insert_pos > 0:
    content = content[:insert_pos+2] + fast_path_func + content[insert_pos+2:]

# 2. Aufruf in der Grafik-Refresh-Schleife vor dem normalen Pfad
# Suche: "if (shift_control == 0 || shift_control == 1)"
marker = 'if (shift_control == 0 || shift_control == 1) {'
if marker in content:
    # Finde die Stelle und füge davor den Fast-Path-Check ein
    call_code = '''        /* Fast-Path für 4bpp Planar */
        if ((shift_control == 0) && xdiv == 1 && !s->comp_ntsc) {
            vga_draw_4bpp_planar_fast(
                vram, addr, palette, (uint16_t*)fb_dev->fb_data, 
                fb_dev->width, i0, x0, y, w, BPP);
        } else '''
    
    content = content.replace(marker, call_code + marker, 1)
    print("✓ Fast-Path-Funktion hinzugefügt")
    print("✓ Fast-Path-Aufruf vor Standard-Schleife eingefügt")

with open('vga.c', 'w') as f:
    f.write(content)
