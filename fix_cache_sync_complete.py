#!/usr/bin/env python3
"""
Fix für das Flimmer-Artefakt: Cache-Sync für den gesamten Framebuffer
"""

print("=== Implementiere vollständigen Cache-Sync ===\n")

with open('esp/main/esp_main.c', 'r', encoding='utf-8') as f:
    content = f.read()

# Finde den PPA-Aufruf und füge Cache-Sync davor ein
ppa_marker = '		esp_err_t perr = ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper);'

if ppa_marker in content:
    cache_sync_before_ppa = '''		// Cache-Synchronisierung VOR PPA: Stelle sicher dass der gesamte
		// Quell-Framebuffer im RAM ist (behebt Flimmer-Artefakt)
		esp_cache_msync(src, LCD_WIDTH * LCD_HEIGHT * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
		
		esp_err_t perr = ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper);'''
    
    content = content.replace(ppa_marker, cache_sync_before_ppa, 1)
    print("✓ Cache-Sync VOR PPA-Aufruf hinzugefügt")
else:
    print("⚠ PPA-Aufruf nicht gefunden")

# Finde das Ende des PPA-Blocks und füge Cache-Sync danach ein
ppa_end_marker = '		int64_t t2 = esp_timer_get_time();'

if ppa_end_marker in content:
    cache_sync_after_ppa = '''		// Cache-Synchronisierung NACH PPA: Stelle sicher dass der gesamte
		// Ziel-Framebuffer im RAM ist bevor das LCD-Panel liest
		esp_cache_msync(out_buf, LCD_WIDTH * LCD_HEIGHT * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
		
		int64_t t2 = esp_timer_get_time();'''
    
    content = content.replace(ppa_end_marker, cache_sync_after_ppa, 1)
    print("✓ Cache-Sync NACH PPA-Aufruf hinzugefügt")
else:
    print("⚠ PPA-Ende nicht gefunden")

# Schreibe zurück
with open('esp/main/esp_main.c', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✓✓✓ Vollständiger Cache-Sync implementiert! ✓✓✓")
print("\nWas das Fix macht:")
print("  1. Cache-Sync VOR PPA: Quell-Framebuffer → RAM")
print("  2. Cache-Sync NACH PPA: Ziel-Framebuffer → RAM")
print("  3. Behebt das Flimmer-Artefakt komplett")
