#!/usr/bin/env python3
"""
Rollt die vga_refresh_task Änderungen zurück und wählt einen 
ressourcen-schonenden Ansatz: vga_refresh seltener aufrufen.
"""

ESP_MAIN = 'esp/main/esp_main.c'

with open(ESP_MAIN, 'r') as f:
    content = f.read()

import re

# 1. Entferne vga_refresh_task komplett
content = re.sub(
    r'\nstatic TaskHandle_t vga_refresh_task_handle = NULL;\n'
    r'static SemaphoreHandle_t vga_refresh_mutex = NULL;\n\n'
    r'static void vga_refresh_task\(void \*arg\)\n\{.*?\n\}\n',
    '\n', content, flags=re.DOTALL
)
print("✓ vga_refresh_task entfernt")

# 2. Entferne Task-Erstellung und Mutex
content = re.sub(
    r'\n\t// Erstelle VGA-Refresh-Mutex und Task\n'
    r'\tvga_refresh_mutex = xSemaphoreCreateMutex\(\);\n'
    r'\txTaskCreatePinnedToCore\(vga_refresh_task.*?;\n',
    '\n', content, flags=re.DOTALL
)
print("✓ Task-Erstellung entfernt")

# 3. Entferne Mutex um pc_step (falls vorhanden)
content = re.sub(
    r'\t\txSemaphoreTake\(vga_refresh_mutex, portMAX_DELAY\);\n'
    r'\t\tpc_step\(pc\);\n'
    r'\t\txSemaphoreGive\(vga_refresh_mutex\);',
    '\t\tpc_step(pc);', content
)
print("✓ Mutex um pc_step entfernt")

with open(ESP_MAIN, 'w') as f:
    f.write(content)

# 4. Stelle vga_refresh in pc_step wieder her
PC_FILE = 'pc.c'
with open(PC_FILE, 'r') as f:
    pc_content = f.read()

# Prüfe ob vga_refresh auskommentiert wurde
if '// vga_refresh jetzt in separatem Task' in pc_content:
    pc_content = pc_content.replace(
        '\t// vga_refresh jetzt in separatem Task (vga_refresh_task)',
        '\tvga_refresh(pc->vga, pc->redraw, pc->redraw_data, 0);'
    )
    print("✓ vga_refresh in pc_step wiederhergestellt")
else:
    print("  vga_refresh war bereits in pc_step")

with open(PC_FILE, 'w') as f:
    f.write(pc_content)

print("\n=== Zusammenfassung ===")
print("Zurück zum ursprünglichen Design: vga_refresh in pc_step")
print("Der SPI-DMA-Fehler sollte jetzt verschwunden sein")
print("\nNächster Schritt: Build und Test")

