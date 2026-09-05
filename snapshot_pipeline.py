#!/usr/bin/env python3
with open('esp/main/esp_main.c', 'r') as f:
    content = f.read()

# 1. redraw(): Snapshot auf Core 0 statt direkter fb-Pointer
old_redraw = '''	Console *s = opaque;
	/* Nur signalisieren - die schwere Arbeit macht display_task,
	 * damit vga_step/Retrace nicht blockiert wird. */
	disp_src = (uint16_t *) s->fb;'''
new_redraw = '''	Console *s = opaque;
	/* Snapshot auf Core 0: display_task (Core 1) liest nur snap_buf,
	 * dadurch keine PSRAM-Contention und kein Tearing. */
	size_t fbsz = (size_t) LCD_WIDTH * LCD_HEIGHT * 2;
	memcpy(snap_buf, s->fb, fbsz);
	esp_cache_msync(snap_buf, fbsz, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
	disp_src = snap_buf;'''
assert old_redraw in content
content = content.replace(old_redraw, new_redraw)

# 2. display_task auf Core 1 (PPA laeuft parallel zum Guest)
old_pin = '''		xTaskCreatePinnedToCore(display_task, "display", 4096, NULL, 0,
					&disp_task_handle, 0);'''
new_pin = '''		xTaskCreatePinnedToCore(display_task, "display", 4096, NULL, 0,
					&disp_task_handle, 1);'''
assert old_pin in content
content = content.replace(old_pin, new_pin)

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)

print("OK: Snapshot-Pipeline aktiv (Core 0 = Guest+Snapshot, Core 1 = PPA)")
