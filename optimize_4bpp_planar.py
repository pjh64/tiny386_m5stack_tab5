#!/usr/bin/env python3
"""
Optimiert die 4bpp-Planar-Konvertierung mit 8-Pixel-Batching
"""

with open('vga.c', 'r') as f:
    lines = f.readlines()

# Finde den shift_control == 0 Block (8bpp planar)
fast_path_8bpp = '''                if (plane_mask == 1) {
                    if (s->comp_ntsc) {
                        if (!(x1 & 3)) {
                            int k = vram[addr + 4 * (x1 >> 3)];
                            if (!(x1 & 4))
                                k >>= 4;
                            color_comp = ntsc_color_lut[k & 0xf];
                        }
                        color = color_comp;
                    } else {
                        int k = ((vram[addr + 4 * (x1 >> 3)] >> (7 - (x1 & 7))) & 1);
                        color = palette[k];
                    }
                } else {
                    int k = ((vram[addr + 4 * (x1 >> 3)] >> (7 - (x1 & 7))) & 1) << 0;
                    k |= ((vram[addr + 4 * (x1 >> 3) + 1] >> (7 - (x1 & 7))) & 1) << 1;
                    k |= ((vram[addr + 4 * (x1 >> 3) + 2] >> (7 - (x1 & 7))) & 1) << 2;
                    k |= ((vram[addr + 4 * (x1 >> 3) + 3] >> (7 - (x1 & 7))) & 1) << 3;
                    color = palette[k];
                }'''

