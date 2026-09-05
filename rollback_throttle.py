with open('pc.c', 'r', encoding='utf-8') as f:
    content = f.read()

# Ersetze die Throttle-Logik mit dem Original
old_code = '''void pc_vga_step(void *o)
{
	PC *pc = o;
	int refresh = vga_step(pc->vga);
	if (refresh) {
		// Throttle: vga_refresh nur alle 100ms (außer bei Modus-Wechsel)
		static uint32_t last_refresh_ms = 0;
		uint32_t now_ms = esp_timer_get_time() / 1000;
		
		bool do_refresh = false;
		if (pc->full_update == 1) {
			do_refresh = true;  // Echter Modus-Wechsel
		} else if ((now_ms - last_refresh_ms) > 100) {
			do_refresh = true;  // 100ms abgelaufen
		}
		
		if (do_refresh) {
			vga_refresh(pc->vga, pc->redraw, pc->redraw_data,
				    pc->full_update != 0);
			last_refresh_ms = now_ms;
			if (pc->full_update == 2)
				pc->full_update = 0;
		}
	}
}'''

new_code = '''void pc_vga_step(void *o)
{
	PC *pc = o;
	int refresh = vga_step(pc->vga);
	if (refresh) {
		vga_refresh(pc->vga, pc->redraw, pc->redraw_data,
			    pc->full_update != 0);
		if (pc->full_update == 2)
			pc->full_update = 0;
	}
}'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("✓ Throttle in pc.c entfernt")
else:
    print("⚠ Throttle-Code nicht gefunden, versuche alternative Suche...")
    # Versuche eine flexiblere Suche
    import re
    pattern = r'void pc_vga_step\(void \*o\)\s*\{[^}]+if \(refresh\) \{.*?\n\t\}\n\}'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_code, content, flags=re.DOTALL)
        print("✓ Throttle in pc.c entfernt (alternative Methode)")
    else:
        print("✗ FEHLER: Konnte Throttle nicht finden")

with open('pc.c', 'w', encoding='utf-8') as f:
    f.write(content)
