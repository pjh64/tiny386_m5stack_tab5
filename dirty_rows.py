#!/usr/bin/env python3
with open('vga.c', 'r') as f:
    c = f.read()

# 1. Dirty-Tracking-Setup vor der y-Schleife
old1 = '''    uint32_t plane_mask = s->ar[0x12];
    for (int y = 0; y < h; y++) {'''
new1 = '''    uint32_t plane_mask = s->ar[0x12];

    /* Dirty-Row-Tracking: nur geaenderte Zeilen konvertieren */
    static uint8_t *shadow = NULL;
    static uint32_t shadow_len = 0;
    static int shadow_valid = 0;
    static uint32_t last_pal[16];
    static uint32_t last_geo = 0;
    int fast_ok = (shift_control == 0 && xdiv == 1 && plane_mask != 1 &&
                   !s->comp_ntsc && w % 8 == 0 && (s->cr[0x17] & 3) == 3);
    int full = 1;
    uint32_t rowbytes = (w / 8) * 4;
    if (fast_ok) {
        if (!shadow) { shadow_len = 512 * 1024; shadow = malloc(shadow_len); }
        uint32_t geo = ((uint32_t)w << 16) ^ h ^ (line_offset << 4) ^ addr1;
        if (shadow && (memcmp(palette, last_pal, 16 * 4) != 0 || geo != last_geo)) {
            memcpy(last_pal, palette, 16 * 4);
            last_geo = geo;
            shadow_valid = 0;
        }
        if (shadow && !shadow_valid) { shadow_valid = 1; full = 1; }
        else if (shadow) full = 0;
    } else {
        shadow_valid = 0;
    }

    for (int y = 0; y < h; y++) {'''
assert c.count(old1) == 1
c = c.replace(old1, new1, 1)

# 2. Fast-Path-Aufruf mit Dirty-Check pro Zeile
old2 = '''#if BPP == 16
        if (fast_ok) {
            vga_draw_8bpp_planar_fast(vram, addr, palette, fb_dev->fb_data,
                                       fb_dev->width, i0, y, w);
        } else
#endif
        {'''
new2 = '''#if BPP == 16
        if (fast_ok && shadow) {
            if (full || addr + rowbytes > shadow_len ||
                memcmp(vram + addr, shadow + addr, rowbytes) != 0) {
                vga_draw_8bpp_planar_fast(vram, addr, palette, fb_dev->fb_data,
                                           fb_dev->width, i0, y, w);
                if (addr + rowbytes <= shadow_len)
                    memcpy(shadow + addr, vram + addr, rowbytes);
            }
        } else
#endif
        {'''
assert c.count(old2) == 1, "Fast-Path-Aufruf nicht gefunden"
c = c.replace(old2, new2, 1)

with open('vga.c', 'w') as f:
    f.write(c)
print("OK: Dirty-Row-Tracking aktiv")
