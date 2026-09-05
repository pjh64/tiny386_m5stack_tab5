#!/usr/bin/env python3
with open('vga.c', 'r') as f:
    c = f.read()

# 1. Funktion: uint16_t* -> uint8_t* (Byte-Indizes wie im Original)
old_sig = 'uint16_t *fb_data, int fb_width, int i0, int y, int w)'
new_sig = 'uint8_t *fb_data, int fb_width, int i0, int y, int w)'
assert c.count(old_sig) == 1
c = c.replace(old_sig, new_sig, 1)

# 2. Store: uint16-Write an Byte-Offset -> zwei Byte-Writes an korrektem Index
old_store = '''            uint16_t color = palette[k] & 0xFFFF;
            fb_data[base_i + (7 - bit)] = color;'''
new_store = '''            uint16_t color = palette[k] & 0xFFFF;
            int i = base_i + 2 * (7 - bit);
            fb_data[i] = color & 0xFF;
            fb_data[i + 1] = color >> 8;'''
assert c.count(old_store) == 1
c = c.replace(old_store, new_store, 1)

# 3. Aufruf: Cast entfernen + BPP-Guard
old_call = '''        /* Fast-Path für 8bpp Planar (Mode 12 etc.) */
        if (shift_control == 0 && xdiv == 1 && plane_mask != 1 && !s->comp_ntsc && w % 8 == 0) {
            vga_draw_8bpp_planar_fast(vram, addr, palette, (uint16_t*)fb_dev->fb_data, 
                                       fb_dev->width, i0, y, w);
        } else {'''
new_call = '''        /* Fast-Path für 8bpp Planar (Mode 12 etc.) */
#if BPP == 16
        if (shift_control == 0 && xdiv == 1 && plane_mask != 1 && !s->comp_ntsc && w % 8 == 0) {
            vga_draw_8bpp_planar_fast(vram, addr, palette, fb_dev->fb_data,
                                       fb_dev->width, i0, y, w);
        } else
#endif
        {'''
assert c.count(old_call) == 1
c = c.replace(old_call, new_call, 1)

with open('vga.c', 'w') as f:
    f.write(c)
print("OK: Out-of-Bounds-Fix im Fast-Path (uint8_t* + Byte-Indizes + BPP-Guard)")
