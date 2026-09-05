#!/usr/bin/env python3
"""
Reduziert die PPA Output-Größe auf 480x640 (native VGA-Auflösung nach Rotation)
"""

with open('esp/main/esp_main.c', 'r') as f:
    content = f.read()

# Ändere die PPA Output-Konfiguration
old_ppa = '''			/* PPA erfordert: buffer_size muss aligned sein */
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

new_ppa = '''			/* PPA erfordert: buffer_size muss aligned sein */
			size_t raw_sz = LCD_WIDTH * LCD_HEIGHT * 2;
			oper.out.buffer_size = (raw_sz + 127) & ~127;  /* auf 128 runden */
			oper.out.pic_w       = 480;   /* Native VGA-Auflösung nach Rotation */
			oper.out.pic_h       = 640;
			oper.out.srm_cm      = PPA_SRM_COLOR_MODE_RGB565;

			/* PPA rotiert ohne Skalierung:
			 * 640x480 -> Rotation -> 480x640. */
			if (g_no_rotate) {
				/* BENCHMARK: keine Rotation, keine Skalierung */
				oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_0;
				oper.scale_x = 1.0f;
				oper.scale_y = 1.0f;
			} else {
				oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_270;
				oper.scale_x = 1.0f;
				oper.scale_y = 1.0f;
			}'''

content = content.replace(old_ppa, new_ppa)

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)

print("✓ PPA Output-Optimierung abgeschlossen")
print("  - Output: 720x1280 -> 480x640")
print("  - Skalierung: 2.0x/1.5x -> 1.0x/1.0x (keine Skalierung)")
print("  - Erwartete Verbesserung: transpose=40ms -> ~10ms")
