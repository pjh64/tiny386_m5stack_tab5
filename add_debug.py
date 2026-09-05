#!/usr/bin/env python3
"""
Fügt effizientes Debug-Logging hinzu (alle 100 Frames, 1 Zeile pro Log)
"""

# === 1. esp_main.c: display_task Debug ===
with open('esp/main/esp_main.c', 'r') as f:
    content = f.read()

# Ersetze das Performance-Logging in display_task
old_perf = '''		/* Performance-Messung */
		static int pc = 0; static int64_t pacc = 0;
		pacc += t2 - t0;
		if (++pc >= 100) {
			ESP_LOGW("PERF", "disp fps=%d avg us: memcpy=0 transpose=%lld draw=%lld",
				(int)(100000000LL / (pacc / pc)),
				(long long)(pacc / pc), 0LL);
			pc = 0; pacc = 0;
		}'''

new_perf = '''		/* Performance-Messung (kompakt, alle 100 Frames) */
		static int pc = 0; static int64_t pacc = 0;
		static int64_t t_ppa_acc = 0, t_copy_acc = 0;
		int64_t t_ppa = t2 - t0;
		int64_t t_copy = esp_timer_get_time() - t2;
		pacc += t_ppa + t_copy;
		t_ppa_acc += t_ppa;
		t_copy_acc += t_copy;
		if (++pc >= 100) {
			int fps = (int)(100000000LL / (pacc / pc));
			ESP_LOGW("PERF", "DISP fps=%d | ppa=%lldus copy=%lldus | res=%dx%d",
				fps,
				(long long)(t_ppa_acc / pc),
				(long long)(t_copy_acc / pc),
				LCD_WIDTH, LCD_HEIGHT);
			pc = 0; pacc = 0; t_ppa_acc = 0; t_copy_acc = 0;
		}'''

content = content.replace(old_perf, new_perf)

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)
print("✓ esp_main.c: display_task Debug hinzugefügt")

# === 2. lcd_m5stack_tab5.c: vga_task Debug ===
with open('esp/main/lcd_m5stack_tab5.c', 'r') as f:
    content = f.read()

# Finde das vga_step Timing-Log und ersetze es
old_vga_log = '''        /* Performance-Messung */
        static int vc = 0; static int64_t vacc = 0;
        vacc += vb - va;
        if (++vc >= 100) {
            ESP_LOGW("PERF", "vga_step avg us=%lld", (long long)(vacc / vc));
            vc = 0; vacc = 0;
        }'''

new_vga_log = '''        /* Performance-Messung (kompakt, alle 100 Frames) */
        static int vc = 0; static int64_t vacc = 0;
        static int64_t t_refresh_acc = 0;
        int64_t vb = esp_timer_get_time();
        vacc += vb - va;
        if (++vc >= 100) {
            ESP_LOGW("PERF", "VGA step=%lldus | refresh=%lldus | res=%dx%d bpp=%d",
                (long long)(vacc / vc),
                (long long)(t_refresh_acc / vc),
                globals.pc->vga->vbe_regs[1],  /* XRES */
                globals.pc->vga->vbe_regs[2],  /* YRES */
                globals.pc->vga->vbe_regs[3]); /* BPP */
            vc = 0; vacc = 0; t_refresh_acc = 0;
        }'''

content = content.replace(old_vga_log, new_vga_log)

# Falls das nicht gefunden wurde, versuche eine andere Variante
if 'vga_step avg us' in content and 'VGA step=' not in content:
    # Finde die Zeile mit dem Log und ersetze sie
    import re
    pattern = r'ESP_LOGW\("PERF", "vga_step avg us=%lld", \(long long\)\(vacc / vc\)\);'
    replacement = '''ESP_LOGW("PERF", "VGA step=%lldus | res=%dx%d bpp=%d",
                (long long)(vacc / vc),
                globals.pc->vga->vbe_regs[1],  /* XRES */
                globals.pc->vga->vbe_regs[2],  /* YRES */
                globals.pc->vga->vbe_regs[3]); /* BPP */'''
    content = re.sub(pattern, replacement, content)
    print("✓ lcd_m5stack_tab5.c: vga_task Debug hinzugefügt (Variante 2)")
else:
    print("✓ lcd_m5stack_tab5.c: vga_task Debug hinzugefügt")

with open('esp/main/lcd_m5stack_tab5.c', 'w') as f:
    f.write(content)

# === 3. vga.c: vga_graphic_refresh Timing ===
with open('vga.c', 'r') as f:
    content = f.read()

# Füge Timing-Messung am Anfang von vga_graphic_refresh hinzu
old_refresh_start = '''static void vga_graphic_refresh(VGAState *s,
                                SimpleFBDrawFunc *redraw_func, void *opaque,
                                int full_update)
{
    FBDevice *fb_dev = s->fb_dev;'''

new_refresh_start = '''static void vga_graphic_refresh(VGAState *s,
                                SimpleFBDrawFunc *redraw_func, void *opaque,
                                int full_update)
{
    int64_t t_start = esp_timer_get_time();
    FBDevice *fb_dev = s->fb_dev;'''

content = content.replace(old_refresh_start, new_refresh_start)

# Füge Timing-Messung vor dem redraw_func hinzu
old_redraw = '''    redraw_func(opaque, 0, 0, fb_dev->width, fb_dev->height);
}

static void simplefb_clear'''

new_redraw = '''    int64_t t_end = esp_timer_get_time();
    static int64_t t_refresh_total = 0;
    static int refresh_count = 0;
    t_refresh_total += (t_end - t_start);
    if (++refresh_count >= 100) {
        fprintf(stderr, "REFRESH avg=%lldus w=%d h=%d bpp=%d\\n",
                (long long)(t_refresh_total / refresh_count),
                fb_dev->width, fb_dev->height,
                s->vbe_regs[3]);
        t_refresh_total = 0;
        refresh_count = 0;
    }
    redraw_func(opaque, 0, 0, fb_dev->width, fb_dev->height);
}

static void simplefb_clear'''

content = content.replace(old_redraw, new_redraw)

with open('vga.c', 'w') as f:
    f.write(content)
print("✓ vga.c: vga_graphic_refresh Timing hinzugefügt")

print("\n=== Debug-System installiert ===")
print("Alle 100 Frames wird 1 Zeile pro Komponente geloggt:")
print("  VGA: step-Zeit, Auflösung, BPP")
print("  DISP: fps, PPA-Zeit, Copy-Zeit")
print("  REFRESH: Pixel-Konvertierungszeit")
