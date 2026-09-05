#!/usr/bin/env python3
with open('vga.c', 'r') as f:
    c = f.read()

# 1. vga_step: if -> while (Catch-up) + retrace_time += statt = now +
a = c.index('int vga_step(VGAState *s)')
b = c.index('void vga_refresh')
seg = c[a:b]
assert 'if (after_eq(now, s->retrace_time)) {' in seg, "vga_step Struktur unerwartet"
seg2 = seg.replace('if (after_eq(now, s->retrace_time)) {',
                   'while (after_eq(now, s->retrace_time)) {', 1)
seg2 = seg2.replace('s->retrace_time = now + 833;', 's->retrace_time += 833;')
seg2 = seg2.replace('s->retrace_time = now + RETRACE_INTERVAL_US;',
                    's->retrace_time += RETRACE_INTERVAL_US;')
seg2 += '\nint vga_is_idle(VGAState *s)\n{\n\treturn !after_eq(get_uticks(), s->retrace_time);\n}\n\n'
c = c[:a] + seg2 + c[b:]

with open('vga.c', 'w') as f:
    f.write(c)

print("OK: while-Catch-up + vga_is_idle wiederhergestellt")
print("Fast-Path vorhanden:", 'vga_draw_8bpp_planar_fast' in c)
