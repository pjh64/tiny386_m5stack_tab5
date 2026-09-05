#!/usr/bin/env python3
"""
Repariert display_task: Entfernt Deklaration und fügt Implementierung ein
"""

with open('esp/main/esp_main.c', 'r') as f:
    lines = f.readlines()

# Finde und entferne die Deklaration auf Zeile 118
out = []
for i, line in enumerate(lines):
    # Entferne die Deklaration
    if line.strip() == 'static void display_task(void *arg);':
        continue
    # Entferne das leere Kommentar davor
    if 'VSync-Interrupt-Callback' in line:
        continue
    if line.strip() == '' and i > 0 and 'VSync-Interrupt-Callback' in lines[max(0,i-1)]:
        continue
    
    out.append(line)

# Finde die Stelle wo display_task implementiert werden sollte
# Das ist vor lcd_draw oder nach den Hilfsfunktionen
content = ''.join(out)

# Finde wo console_init endet und füge display_task danach ein
display_task_impl = '''

/* Eigener Display-Task: macht Stretch+Transpose mit PPA */
static void display_task(void *arg)
{
	for (;;) {
		ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
		uint16_t *src = disp_src;
		uint16_t *out_buf = rot_buf;  /* Immer in rot_buf rendern */
		if (!src || !rot_buf || !snap_buf)
			continue;

		int64_t t0 = esp_timer_get_time();

		if (ppa_srm_handle) {
			/* PPA-Hardware: Rotation + Skalierung */
			ppa_srm_oper_config_t oper;
			memset(&oper, 0, sizeof(oper));
			oper.in.buffer  = src;
			oper.in.pic_w   = LCD_WIDTH;
			oper.in.pic_h   = LCD_HEIGHT;

			/* Dynamischer Crop basierend auf aktueller VGA-Auflösung */
			int vga_w = g_vga_width;
			int vga_h = g_vga_height;
			
			if (vga_w < 320) vga_w = 320;
			if (vga_w > LCD_WIDTH) vga_w = LCD_WIDTH;
			if (vga_h < 200) vga_h = 200;
			if (vga_h > LCD_HEIGHT) vga_h = LCD_HEIGHT;
			
			int offset_x = (LCD_WIDTH - vga_w) / 2;
			int offset_y = (LCD_HEIGHT - vga_h) / 2;
			
			oper.in.block_offset_x = offset_x;
			oper.in.block_offset_y = offset_y;
			oper.in.block_w = vga_w;
			oper.in.block_h = vga_h;
			oper.in.srm_cm  = PPA_SRM_COLOR_MODE_RGB565;

			oper.out.buffer      = out_buf;
			size_t raw_sz = LCD_WIDTH * LCD_HEIGHT * 2;
			oper.out.buffer_size = (raw_sz + 127) & ~127;
			oper.out.pic_w       = LCD_HEIGHT;
			oper.out.pic_h       = LCD_WIDTH;
			oper.out.srm_cm      = PPA_SRM_COLOR_MODE_RGB565;

			if (g_no_rotate) {
				oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_0;
				oper.scale_x = 1.0f;
				oper.scale_y = 1280.0f / 480.0f;
			} else {
				oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_270;
				oper.scale_x = 1280.0f / 720.0f;
				oper.scale_y = 720.0f / 480.0f;
			}
			oper.mirror_x = false;
			oper.mirror_y = false;
			oper.mode = PPA_TRANS_MODE_BLOCKING;

			esp_err_t perr = ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper);
			if (perr != ESP_OK) {
				static int ec = 0;
				if (++ec <= 3)
					ESP_LOGE("PPA", "srm failed: %s", esp_err_to_name(perr));
			}
		} else {
			/* Fallback: Software-Transpose */
			for (int y = 0; y < LCD_HEIGHT; y++) {
				const uint16_t *row = src + (size_t) y * LCD_WIDTH;
				uint16_t *dst = rot_buf + y;
				for (int x = 0; x < LCD_WIDTH; x++)
					dst[(size_t) x * LCD_HEIGHT] = row[LCD_WIDTH - 1 - x];
			}
		}

		int64_t t2 = esp_timer_get_time();
		
		/* Kopiere fertigen Frame atomar in den DPI-Framebuffer */
		if (globals.panel_fb) {
			memcpy(globals.panel_fb, out_buf, LCD_WIDTH * LCD_HEIGHT * 2);
		}

		/* Performance-Messung */
		static int pc = 0; static int64_t pacc = 0;
		pacc += t2 - t0;
		if (++pc >= 100) {
			ESP_LOGW("PERF", "disp fps=%d avg us: memcpy=0 transpose=%lld draw=%lld",
				(int)(100000000LL / (pacc / pc)),
				(long long)(pacc / pc), 0LL);
			pc = 0; pacc = 0;
		}
	}
}

'''

# Füge display_task nach console_init ein
# Suche nach dem Ende von console_init
console_init_end = content.find('c->fb = bigmalloc(LCD_WIDTH * LCD_HEIGHT * 2);')
if console_init_end != -1:
    # Finde das Ende der Funktion (nächste })
    next_brace = content.find('\n}\n', console_init_end)
    if next_brace != -1:
        insert_pos = next_brace + 3
        content = content[:insert_pos] + display_task_impl + content[insert_pos:]
        print("✓ display_task nach console_init eingefügt")
else:
    print("⚠ console_init Ende nicht gefunden, füge am Ende ein")
    content = content + display_task_impl

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)

print("✓ display_task wiederhergestellt")
