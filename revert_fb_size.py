#!/usr/bin/env python3
with open('esp/main/esp_main.c', 'r') as f:
    content = f.read()

# 1. conf wieder auf 1280x720
content = content.replace(
    '''	/* Framebuffer auf VGA-Auflösung reduzieren (640x480) */
	if (conf.width != 640 || conf.height != 480) {
		fprintf(stderr, "fixing width/height mismatch %dx%d => 640x480\\n",
			conf.width, conf.height);
		conf.width = 640;
		conf.height = 480;
	}''',
    '''	if (conf.width != LCD_WIDTH || conf.height != LCD_HEIGHT) {
		fprintf(stderr, "fixing width/height mismatch %dx%d => %dx%d\\n",
			conf.width, conf.height, LCD_WIDTH, LCD_HEIGHT);
		conf.width = LCD_WIDTH;
		conf.height = LCD_HEIGHT;
	}''')

# 2. Buffer-Groessen zurueck (alle Vorkommen)
content = content.replace('fbmalloc(640 * 480 / NN * 2)', 'fbmalloc(LCD_WIDTH * LCD_HEIGHT / NN * 2)')
content = content.replace('bigmalloc(640 * 480 * 2)', 'bigmalloc(LCD_WIDTH * LCD_HEIGHT * 2)')
content = content.replace('size_t sz = 640 * 480 * 2;', 'size_t sz = LCD_WIDTH * LCD_HEIGHT * 2;')

# 3. PPA Input-Block zurueck auf 720x480 @ (280,120)
content = content.replace(
    '''			oper.in.pic_w   = 640;    /* VGA-Auflösung */
			oper.in.pic_h   = 480;

			/* Lies den gesamten 640x480 Framebuffer */
			oper.in.block_offset_x = 0;
			oper.in.block_offset_y = 0;
			oper.in.block_w = 640;
			oper.in.block_h = 480;''',
    '''			oper.in.pic_w   = LCD_WIDTH;    /* 1280 */
			oper.in.pic_h   = LCD_HEIGHT;   /* 720 */

			/* Wie alter STRETCH-Pfad:
			 * Nimm den zentralen 720x480-Ausschnitt aus dem 1280x720 VGA-Framebuffer
			 * und strecke ihn auf Vollbild. */
			oper.in.block_offset_x = 280;
			oper.in.block_offset_y = 120;
			oper.in.block_w = 720;
			oper.in.block_h = 480;''')

# 4. Skalierung zurueck auf 720er-Basis
content = content.replace('oper.scale_x = 1280.0f / 640.0f;', 'oper.scale_x = 1280.0f / 720.0f;')

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)

print("✓ Framebuffer zurueck auf 1280x720 (Text-Mode repariert, rot_buf-Overflow behoben)")
print("✓ BEHALTEN: Port 0x3da Fast-Forward + display_task auf Core 1")
