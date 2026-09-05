#!/usr/bin/env python3
with open('vga.c', 'r') as f:
    c = f.read()

# 1. Neue Fast-Funktion fuer 8bpp linear neben der planar-Funktion
old_fn = '/* Fast-Path für 8bpp Planar VGA (shift_control == 0, plane_mask != 1) */'
new_fn = '''/* Fast-Path für 8bpp linear/chunky (shift_control == 2, bpp == 8) */
static void vga_draw_8bpp_linear_fast(
    uint8_t *vram, uint32_t addr, uint32_t *palette,
    uint8_t *fb_data, int fb_width, int i0, int y, int w, int xdiv)
{
    const uint8_t *src = vram + addr;
    int base_i = 2 * (y * fb_width) + i0;
    for (int x = 0; x < w; x++) {
        uint16_t color = palette[src[x / xdiv]] & 0xFFFF;
        int i = base_i + 2 * x;
        fb_data[i] = color & 0xFF;
        fb_data[i + 1] = color >> 8;
    }
}

/* Fast-Path für 8bpp Planar VGA (shift_control == 0, plane_mask != 1) */'''
assert c.count(old_fn) == 1
c = c.replace(old_fn, new_fn, 1)

# 2. Dirty-Block generalisieren (planar + linear)
old_block = '''    int fast_ok = (shift_control == 0 && xdiv == 1 && plane_mask != 1 &&
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
    }'''
new_block = '''    int fast_ok = 0;
    uint32_t rowbytes = 0, pal_bytes = 0;
    if ((s->cr[0x17] & 3) == 3 && !s->comp_ntsc) {
        if (shift_control == 0 && xdiv == 1 && plane_mask != 1 && w % 8 == 0) {
            fast_ok = 1; rowbytes = (w / 8) * 4; pal_bytes = 16 * 4;
        } else if (shift_control == 2 && bpp == 8) {
            fast_ok = 2; rowbytes = w / xdiv; pal_bytes = 256 * 4;
        }
    }
    int full = 1;
    if (fast_ok) {
        if (!shadow) { shadow_len = 512 * 1024; shadow = malloc(shadow_len); }
        uint32_t geo = ((uint32_t)w << 16) ^ h ^ (line_offset << 4) ^ addr1 ^ ((uint32_t)fast_ok << 24);
        if (shadow && (memcmp(palette, last_pal, pal_bytes) != 0 || geo != last_geo)) {
            memcpy(last_pal, palette, pal_bytes);
            last_geo = geo;
            shadow_valid = 0;
        }
        if (shadow && !shadow_valid) { shadow_valid = 1; full = 1; }
        else if (shadow) full = 0;
    } else {
        shadow_valid = 0;
    }'''
assert c.count(old_block) == 1
c = c.replace(old_block, new_block, 1)

# 3. last_pal auf 256 Eintraege vergroessern
old_pal = '    static uint32_t last_pal[16];'
new_pal = '    static uint32_t last_pal[256];'
assert c.count(old_pal) == 1
c = c.replace(old_pal, new_pal, 1)

# 4. Aufruf: planar vs linear unterscheiden
old_call = '''        if (fast_ok && shadow) {
            if (full || addr + rowbytes > shadow_len ||
                memcmp(vram + addr, shadow + addr, rowbytes) != 0) {
                vga_draw_8bpp_planar_fast(vram, addr, palette, fb_dev->fb_data,
                                           fb_dev->width, i0, y, w);
                if (addr + rowbytes <= shadow_len)
                    memcpy(shadow + addr, vram + addr, rowbytes);
            }
        } else'''
new_call = '''        if (fast_ok && shadow) {
            if (full || addr + rowbytes > shadow_len ||
                memcmp(vram + addr, shadow + addr, rowbytes) != 0) {
                if (fast_ok == 1)
                    vga_draw_8bpp_planar_fast(vram, addr, palette, fb_dev->fb_data,
                                               fb_dev->width, i0, y, w);
                else
                    vga_draw_8bpp_linear_fast(vram, addr, palette, fb_dev->fb_data,
                                               fb_dev->width, i0, y, w, xdiv);
                if (addr + rowbytes <= shadow_len)
                    memcpy(shadow + addr, vram + addr, rowbytes);
            }
        } else'''
assert c.count(old_call) == 1
c = c.replace(old_call, new_call, 1)

with open('vga.c', 'w') as f:
    f.write(c)
print("OK: 8bpp-linear Fast-Path + Dirty-Tracking erweitert")
