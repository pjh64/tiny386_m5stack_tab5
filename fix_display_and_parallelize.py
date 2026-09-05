#!/usr/bin/env python3
with open('esp/main/esp_main.c', 'r') as f:
    content = f.read()

# 1. Output auf volle Panel-Groesse zuruecksetzen (Stride muss 720 sein!)
content = content.replace(
    '''			oper.out.pic_w       = 480;   /* Native VGA-Auflösung nach Rotation */
			oper.out.pic_h       = 640;''',
    '''			oper.out.pic_w       = LCD_HEIGHT;  /* 720 */
			oper.out.pic_h       = LCD_WIDTH;   /* 1280 */''')

# 2. Skalierung wiederherstellen (640x480 -> Vollbild)
content = content.replace(
    '''			if (g_no_rotate) {
				/* BENCHMARK: keine Rotation, keine Skalierung */
				oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_0;
				oper.scale_x = 1.0f;
				oper.scale_y = 1.0f;
			} else {
				oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_270;
				oper.scale_x = 1.0f;
				oper.scale_y = 1.0f;
			}''',
    '''			if (g_no_rotate) {
				/* BENCHMARK: keine Rotation, nur Skalierung */
				oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_0;
				oper.scale_x = 1280.0f / 640.0f;
				oper.scale_y = 1280.0f / 480.0f;
			} else {
				oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_270;
				oper.scale_x = 1280.0f / 640.0f;
				oper.scale_y = 720.0f / 480.0f;
			}''')

# 3. display_task auf Core 1 verschieben (parallel zur VGA-Emulation auf Core 0)
content = content.replace(
    '''		xTaskCreatePinnedToCore(display_task, "display", 4096, NULL, 0,
					&disp_task_handle, 0);''',
    '''		xTaskCreatePinnedToCore(display_task, "display", 4096, NULL, 0,
					&disp_task_handle, 1);''')

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)

print("✓ Display repariert (volle 720x1280, Stride 720)")
print("✓ display_task auf Core 1 (parallel zu vga_task auf Core 0)")
