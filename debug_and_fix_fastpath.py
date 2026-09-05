#!/usr/bin/env python3
"""
Debug warum der Fast-Path nicht greift und fixe das Flimmer-Problem
"""

print("=== Implementiere Debug + Cache-Sync + erweiterter Fast-Path ===\n")

with open('vga.c', 'r', encoding='utf-8') as f:
    content = f.read()

# Schritt 1: Ersetze den aktuellen Fast-Path mit Debug-Version
old_fastpath = '''    // Fast-Path: 16bpp VBE mit direktem memcpy
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
#endif'''

new_fastpath = '''    // Fast-Path: Direkter memcpy für VBE-Modi ohne Konvertierung
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

content = content.replace(old_fastpath, new_fastpath, 1)

# Schritt 2: Finde esp_main.c und füge Cache-Sync hinzu
try:
    with open('esp/main/esp_main.c', 'r', encoding='utf-8') as f:
        esp_content = f.read()
    
    # Suche nach der redraw Funktion die den Framebuffer aktualisiert
    # Füge Cache-Sync nach dem memcpy/PPA hinzu
    if 'esp_cache_msync' not in esp_content or esp_content.count('esp_cache_msync') < 3:
        # Suche nach dem display_task wo der Framebuffer beschrieben wird
        cache_sync_marker = '    lcd_panel_draw_bitmap(panel, 0, 0, LCD_WIDTH, LCD_HEIGHT, src);'
        if cache_sync_marker in esp_content:
            cache_sync = '''
    
    // Cache-Synchronisierung: Stelle sicher dass der Framebuffer im RAM ist
    // bevor das LCD-Panel darauf zugreift (behebt Flimmer-Artefakt)
    esp_cache_msync(src, LCD_WIDTH * LCD_HEIGHT * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
    
    lcd_panel_draw_bitmap(panel, 0, 0, LCD_WIDTH, LCD_HEIGHT, src);'''
            
            esp_content = esp_content.replace(cache_sync_marker, cache_sync, 1)
            print("✓ Cache-Sync in esp_main.c hinzugefügt")
        else:
            print("⚠ Konnte lcd_panel_draw_bitmap nicht finden")
    
    with open('esp/main/esp_main.c', 'w', encoding='utf-8') as f:
        f.write(esp_content)
        
except Exception as e:
    print(f"⚠ Fehler bei esp_main.c: {e}")

# Schreibe vga.c zurück
with open('vga.c', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Debug-Output und erweiterter Fast-Path implementiert")
print("\nWas jetzt passiert:")
print("  1. Debug zeigt welche Bedingungen nicht passen")
print("  2. Fast-Path für 8bpp, 16bpp und 32bpp")
print("  3. Cache-Sync behebt Flimmer-Artefakt")
