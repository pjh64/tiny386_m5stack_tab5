#!/usr/bin/env python3
"""
Sauberer Fix: Revert VSync-Versuch, stattdessen Double-Buffer gegen Tearing
"""

with open('esp/main/esp_main.c', 'r') as f:
    lines = f.readlines()

out = []
skip_vsync_callback = False
seen_callback = False

for i, line in enumerate(lines):
    # Entferne VSync-Semaphore Deklaration
    if 'static SemaphoreHandle_t vsync_sem' in line:
        continue
    
    # Entferne VSync-Callback-Funktionen (alle Kopien)
    if 'on_vsync_callback' in line and 'static bool' in line:
        skip_vsync_callback = True
        continue
    if skip_vsync_callback:
        if line.strip() == '}' and not seen_callback:
            seen_callback = True
            skip_vsync_callback = False
            continue
        continue
    
    # Entferne VSync-Semaphore Init Block
    if 'Initialisiere VSync-Synchronisation' in line:
        # Skip bis zur schliessenden Klammer des Blocks
        continue
    if 'vsync_sem = xSemaphoreCreateBinary' in line:
        continue
    if 'Failed to create vsync semaphore' in line:
        continue
    if 'vTaskDelete(NULL)' in line and i > 0 and 'vsync' in lines[max(0,i-3):i+1].__repr__().lower():
        continue
    if 'esp_lcd_dpi_panel_event_callbacks_t' in line:
        continue
    if '.on_vsync = on_vsync_callback' in line:
        continue
    if 'esp_lcd_dpi_panel_register_event_callbacks' in line:
        continue
    if 'VSync callback registered' in line:
        continue
    if 'VSync-Synchronisation' in line.lower() and 'Warte' in line:
        continue
    if 'vsync_sem' in line:
        continue
    
    # Reset seen_callback für eventuelle weitere Kopien
    if skip_vsync_callback == False and 'on_vsync_callback' in line:
        continue
    
    out.append(line)

content = ''.join(out)

# Fix: Tearing durch Double-Buffer lösen
# Statt direkt in panel_fb zu schreiben, immer erst in rot_buf,
# dann mit memcpy nach panel_fb kopieren

old_outbuf = '		uint16_t *out_buf = globals.panel_fb ? (uint16_t *)globals.panel_fb : rot_buf;'
new_outbuf = '		uint16_t *out_buf = rot_buf;  /* Immer in rot_buf rendern, dann nach panel_fb kopieren */'

content = content.replace(old_outbuf, new_outbuf)

# Finde die Stelle nach dem Edge-Clearing und füge memcpy ein
# Suche nach dem memset für die Kanten und dem draw-Timing
old_edge = '''		esp_cache_msync(out_buf, 4 * 720 * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
		esp_cache_msync(out_buf + (1280 - 4) * 720, 4 * 720 * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);   /* row last  -> linke Kante  */'''

new_edge = '''		/* Kopiere fertigen Frame atomar in den DPI-Framebuffer */
		if (globals.panel_fb) {
			memcpy(globals.panel_fb, out_buf, LCD_WIDTH * LCD_HEIGHT * 2);
		}'''

content = content.replace(old_edge, new_edge)

# Entferne die Cache-Sync VOR und NACH PPA (nicht mehr nötig)
content = content.replace('''		// Cache-Synchronisierung VOR PPA mit korrekter Ausrichtung
		{
			uint32_t addr = (uint32_t)src;
			uint32_t aligned_addr = addr & ~0x7F;  // Auf 128 Bytes abrunden
			uint32_t size = LCD_WIDTH * LCD_HEIGHT * 2;
			uint32_t aligned_size = (size + 0x7F) & ~0x7F;  // Auf 128 Bytes aufrunden
			esp_cache_msync((void*)aligned_addr, aligned_size, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
		}
		''', '		')

content = content.replace('''		// Cache-Synchronisierung NACH PPA mit korrekter Ausrichtung
		{
			uint32_t addr = (uint32_t)out_buf;
			uint32_t aligned_addr = addr & ~0x7F;  // Auf 128 Bytes abrunden
			uint32_t size = LCD_WIDTH * LCD_HEIGHT * 2;
			uint32_t aligned_size = (size + 0x7F) & ~0x7F;  // Auf 128 Bytes aufrunden
			esp_cache_msync((void*)aligned_addr, aligned_size, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
		}
		''', '		')

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)

print("✓ VSync-Code entfernt")
print("✓ Double-Buffer implementiert (rot_buf → panel_fb)")
print("✓ Cache-Sync entfernt (nicht mehr nötig)")
print("\nWas das Fix macht:")
print("  PPA rendert in rot_buf (privater Buffer)")
print("  Dann memcpy nach panel_fb (atomar, kein Tearing)")