# Suche den Block
for i, line in enumerate(lines):
    if 'if (shift_control == 0)' in line and i > 1100 and i < 1200:
        # Ersetze die nächsten 20 Zeilen mit Fast-Path
        indent = ' ' * (len(line) - len(line.lstrip()))
        
        # Original-Block finden
        j = i + 1
        while j < len(lines) and '}' not in lines[j]:
            j += 1
        j += 1  # schließende Klammer
        
        # Fast-Path einfügen
        new_code = [
            f'{indent}if (shift_control == 0 && xdiv == 1) {{\n',
            f'{indent}    /* Fast-Path: 8-Pixel-Batching */\n',
            f'{indent}    if (plane_mask == 1 && !s->comp_ntsc) {{\n',
            f'{indent}        for (int x = 0; x < w; x += 8) {{\n',
            f'{indent}            uint32_t addr_byte = addr + 4 * (x >> 3);\n',
            f'{indent}            uint8_t p0 = vram[addr_byte];\n',
            f'{indent}            uint32_t base_i = (BPP / 8) * (y * fb_dev->width + x) + i0;\n',
            f'{indent}            for (int bit = 7; bit >= 0; bit--) {{\n',
            f'{indent}                int k = (p0 >> bit) & 1;\n',
            f'{indent}                uint32_t color = palette[k];\n',
            f'{indent}                int i = base_i + (BPP / 8) * (7 - bit);\n',
            f'#if BPP == 32\n',
            f'{indent}                fb_dev->fb_data[i + 0] = color;\n',
            f'{indent}                fb_dev->fb_data[i + 1] = color >> 8;\n',
            f'{indent}                fb_dev->fb_data[i + 2] = color >> 16;\n',
            f'{indent}                fb_dev->fb_data[i + 3] = color >> 24;\n',
            f'#elif BPP == 16\n',
            f'{indent}                fb_dev->fb_data[i + 0] = color;\n',
            f'{indent}                fb_dev->fb_data[i + 1] = color >> 8;\n',
            f'#endif\n',
            f'{indent}            }}\n',
            f'{indent}        }}\n',
            f'{indent}    }} else {{\n',
            f'{indent}        for (int x = 0; x < w; x += 8) {{\n',
            f'{indent}            uint32_t addr_byte = addr + 4 * (x >> 3);\n',
            f'{indent}            uint8_t p0 = vram[addr_byte];\n',
            f'{indent}            uint8_t p1 = vram[addr_byte + 1];\n',
            f'{indent}            uint8_t p2 = vram[addr_byte + 2];\n',
            f'{indent}            uint8_t p3 = vram[addr_byte + 3];\n',
            f'{indent}            uint32_t base_i = (BPP / 8) * (y * fb_dev->width + x) + i0;\n',
            f'{indent}            for (int bit = 7; bit >= 0; bit--) {{\n',
            f'{indent}                int k = ((p0 >> bit) & 1) |\n',
            f'{indent}                        (((p1 >> bit) & 1) << 1) |\n',
            f'{indent}                        (((p2 >> bit) & 1) << 2) |\n',
            f'{indent}                        (((p3 >> bit) & 1) << 3);\n',
            f'{indent}                uint32_t color = palette[k];\n',
            f'{indent}                int i = base_i + (BPP / 8) * (7 - bit);\n',
            f'#if BPP == 32\n',
            f'{indent}                fb_dev->fb_data[i + 0] = color;\n',
            f'{indent}                fb_dev->fb_data[i + 1] = color >> 8;\n',
            f'{indent}                fb_dev->fb_data[i + 2] = color >> 16;\n',
            f'{indent}                fb_dev->fb_data[i + 3] = color >> 24;\n',
            f'#elif BPP == 16\n',
            f'{indent}                fb_dev->fb_data[i + 0] = color;\n',
            f'{indent}                fb_dev->fb_data[i + 1] = color >> 8;\n',
            f'#endif\n',
            f'{indent}            }}\n',
            f'{indent}        }}\n',
            f'{indent}    }}\n',
            f'{indent}}} else if (shift_control == 1 && xdiv == 1) {{\n',
            f'{indent}    /* Fast-Path: 4-Pixel-Batching für 4bpp */\n',
            f'{indent}    for (int x = 0; x < w; x += 4) {{\n',
            f'{indent}        uint32_t addr_byte = addr + 4 * (x >> 3);\n',
            f'{indent}        uint8_t byte0 = vram[addr_byte + ((x & 4) >> 2)];\n',
            f'{indent}        uint8_t byte1 = vram[addr_byte + (((x + 2) & 4) >> 2)];\n',
            f'{indent}        uint32_t base_i = (BPP / 8) * (y * fb_dev->width + x) + i0;\n',
            f'{indent}        for (int j = 0; j < 4; j++) {{\n',
            f'{indent}            uint8_t byte = (j < 2) ? byte0 : byte1;\n',
            f'{indent}            int shift = 6 - 2 * ((x + j) & 3);\n',
            f'{indent}            int k = (byte >> shift) & 3;\n',
            f'{indent}            uint32_t color = palette[k];\n',
            f'{indent}            int i = base_i + (BPP / 8) * j;\n',
            f'#if BPP == 32\n',
            f'{indent}            fb_dev->fb_data[i + 0] = color;\n',
            f'{indent}            fb_dev->fb_data[i + 1] = color >> 8;\n',
            f'{indent}            fb_dev->fb_data[i + 2] = color >> 16;\n',
            f'{indent}            fb_dev->fb_data[i + 3] = color >> 24;\n',
            f'#elif BPP == 16\n',
            f'{indent}            fb_dev->fb_data[i + 0] = color;\n',
            f'{indent}            fb_dev->fb_data[i + 1] = color >> 8;\n',
            f'#endif\n',
            f'{indent}        }}\n',
            f'{indent}    }}\n',
            f'{indent}}} else {{\n',
        ]
        
        lines[i:j] = new_code
        print(f"Fast-Path für shift_control == 0/1 bei Zeile {i} eingefügt")
        break

with open('vga.c', 'w') as f:
    f.writelines(lines)

print("✓ 4bpp-Planar-Fast-Path implementiert")
print("  - 8-Pixel-Batching für 8bpp planar")
print("  - 4-Pixel-Batching für 4bpp planar")
print("  - Erwartung: 95ms → ~10ms")
