#!/usr/bin/env python3
with open('pc.c', 'r') as f:
    c = f.read()

old = '''void pc_vga_step(void *o)
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

new = '''extern uint32_t get_uticks(void);
void pc_vga_step(void *o)
{
	PC *pc = o;
	int refresh = vga_step(pc->vga);
	if (refresh) {
		uint32_t r0 = get_uticks();
		vga_refresh(pc->vga, pc->redraw, pc->redraw_data,
			    pc->full_update != 0);
		uint32_t r1 = get_uticks();
		static int rc = 0; static uint32_t racc = 0, rlast = 0;
		racc += r1 - r0; rc++;
		if (r1 - rlast > 1000000) {
			fprintf(stderr, "VGA_REFRESH avg us=%u (n=%d)\\n", racc / rc, rc);
			rc = 0; racc = 0; rlast = r1;
		}
		if (pc->full_update == 2)
			pc->full_update = 0;
	}
}'''

assert old in c, "pc_vga_step nicht gefunden"
c = c.replace(old, new, 1)
with open('pc.c', 'w') as f:
    f.write(c)
print("OK: VGA_REFRESH-Timing in pc.c")
