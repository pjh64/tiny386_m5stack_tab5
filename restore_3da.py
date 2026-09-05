#!/usr/bin/env python3
with open('vga.c', 'r') as f:
    c = f.read()

old = '''        case 0x3ba:
        case 0x3da:
            /* just toggle to fool polling */
//            s->st01 ^= ST01_V_RETRACE | ST01_DISP_ENABLE;
            val = s->st01;
            s->ar_flip_flop = 0;
            break;'''

new = '''        case 0x3ba:
        case 0x3da:
            /* Fast-forward through entire retrace cycle */
            {
                uint32_t now = get_uticks();
                if (s->st01 & ST01_V_RETRACE) {
                    /* Guest wartet auf VRETRACE-clear (Phase 2->0) */
                    s->st01 &= ~(ST01_V_RETRACE | ST01_DISP_ENABLE);
                    s->retrace_phase = 0;
                    s->retrace_time = now + RETRACE_INTERVAL_US;
                } else {
                    /* Guest wartet auf VRETRACE-set (Phase 0->2) */
                    s->st01 |= ST01_DISP_ENABLE | ST01_V_RETRACE;
                    s->retrace_phase = 2;
                    s->retrace_time = now + 833;
                }
            }
            val = s->st01;
            s->ar_flip_flop = 0;
            break;'''

assert old in c, "0x3da-Handler nicht im Git-Zustand gefunden"
c = c.replace(old, new, 1)

with open('vga.c', 'w') as f:
    f.write(c)
print("OK: Port 0x3da Fast-Forward wiederhergestellt")
