#!/usr/bin/env python3
import re

# --- 1. vga.c: Catch-up in vga_step (alle faelligen Phasen in EINEM Call) ---
with open('vga.c', 'r') as f:
    c = f.read()
a = c.index('int vga_step(VGAState *s)')
b = c.index('void vga_refresh')
seg = c[a:b]
seg2 = seg.replace('if (after_eq(now, s->retrace_time)) {',
                   'while (after_eq(now, s->retrace_time)) {', 1)
seg2 = seg2.replace('s->retrace_time = now + 833;', 's->retrace_time += 833;')
seg2 = seg2.replace('s->retrace_time = now + RETRACE_INTERVAL_US;',
                    's->retrace_time += RETRACE_INTERVAL_US;')
seg2 += '\nint vga_is_idle(VGAState *s)\n{\n\treturn !after_eq(get_uticks(), s->retrace_time);\n}\n\n'
c = c[:a] + seg2 + c[b:]
with open('vga.c', 'w') as f:
    f.write(c)
print("OK vga.c: while-Catch-up + vga_is_idle")

# --- 2. vga.h: Deklaration ---
with open('vga.h', 'r') as f:
    h = f.read()
assert 'int vga_step(VGAState *vga);' in h
h = h.replace('int vga_step(VGAState *vga);',
              'int vga_step(VGAState *vga);\nint vga_is_idle(VGAState *vga);')
with open('vga.h', 'w') as f:
    f.write(h)
print("OK vga.h")

# --- 3. pc.c: Wrapper ---
with open('pc.c', 'r') as f:
    p = f.read()
assert 'void pc_step(PC *pc)' in p
p = p.replace('void pc_step(PC *pc)',
              'int pc_vga_idle(void *o)\n{\n\tPC *pc = o;\n\treturn vga_is_idle(pc->vga);\n}\n\nvoid pc_step(PC *pc)', 1)
with open('pc.c', 'w') as f:
    f.write(p)
print("OK pc.c")

# --- 4. lcd_m5stack_tab5.c: adaptives Pacing statt fixer 10ms ---
with open('esp/main/lcd_m5stack_tab5.c', 'r') as f:
    l = f.read()
assert 'extern void pc_vga_step(void *pc);' in l
l = l.replace('extern void pc_vga_step(void *pc);',
              'extern void pc_vga_step(void *pc);\nextern int pc_vga_idle(void *pc);')
assert 'vTaskDelay(10 / portTICK_PERIOD_MS);' in l
l = l.replace('vTaskDelay(10 / portTICK_PERIOD_MS);',
              'if (pc_vga_idle(globals.pc)) vTaskDelay(1);')
with open('esp/main/lcd_m5stack_tab5.c', 'w') as f:
    f.write(l)
print("OK lcd: adaptives Pacing")
