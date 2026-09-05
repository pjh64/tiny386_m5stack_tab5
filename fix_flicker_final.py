#!/usr/bin/env python3
"""
Saubere Korrektur: Dynamischer PPA-Crop + Double-Buffering
"""

with open('esp/main/esp_main.c', 'r') as f:
    lines = f.readlines()

# 1. Füge globale Variablen für VGA-Auflösung nach den anderen Globals hinzu
out = []
added_globals = False
for i, line in enumerate(lines):
    out.append(line)
    
    # Nach der Zeile mit g_no_rotate einfügen (nur einmal)
    if not added_globals and 'static volatile bool g_no_rotate = false;' in line:
        out.append('\n')
        out.append('/* Dynamische VGA-Auflösung für PPA-Crop */\n')
        out.append('static volatile int g_vga_width = 640;\n')
        out.append('static volatile int g_vga_height = 480;\n')
        out.append('\n')
        out.append('/* Aktualisiert die globale VGA-Auflösung */\n')
        out.append('void lcd_update_vga_resolution(int width, int height)\n')
        out.append('{\n')
        out.append('\tg_vga_width = width;\n')
        out.append('\tg_vga_height = height;\n')
        out.append('}\n')
        added_globals = True

content = ''.join(out)

# 2. Ersetze die hartcodierte PPA-Config mit dynamischer Berechnung
old_config = '''			/* Wie alter STRETCH-Pfad:
			 * Nimm den zentralen 720x480-Ausschnitt aus dem 1280x720 VGA-Framebuffer
			 * und strecke ihn auf Vollbild. */
			oper.in.block_offset_x = 280;
			oper.in.block_offset_y = 120;
			oper.in.block_w = 720;
			oper.in.block_h = 480;'''

new_config = '''			/* Dynamischer Crop basierend auf aktueller VGA-Auflösung */
			int vga_w = g_vga_width;
			int vga_h = g_vga_height;
			
			/* Clamp auf sinnvolle Werte */
			if (vga_w < 320) vga_w = 320;
			if (vga_w > LCD_WIDTH) vga_w = LCD_WIDTH;
			if (vga_h < 200) vga_h = 200;
			if (vga_h > LCD_HEIGHT) vga_h = LCD_HEIGHT;
			
			/* Berechne zentrierte Offsets */
			int offset_x = (LCD_WIDTH - vga_w) / 2;
			int offset_y = (LCD_HEIGHT - vga_h) / 2;
			
			oper.in.block_offset_x = offset_x;
			oper.in.block_offset_y = offset_y;
			oper.in.block_w = vga_w;
			oper.in.block_h = vga_h;'''

content = content.replace(old_config, new_config)

# 3. Ändere out_buf zu rot_buf (Double-Buffering)
content = content.replace(
    'uint16_t *out_buf = globals.panel_fb ? (uint16_t *)globals.panel_fb : rot_buf;',
    'uint16_t *out_buf = rot_buf;  /* Immer in rot_buf rendern */'
)

# 4. Füge memcpy nach PPA hinzu (vor dem Edge-Clearing)
old_edge = '''		esp_cache_msync(out_buf, 4 * 720 * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
		esp_cache_msync(out_buf + (1280 - 4) * 720, 4 * 720 * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);   /* row last  -> linke Kante  */'''

new_edge = '''		/* Kopiere fertigen Frame atomar in den DPI-Framebuffer */
		if (globals.panel_fb) {
			memcpy(globals.panel_fb, out_buf, LCD_WIDTH * LCD_HEIGHT * 2);
		}'''

content = content.replace(old_edge, new_edge)

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)

print("✓ esp_main.c: Dynamischer PPA-Crop implementiert")
print("✓ esp_main.c: Double-Buffering (rot_buf → panel_fb)")
