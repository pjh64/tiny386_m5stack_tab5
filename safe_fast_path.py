#!/usr/bin/env python3
"""
Fügt Fast-Path NACH addr-Berechnung und VOR x-Schleife ein
"""

with open('vga.c', 'r') as f:
    content = f.read()

# 1. Fast-Path-Funktion am Anfang einfügen (nach Includes)
fast_path_func = '''
/* Fast-Path für 8bpp Planar VGA (shift_control == 0, plane_mask != 1) */
static void vga_draw_8bpp_planar_fast(
    uint8_t *vram, uint32_t addr, uint32_t *palette,
    uint16_t *fb_data, int fb_width, int i0, int y, int w)
{
    /* 8-Pixel-Batching: Lade 4 Bytes, extrahiere 8 Pixel parallel */
    for (int x = 0; x < w; x += 8) {
        uint32_t addr_byte = addr + 4 * (x >> 3);
        uint8_t p0 = vram[addr_byte];
        uint8_t p1 = vram[addr_byte + 1];
        uint8_t p2 = vram[addr_byte + 2];
        uint8_t p3 = vram[addr_byte + 3];
        
        int base_i = 2 * (y * fb_width + x) + i0;
        
        /* 8 Pixel parallel extrahieren */
        for (int bit = 7; bit >= 0; bit--) {
            int k = ((p0 >> bit) & 1) |
                    (((p1 >> bit) & 1) << 1) |
                    (((p2 >> bit) & 1) << 2) |
                    (((p3 >> bit) & 1) << 3);
            
            uint16_t color = palette[k] & 0xFFFF;
            fb_data[base_i + (7 - bit)] = color;
        }
    }
}

'''

insert_pos = content.find('\n\n', content.find('#include "vga.h"'))
if insert_pos > 0:
    content = content[:insert_pos+2] + fast_path_func + content[insert_pos+2:]

# 2. Fast-Path-Aufruf VOR der x-Schleife
# Suche: "uint32_t color_comp = 0;" nach addr-Berechnung
marker = '''        uint32_t color_comp = 0;
        for (int x = 0; x < w; x++) {'''

if marker in content:
    fast_call = '''        uint32_t color_comp = 0;
        
        /* Fast-Path für 8bpp Planar (Mode 12 etc.) */
        if (shift_control == 0 && xdiv == 1 && plane_mask != 1 && !s->comp_ntsc && w % 8 == 0) {
            vga_draw_8bpp_planar_fast(vram, addr, palette, (uint16_t*)fb_dev->fb_data, 
                                       fb_dev->width, i0, y, w);
        } else {
        
        for (int x = 0; x < w; x++) {'''
    
    content = content.replace(marker, fast_call, 1)
    
    # Finde das Ende der x-Schleife und füge schließende Klammer ein
    # Suche nach der y-Schleifen-Endlogik
    end_marker = '''        if (!multi_run) {
            int mask = (s->cr[0x17] & 3) ^ 3;'''
    
    if end_marker in content:
        content = content.replace(end_marker, '''        } // end of else (fast path fallback)
        ''' + end_marker, 1)
        print("✓ Fast-Path-Funktion hinzugefügt")
        print("✓ Fast-Path-Aufruf vor x-Schleife eingefügt")
        print("✓ Schließende Klammer für else-Block hinzugefügt")

with open('vga.c', 'w') as f:
    f.write(content)
