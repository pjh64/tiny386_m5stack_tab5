#!/usr/bin/env python3
"""
Entfernt Debug-Output und optimiert den Fast-Path
"""

print("=== Entferne Debug und optimiere Fast-Path ===\n")

with open('vga.c', 'r', encoding='utf-8') as f:
    content = f.read()

# Schritt 1: Entferne Debug-Output und optimiere Fast-Path
old_code = '''    // Fast-Path: Direkter memcpy für VBE-Modi ohne Konvertierung
#if BPP == 16
    if (vbe_enabled(s)) {
        // Debug: Zeige aktuelle Bedingungen
        static int debug_count = 0;
        if (debug_count++ < 5) {
            fprintf(stderr, "Fast-Path check: bpp=%d, cr17=%d, multi_scan=%d, xdiv=%d\\n",
                    bpp, s->cr[0x17] & 3, multi_scan, xdiv);
        }
        
        // 8bpp Fast-Path: Palette-Lookup pro Zeile
        if (bpp == 8 && (s->cr[0x17] & 3) == 3 && multi_scan == 0 && xdiv == 1) {
            uint32_t src_offset = 4 * start_addr;
            for (int y = 0; y < h; y++) {
                uint8_t *src = vram + src_offset + y * line_offset;
                uint16_t *dst = (uint16_t*)(fb_dev->fb_data + i0 + y * fb_dev->stride);
                for (int x = 0; x < w; x++) {
                    dst[x] = (uint16_t)palette[src[x]];
                }
            }
            redraw_func(opaque, 0, 0, fb_dev->width, fb_dev->height);
            return;
        }
        
        // 16bpp Fast-Path: Direkter memcpy
        if (bpp == 16 && (s->cr[0x17] & 3) == 3 && multi_scan == 0 && xdiv == 1) {
            uint32_t src_offset = 4 * start_addr;
            for (int y = 0; y < h; y++) {
                uint8_t *src = vram + src_offset + y * line_offset;
                uint8_t *dst = fb_dev->fb_data + i0 + y * fb_dev->stride;
                memcpy(dst, src, w * 2);
            }
            redraw_func(opaque, 0, 0, fb_dev->width, fb_dev->height);
            return;
        }
        
        // 32bpp Fast-Path: Konvertiere zu 16bpp
        if (bpp == 32 && (s->cr[0x17] & 3) == 3 && multi_scan == 0 && xdiv == 1) {
            uint32_t src_offset = 4 * start_addr;
            for (int y = 0; y < h; y++) {
                uint32_t *src = (uint32_t*)(vram + src_offset + y * line_offset);
                uint16_t *dst = (uint16_t*)(fb_dev->fb_data + i0 + y * fb_dev->stride);
                for (int x = 0; x < w; x++) {
                    uint32_t c = src[x];
                    dst[x] = ((c >> 3) & 0x1f) | (((c >> 10) & 0x3f) << 5) | (((c >> 19) & 0x1f) << 11);
                }
            }
            redraw_func(opaque, 0, 0, fb_dev->width, fb_dev->height);
            return;
        }
    }
#endif'''

new_code = '''    // Fast-Path: Direkte Konvertierung für VBE-Modi (ohne Debug-Output)
#if BPP == 16
    if (vbe_enabled(s) && (s->cr[0x17] & 3) == 3 && multi_scan == 0 && xdiv == 1) {
        uint32_t src_offset = 4 * start_addr;
        
        // 8bpp Fast-Path: Palette-Lookup
        if (bpp == 8) {
            for (int y = 0; y < h; y++) {
                uint8_t *src = vram + src_offset + y * line_offset;
                uint16_t *dst = (uint16_t*)(fb_dev->fb_data + i0 + y * fb_dev->stride);
                for (int x = 0; x < w; x++) {
                    dst[x] = (uint16_t)palette[src[x]];
                }
            }
            redraw_func(opaque, 0, 0, fb_dev->width, fb_dev->height);
            return;
        }
        
        // 16bpp Fast-Path: Direkter memcpy
        if (bpp == 16) {
            for (int y = 0; y < h; y++) {
                uint8_t *src = vram + src_offset + y * line_offset;
                uint8_t *dst = fb_dev->fb_data + i0 + y * fb_dev->stride;
                memcpy(dst, src, w * 2);
            }
            redraw_func(opaque, 0, 0, fb_dev->width, fb_dev->height);
            return;
        }
        
        // 32bpp Fast-Path: Konvertiere zu 16bpp
        if (bpp == 32) {
            for (int y = 0; y < h; y++) {
                uint32_t *src = (uint32_t*)(vram + src_offset + y * line_offset);
                uint16_t *dst = (uint16_t*)(fb_dev->fb_data + i0 + y * fb_dev->stride);
                for (int x = 0; x < w; x++) {
                    uint32_t c = src[x];
                    dst[x] = ((c >> 3) & 0x1f) | (((c >> 10) & 0x3f) << 5) | (((c >> 19) & 0x1f) << 11);
                }
            }
            redraw_func(opaque, 0, 0, fb_dev->width, fb_dev->height);
            return;
        }
    }
#endif'''

content = content.replace(old_code, new_code, 1)

# Schreibe zurück
with open('vga.c', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Debug entfernt und Fast-Path optimiert")
print("\nWas geändert wurde:")
print("  - Debug-Output entfernt (fprintf ist langsam)")
print("  - Bedingungen zusammengefasst")
print("  - Fast-Path sollte jetzt schneller sein")
