#!/usr/bin/env python3
"""
Reduziert den Framebuffer auf 640x480 und passt die PPA-Konfiguration an
"""

with open('esp/main/esp_main.c', 'r') as f:
    content = f.read()

# 1. Ändere die conf.width/conf.height Korrektur auf 640x480
old_conf = '''	if (conf.width != LCD_WIDTH || conf.height != LCD_HEIGHT) {
		fprintf(stderr, "fixing width/height mismatch %dx%d => %dx%d\\n",
			conf.width, conf.height, LCD_WIDTH, LCD_HEIGHT);
		conf.width = LCD_WIDTH;
		conf.height = LCD_HEIGHT;
	}'''

new_conf = '''	/* Framebuffer auf VGA-Auflösung reduzieren (640x480) */
	if (conf.width != 640 || conf.height != 480) {
		fprintf(stderr, "fixing width/height mismatch %dx%d => 640x480\\n",
			conf.width, conf.height);
		conf.width = 640;
		conf.height = 480;
	}'''

content = content.replace(old_conf, new_conf)

# 2. Ändere die PPA-Konfiguration in display_task
old_ppa = '''			oper.in.buffer  = src;
			oper.in.pic_w   = LCD_WIDTH;    /* 1280 */
			oper.in.pic_h   = LCD_HEIGHT;   /* 720 */

			/* Wie alter STRETCH-Pfad:
			 * Nimm den zentralen 720x480-Ausschnitt aus dem 1280x720 VGA-Framebuffer
			 * und strecke ihn auf Vollbild. */
			oper.in.block_offset_x = 280;
			oper.in.block_offset_y = 120;
			oper.in.block_w = 720;
			oper.in.block_h = 480;
			oper.in.srm_cm  = PPA_SRM_COLOR_MODE_RGB565;

			oper.out.buffer      = out_buf;
			/* PPA erfordert: buffer_size muss aligned sein */
			size_t raw_sz = LCD_WIDTH * LCD_HEIGHT * 2;
			oper.out.buffer_size = (raw_sz + 127) & ~127;  /* auf 128 runden */
			oper.out.pic_w       = LCD_HEIGHT;  /* 720 */
			oper.out.pic_h       = LCD_WIDTH;   /* 1280 */
			oper.out.srm_cm      = PPA_SRM_COLOR_MODE_RGB565;

			/* Orientierung war mit 270° korrekt.
			 * PPA skaliert vor der Rotation:
			 * 720x480 -> 1280x720, danach Rotation -> 720x1280. */
			if (g_no_rotate) {
				/* BENCHMARK: keine Rotation, nur Skalierung */
				oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_0;
				oper.scale_x = 1280.0f / 720.0f;
				oper.scale_y = 1280.0f / 480.0f;
			} else {
				oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_270;
				oper.scale_x = 1280.0f / 720.0f;
				oper.scale_y = 720.0f / 480.0f;
			}'''

new_ppa = '''			oper.in.buffer  = src;
			oper.in.pic_w   = 640;    /* VGA-Auflösung */
			oper.in.pic_h   = 480;

			/* Lies den gesamten 640x480 Framebuffer */
			oper.in.block_offset_x = 0;
			oper.in.block_offset_y = 0;
			oper.in.block_w = 640;
			oper.in.block_h = 480;
			oper.in.srm_cm  = PPA_SRM_COLOR_MODE_RGB565;

			oper.out.buffer      = out_buf;
			/* PPA erfordert: buffer_size muss aligned sein */
			size_t raw_sz = LCD_WIDTH * LCD_HEIGHT * 2;
			oper.out.buffer_size = (raw_sz + 127) & ~127;  /* auf 128 runden */
			oper.out.pic_w       = LCD_HEIGHT;  /* 720 */
			oper.out.pic_h       = LCD_WIDTH;   /* 1280 */
			oper.out.srm_cm      = PPA_SRM_COLOR_MODE_RGB565;

			/* PPA skaliert vor der Rotation:
			 * 640x480 -> 1280x720, danach Rotation -> 720x1280. */
			if (g_no_rotate) {
				/* BENCHMARK: keine Rotation, nur Skalierung */
				oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_0;
				oper.scale_x = 1280.0f / 640.0f;
				oper.scale_y = 1280.0f / 480.0f;
			} else {
				oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_270;
				oper.scale_x = 1280.0f / 640.0f;
				oper.scale_y = 720.0f / 480.0f;
			}'''

content = content.replace(old_ppa, new_ppa)

# 3. Ändere die console_init Framebuffer-Größe
old_fb1 = '''	c->fb1 = fbmalloc(LCD_WIDTH * LCD_HEIGHT / NN * 2);'''
new_fb1 = '''	c->fb1 = fbmalloc(640 * 480 / NN * 2);'''
content = content.replace(old_fb1, new_fb1)

old_rot = '''	if (rot_buf == NULL) {
		/* PSRAM-Heap ignoriert grosse Alignments -> manuell auf 64 aufrunden */
		size_t sz = LCD_WIDTH * LCD_HEIGHT * 2;'''
new_rot = '''	if (rot_buf == NULL) {
		/* PSRAM-Heap ignoriert grosse Alignments -> manuell auf 64 aufrunden */
		size_t sz = 640 * 480 * 2;'''
content = content.replace(old_rot, new_rot)

old_snap = '''	if (snap_buf == NULL) {
		size_t sz = LCD_WIDTH * LCD_HEIGHT * 2;'''
new_snap = '''	if (snap_buf == NULL) {
		size_t sz = 640 * 480 * 2;'''
content = content.replace(old_snap, new_snap)

# 4. Ändere den c->fb Framebuffer
old_fb = '''	c->fb = bigmalloc(LCD_WIDTH * LCD_HEIGHT * 2);'''
new_fb = '''	c->fb = bigmalloc(640 * 480 * 2);'''
content = content.replace(old_fb, new_fb)

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)

print("✓ Framebuffer-Optimierung abgeschlossen")
print("  - Framebuffer: 1280x720 -> 640x480")
print("  - PPA: Liest direkt 640x480, skaliert auf 1280x720")
print("  - Erwartete Verbesserung: transpose=40ms -> ~15ms")
