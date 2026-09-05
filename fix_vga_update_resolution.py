import re

with open('esp/main/esp_main.c', 'r') as f:
    content = f.read()

# 1. Füge extern-Deklaration hinzu
extern_decl = '''extern void pc_vga_step(void *pc);
extern void lcd_update_vga_resolution(int width, int height);
'''

content = content.replace(
    'extern void pc_vga_step(void *pc);',
    extern_decl
)

# 2. Finde vga_task und füge Auflösungs-Update hinzu
# Suche nach dem Aufruf von pc_vga_step in der while-Schleife
old_vga_loop = '''    while (1) {
        int64_t va = esp_timer_get_time();
        pc_vga_step(globals.pc);'''

new_vga_loop = '''    while (1) {
        /* Aktualisiere VGA-Auflösung für PPA-Crop */
        if (globals.pc && globals.pc->vga) {
            int w = globals.pc->vga->vbe_regs[VBE_DISPI_INDEX_XRES];
            int h = globals.pc->vga->vbe_regs[VBE_DISPI_INDEX_YRES];
            if (w > 0 && h > 0) {
                lcd_update_vga_resolution(w, h);
            }
        }
        
        int64_t va = esp_timer_get_time();
        pc_vga_step(globals.pc);'''

content = content.replace(old_vga_loop, new_vga_loop)

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)

print("✓ esp_main.c: VGA-Auflösungs-Update in vga_task hinzugefügt")
