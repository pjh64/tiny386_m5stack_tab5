#!/usr/bin/env python3
"""
Korrigiert vga_refresh_task: verwendet pc->redraw statt lokaler redraw-Funktion
"""

ESP_MAIN = 'esp/main/esp_main.c'

with open(ESP_MAIN, 'r') as f:
    content = f.read()

# Ersetze den fehlerhaften vga_refresh_task
old_task = '''static void vga_refresh_task(void *arg)
{
	TickType_t last_wake_time = xTaskGetTickCount();
	
	for (;;) {
		// Warte ~16ms (60Hz)
		vTaskDelayUntil(&last_wake_time, pdMS_TO_TICKS(16));
		
		// Hole exklusiven Zugriff auf VGA-State
		if (xSemaphoreTake(vga_refresh_mutex, pdMS_TO_TICKS(1)) == pdTRUE) {
			if (globals.pc && globals.pc->vga) {
				vga_refresh(globals.pc->vga, redraw, globals.pc, 0);
			}
			xSemaphoreGive(vga_refresh_mutex);
		}
	}
}'''

new_task = '''static void vga_refresh_task(void *arg)
{
	TickType_t last_wake_time = xTaskGetTickCount();
	
	for (;;) {
		// Warte ~16ms (60Hz)
		vTaskDelayUntil(&last_wake_time, pdMS_TO_TICKS(16));
		
		// Hole exklusiven Zugriff auf VGA-State
		if (xSemaphoreTake(vga_refresh_mutex, pdMS_TO_TICKS(1)) == pdTRUE) {
			PC *pc = globals.pc;
			if (pc && pc->vga && pc->redraw) {
				vga_refresh(pc->vga, pc->redraw, pc->redraw_data, 0);
			}
			xSemaphoreGive(vga_refresh_mutex);
		}
	}
}'''

content = content.replace(old_task, new_task)

with open(ESP_MAIN, 'w') as f:
    f.write(content)

print("✓ vga_refresh_task korrigiert")
print("  Verwendet jetzt pc->redraw und pc->redraw_data")

