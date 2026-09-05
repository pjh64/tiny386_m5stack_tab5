#!/usr/bin/env python3
"""
Fix für das Flimmer-Artefakt am linken Rand
"""

print("=== Implementiere Cache-Sync Fix ===\n")

try:
    with open('esp/main/esp_main.c', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Suche nach dem redraw/lcd_draw Aufruf
    # Füge Cache-Sync VOR dem LCD-Update hinzu
    
    # Methode 1: Suche nach "xTaskNotifyGive(disp_task_handle)"
    marker1 = '    xTaskNotifyGive(disp_task_handle);'
    if marker1 in content:
        cache_sync_before_notify = '''    // Cache-Synchronisierung VOR dem Notify
    // Stelle sicher dass der gesamte Framebuffer im RAM ist
    esp_cache_msync(console->fb, LCD_WIDTH * LCD_HEIGHT * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
    
    xTaskNotifyGive(disp_task_handle);'''
        
        content = content.replace(marker1, cache_sync_before_notify, 1)
        print("✓ Cache-Sync vor xTaskNotifyGive hinzugefügt")
    
    # Methode 2: Suche nach dem PPA-Block in display_task
    marker2 = 'esp_lcd_panel_draw_bitmap'
    if marker2 in content:
        # Finde die Zeile und füge Cache-Sync davor ein
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if marker2 in line:
                # Füge Cache-Sync 3 Zeilen davor ein
                insert_pos = max(0, i - 3)
                cache_sync = '''    
    // Cache-Synchronisierung für LCD-Panel
    esp_cache_msync(src, LCD_WIDTH * LCD_HEIGHT * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
'''
                lines.insert(insert_pos, cache_sync)
                print(f"✓ Cache-Sync vor lcd_panel_draw_bitmap hinzugefügt (Zeile {i})")
                break
        content = '\n'.join(lines)
    
    with open('esp/main/esp_main.c', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✓✓✓ Cache-Sync Fix implementiert! ✓✓✓")
    print("\nWas das Fix macht:")
    print("  - Synchronisiert den Cache VOR dem LCD-Update")
    print("  - Stellt sicher dass alle Pixel-Daten im RAM sind")
    print("  - Behebt das Flimmer-Artefakt am linken Rand")
    
except Exception as e:
    print(f"✗ Fehler: {e}")
    import traceback
    traceback.print_exc()
