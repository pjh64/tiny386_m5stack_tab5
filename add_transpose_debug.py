#!/usr/bin/env python3
with open('esp/main/esp_main.c', 'r') as f:
    content = f.read()

start = content.index('static void display_task(void *arg)')
end = content.index('static int redraw_count = 0;')

new_task = '''static void display_task(void *arg)
{
	for (;;) {
		ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
		uint16_t *src = disp_src;
		uint16_t *out_buf = globals.panel_fb ? (uint16_t *)globals.panel_fb : rot_buf;
		if (!src || !rot_buf || !snap_buf)
			continue;

		/* Kein Snapshot noetig: vga_task (schreibt fb) und display_task
		 * (PPA) laufen beide auf Core 0 -> fb ist stabil waehrend PPA liest. */
		int64_t t0 = esp_timer_get_time();
		int64_t t1 = t0;   /* memcpy entfaellt */

		int64_t t_cfg = 0, t_ppa = 0, t_edge = 0, t_sync = 0;

		if (ppa_srm_handle) {
			/* PPA-Hardware: Rotation 270 + Skalierung in einem Durchlauf */
			int64_t tc0 = esp_timer_get_time();
			ppa_srm_oper_config_t oper;
			memset(&oper, 0, sizeof(oper));
			oper.in.buffer  = src;
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

			/* Orientierung war mit 270 korrekt.
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
			}
			oper.mirror_x = false;
			oper.mirror_y = false;
			oper.mode = PPA_TRANS_MODE_BLOCKING;
			int64_t tc1 = esp_timer_get_time();
			t_cfg = tc1 - tc0;

			esp_err_t perr = ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper);
			int64_t tc2 = esp_timer_get_time();
			t_ppa = tc2 - tc1;
			if (perr != ESP_OK) {
				static int ec = 0;
				if (++ec <= 3)
					ESP_LOGE("PPA", "srm failed: %s", esp_err_to_name(perr));
				/* Fallback: Software */
				for (int y = 0; y < LCD_HEIGHT; y++) {
					const uint16_t *row = src + (size_t) y * LCD_WIDTH;
					uint16_t *dst = rot_buf + y;
					for (int x = 0; x < LCD_WIDTH; x++)
						dst[(size_t) x * LCD_HEIGHT] = row[LCD_WIDTH - 1 - x];
				}
			}
		} else {
			int64_t tc1 = esp_timer_get_time();
			/* Fallback: Software */
			for (int y = 0; y < LCD_HEIGHT; y++) {
				const uint16_t *row = src + (size_t) y * LCD_WIDTH;
				uint16_t *dst = rot_buf + y;
				for (int x = 0; x < LCD_WIDTH; x++)
					dst[(size_t) x * LCD_HEIGHT] = row[LCD_WIDTH - 1 - x];
			}
			t_ppa = esp_timer_get_time() - tc1;
		}

		/* Kanten-Artefakt der PPA-Rotation: aeusserste Zeilen schwarz */
		int64_t te0 = esp_timer_get_time();
		memset(out_buf, 0, 2 * 720 * 2);                      /* row 0..1  -> rechte Kante */
		memset(out_buf + (1280 - 2) * 720, 0, 2 * 720 * 2);
		memset(rot_buf, 0, 2 * 720 * 2);                      /* row 0..1  -> rechte Kante */
		memset(rot_buf + (1280 - 2) * 720, 0, 2 * 720 * 2);   /* row last  -> linke Kante  */
		int64_t te1 = esp_timer_get_time();
		t_edge = te1 - te0;

		esp_cache_msync(out_buf, 4 * 720 * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
		esp_cache_msync(out_buf + (1280 - 4) * 720, 4 * 720 * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
		int64_t t2 = esp_timer_get_time();
		t_sync = t2 - te1;

		if (!globals.panel_fb)
			lcd_draw(0, 0, 720, 1280, rot_buf);
		int64_t t3 = esp_timer_get_time();

		static int fc = 0;
		static int64_t acc_mem = 0, acc_dr = 0;
		static int64_t acc_cfg = 0, acc_ppa = 0, acc_edge = 0, acc_sync = 0;
		static int64_t last_log = 0;
		acc_mem  += t1 - t0;
		acc_cfg  += t_cfg;
		acc_ppa  += t_ppa;
		acc_edge += t_edge;
		acc_sync += t_sync;
		acc_dr   += t3 - t2;
		fc++;
		if (t3 - last_log > 1000000) {   /* 1x pro Sekunde */
			long tr = (long)((acc_cfg + acc_ppa + acc_edge + acc_sync) / fc);
			ESP_LOGW("PERF", "disp fps=%d avg us: memcpy=%ld | tr=%ld [cfg=%ld ppa=%ld edge=%ld sync=%ld] | draw=%ld",
				 fc, (long)(acc_mem / fc), tr,
				 (long)(acc_cfg / fc), (long)(acc_ppa / fc),
				 (long)(acc_edge / fc), (long)(acc_sync / fc),
				 (long)(acc_dr / fc));
			fc = 0;
			acc_mem = acc_dr = 0;
			acc_cfg = acc_ppa = acc_edge = acc_sync = 0;
			last_log = t3;
		}
	}
}

'''

content = content[:start] + new_task + content[end:]

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)

print("display_task mit Transpose-Einzelschritt-Timing ersetzt")
