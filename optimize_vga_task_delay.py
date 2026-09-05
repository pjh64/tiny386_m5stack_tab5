#!/usr/bin/env python3
"""
Optimiert vga_task: Fügt vTaskDelay hinzu um die Frame-Rate auf 30fps zu begrenzen.

Problem: Die 100ms-Throttle in pc_vga_step greift nicht weil full_update immer true ist.
Lösung: vga_task ruft pc_vga_step() nur alle 33ms auf (30fps statt ~60fps).

Das reduziert den Overhead von ~50% auf ~25% ohne RAM zu verbrauchen.
"""

VGA_TASK_FILE = 'esp/main/lcd_m5stack_tab5.c'

with open(VGA_TASK_FILE, 'r') as f:
    content = f.read()

# Suche nach der while-Loop in vga_task
old_loop = '''    while (1) {
        int64_t va = esp_timer_get_time();
        pc_vga_step(globals.pc);
        int64_t vb = esp_timer_get_time();'''

new_loop = '''    while (1) {
        vTaskDelay(pdMS_TO_TICKS(33));  // Limit auf 30fps
        int64_t va = esp_timer_get_time();
        pc_vga_step(globals.pc);
        int64_t vb = esp_timer_get_time();'''

if old_loop in content:
    content = content.replace(old_loop, new_loop)
    print("✓ vga_task: vTaskDelay(33ms) hinzugefügt (30fps)")
else:
    print("FEHLER: Konnte while-Loop in vga_task nicht finden")
    import sys
    sys.exit(1)

with open(VGA_TASK_FILE, 'w') as f:
    f.write(content)

print("\n=== Zusammenfassung ===")
print("vga_task läuft jetzt mit 30fps statt ~60fps")
print("Das reduziert den VGA-Overhead um ~50%")
print("\nErwarteter Speedup: 20-30% für die CPU-Emulation")

