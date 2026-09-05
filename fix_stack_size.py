#!/usr/bin/env python3
"""Reduziert den Stack des vga_refresh_task von 4096 auf 2048"""

ESP_MAIN = 'esp/main/esp_main.c'

with open(ESP_MAIN, 'r') as f:
    content = f.read()

# Reduziere Stack von 4096 auf 2048
old = 'xTaskCreatePinnedToCore(vga_refresh_task, "vga_refresh", 4096, NULL, 2, &vga_refresh_task_handle, 1);'
new = 'xTaskCreatePinnedToCore(vga_refresh_task, "vga_refresh", 2048, NULL, 2, &vga_refresh_task_handle, 1);'

if old in content:
    content = content.replace(old, new)
    print("✓ Stack-Größe auf 2048 reduziert")
else:
    print("Task-Start nicht gefunden")

with open(ESP_MAIN, 'w') as f:
    f.write(content)

