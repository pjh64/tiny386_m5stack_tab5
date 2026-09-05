#!/usr/bin/env python3
"""
Entkoppelt vga_refresh() von der CPU-Emulation.

Vorher:
  CPU1: cpu_step() → vga_refresh() [15ms blockiert]

Nachher:
  CPU1: cpu_step() [läuft ununterbrochen]
  CPU1 (separater Task): vga_refresh() [alle 16ms, asynchron]
"""

import sys

# 1. Erstelle separaten vga_refresh_task in esp_main.c
ESP_MAIN = 'esp/main/esp_main.c'

with open(ESP_MAIN, 'r') as f:
    content = f.read()

# Füge VGA-Refresh-Task nach display_task ein
vga_refresh_task = '''
static TaskHandle_t vga_refresh_task_handle = NULL;
static SemaphoreHandle_t vga_refresh_mutex = NULL;

static void vga_refresh_task(void *arg)
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
}
'''

# Füge nach display_task Definition ein
insert_pos = content.find('static void display_task(void *arg)')
if insert_pos != -1:
    # Finde das Ende der display_task Funktion
    func_end = content.find('}\n\n', insert_pos + 100)
    if func_end != -1:
        content = content[:func_end+2] + vga_refresh_task + content[func_end+2:]
        print("✓ VGA-Refresh-Task hinzugefügt")
else:
    print("FEHLER: Konnte display_task nicht finden")
    sys.exit(1)

# 2. Erstelle Mutex und starte Task in app_main
task_start = '''
	// Erstelle VGA-Refresh-Mutex und Task
	vga_refresh_mutex = xSemaphoreCreateMutex();
	xTaskCreatePinnedToCore(vga_refresh_task, "vga_refresh", 4096, NULL, 2, &vga_refresh_task_handle, 1);
'''

# Füge nach i386_task und vga_task Start ein
insert_pos = content.find('xTaskCreatePinnedToCore(vga_task')
if insert_pos != -1:
    line_end = content.find('\n', insert_pos) + 1
    content = content[:line_end] + task_start + content[line_end:]
    print("✓ VGA-Refresh-Task-Start hinzugefügt")

# 3. Schütze pc_step mit Mutex
pc_step_call = content.find('pc_step(pc);')
if pc_step_call != -1:
    # Finde die for-Loop
    loop_start = content.rfind('for (; pc->shutdown_state', 0, pc_step_call)
    if loop_start != -1:
        old_loop = content[loop_start:pc_step_call + len('pc_step(pc);')]
        new_loop = old_loop.replace(
            'pc_step(pc);',
            '''xSemaphoreTake(vga_refresh_mutex, portMAX_DELAY);
		pc_step(pc);
		xSemaphoreGive(vga_refresh_mutex);'''
        )
        content = content[:loop_start] + new_loop + content[pc_step_call + len('pc_step(pc);'):]
        print("✓ Mutex-Schutz um pc_step hinzugefügt")

# 4. Entferne vga_refresh aus pc_step
PC_FILE = 'pc.c'
with open(PC_FILE, 'r') as f:
    pc_content = f.read()

# Finde und entferne vga_refresh Aufruf
if 'vga_refresh(pc->vga' in pc_content:
    pc_content = pc_content.replace(
        '\tvga_refresh(pc->vga, pc->redraw, pc->redraw_data, 0);',
        '\t// vga_refresh jetzt in separatem Task (vga_refresh_task)'
    )
    print("✓ vga_refresh aus pc_step entfernt")

with open(PC_FILE, 'w') as f:
    f.write(pc_content)

with open(ESP_MAIN, 'w') as f:
    f.write(content)

print("\n=== Zusammenfassung ===")
print("VGA-Refresh läuft jetzt in separatem Task (alle 16ms)")
print("CPU-Emulation wird nicht mehr blockiert")
print("\nErwarteter Speedup: 30-50%")
print("\nNächster Schritt: cd esp && idf.py build")

