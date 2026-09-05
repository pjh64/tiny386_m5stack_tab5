#!/usr/bin/env python3
"""
Fix für Cache-Line-Ausrichtung
"""

print("=== Fix Cache-Line-Ausrichtung ===\n")

with open('esp/main/esp_main.c', 'r', encoding='utf-8') as f:
    content = f.read()

# Ersetze den Cache-Sync VOR PPA mit korrekter Ausrichtung
old_sync_before = '''		// Cache-Synchronisierung VOR PPA: Stelle sicher dass der gesamte
		// Quell-Framebuffer im RAM ist (behebt Flimmer-Artefakt)
		esp_cache_msync(src, LCD_WIDTH * LCD_HEIGHT * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);'''

new_sync_before = '''		// Cache-Synchronisierung VOR PPA mit korrekter Ausrichtung
		{
			uint32_t addr = (uint32_t)src;
			uint32_t aligned_addr = addr & ~0x7F;  // Auf 128 Bytes abrunden
			uint32_t size = LCD_WIDTH * LCD_HEIGHT * 2;
			uint32_t aligned_size = (size + 0x7F) & ~0x7F;  // Auf 128 Bytes aufrunden
			esp_cache_msync((void*)aligned_addr, aligned_size, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
		}'''

content = content.replace(old_sync_before, new_sync_before, 1)
print("✓ Cache-Sync VOR PPA mit Ausrichtung ersetzt")

# Ersetze den Cache-Sync NACH PPA mit korrekter Ausrichtung
old_sync_after = '''		// Cache-Synchronisierung NACH PPA: Stelle sicher dass der gesamte
		// Ziel-Framebuffer im RAM ist bevor das LCD-Panel liest
		esp_cache_msync(out_buf, LCD_WIDTH * LCD_HEIGHT * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);'''

new_sync_after = '''		// Cache-Synchronisierung NACH PPA mit korrekter Ausrichtung
		{
			uint32_t addr = (uint32_t)out_buf;
			uint32_t aligned_addr = addr & ~0x7F;  // Auf 128 Bytes abrunden
			uint32_t size = LCD_WIDTH * LCD_HEIGHT * 2;
			uint32_t aligned_size = (size + 0x7F) & ~0x7F;  // Auf 128 Bytes aufrunden
			esp_cache_msync((void*)aligned_addr, aligned_size, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
		}'''

content = content.replace(old_sync_after, new_sync_after, 1)
print("✓ Cache-Sync NACH PPA mit Ausrichtung ersetzt")

# Schreibe zurück
with open('esp/main/esp_main.c', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✓✓✓ Cache-Line-Ausrichtung implementiert! ✓✓✓")
print("\nWas das Fix macht:")
print("  - Adresse auf 128 Bytes abgerundet")
print("  - Größe auf 128 Bytes aufgerundet")
print("  - Sollte die Alignment-Fehler beheben")
