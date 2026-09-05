#!/usr/bin/env python3
"""
Optimiert Port 0x3da Handler mit Zeitvorspul für Busy-Wait Schleifen
"""

with open('vga.c', 'r') as f:
    lines = f.readlines()

# Finde den Port 0x3da Handler
for i, line in enumerate(lines):
    if 'case 0x3ba:' in line and i+1 < len(lines) and 'case 0x3da:' in lines[i+1]:
        # Ersetze den Handler
        indent = ' ' * (len(line) - len(line.lstrip()))
        
        # Ersetze die nächsten Zeilen bis zum break
        j = i + 2
        while j < len(lines) and 'break;' not in lines[j]:
            j += 1
        
        # Erstelle den neuen Handler
        new_handler = [
            f'{indent}case 0x3ba:\n',
            f'{indent}case 0x3da:\n',
            f'{indent}    /* Fast-forward time if guest is polling for V_RETRACE */\n',
            f'{indent}    if (!(s->st01 & ST01_V_RETRACE)) {{\n',
            f'{indent}        /* Guest is waiting for VRETRACE, skip forward */\n',
            f'{indent}        uint32_t now = get_uticks();\n',
            f'{indent}        \n',
            f'{indent}        if (s->retrace_phase == 0) {{\n',
            f'{indent}            /* Phase 0: DISP_ENABLE active, need 833us to reach phase 1 */\n',
            f'{indent}            s->st01 |= ST01_DISP_ENABLE;\n',
            f'{indent}            s->retrace_phase = 1;\n',
            f'{indent}            s->retrace_time = now + 833;\n',
            f'{indent}        }}\n',
            f'{indent}        \n',
            f'{indent}        if (s->retrace_phase == 1) {{\n',
            f'{indent}            /* Phase 1: Set VRETRACE bit immediately */\n',
            f'{indent}            s->st01 |= ST01_V_RETRACE;\n',
            f'{indent}            s->retrace_phase = 2;\n',
            f'{indent}            s->retrace_time = now + 833;\n',
            f'{indent}        }}\n',
            f'{indent}    }}\n',
            f'{indent}    \n',
            f'{indent}    val = s->st01;\n',
            f'{indent}    s->ar_flip_flop = 0;\n',
            f'{indent}    break;\n',
        ]
        
        # Ersetze die Zeilen
        lines[i:j+1] = new_handler
        print(f"Port 0x3da Handler bei Zeile {i+1} optimiert")
        break

with open('vga.c', 'w') as f:
    f.writelines(lines)

print("✓ Port 0x3da Optimierung abgeschlossen")
