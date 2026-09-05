#!/usr/bin/env python3
"""
Fügt den 32bpp -> 16bpp Fast-Path in vga_graphic_refresh ein
"""

with open('vga.c', 'r') as f:
    lines = f.readlines()

# Finde die Zeile mit "uint32_t plane_mask = s->ar[0x12];"
insert_idx = None
for i, line in enumerate(lines):
    if 'uint32_t plane_mask = s->ar[0x12];' in line:
        insert_idx = i + 1
        break

if insert_idx is None:
    print("FEHLER: Zeile nicht gefunden!")
    exit(1)

fastpath_code = '''
#if BPP == 16
    /* Fast-Path fuer 32bpp VBE-Modi: konvertiere zu 16bpp RGB565 */
    if (shift_control == 2 && bpp == 32 && xdiv == 1 && 
        (s->cr[0x17] & 1) && (s->cr[0x17] & 2)) {
        int64_t t_start = esp_timer_get_time();
        
        for (int y = 0; y < h; y++) {
            uint32_t *src = (uint32_t*)(vram + addr1 + y * line_offset);
            uint16_t *dst = (uint16_t*)(fb_dev->fb_data + i0 + y * fb_dev->stride);
            for (int x = 0; x < w; x++) {
                uint32_t c = src[x];
                dst[x] = ((c >> 3) & 0x1f) | ((c >> 10) & 0x3f) << 5 | ((c >> 19) & 0x1f) << 11;
            }
        }
        
        static int64_t t_fastpath_total = 0;
        static int fastpath_count = 0;
        t_fastpath_total += (esp_timer_get_time() - t_start);
        fastpath_count++;
        if (fastpath_count >= 100) {
            fprintf(stderr, "FASTPATH avg=%lldus\\n", (long long)(t_fastpath_total / 100));
            t_fastpath_total = 0;
            fastpath_count = 0;
        }
        
        redraw_func(opaque, 0, 0, fb_dev->width, fb_dev->height);
        return;
    }
#endif

'''

lines.insert(insert_idx, fastpath_code)

with open('vga.c', 'w') as f:
    f.writelines(lines)

print(f"Fast-Path bei Zeile {insert_idx} eingefügt")
