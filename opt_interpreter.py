#!/usr/bin/env python3
import re
p = 'esp/main/CMakeLists.txt'
cm = open(p).read()
m = re.search(r'set_source_files_properties\([^)]*vga\.c[^)]*\)', cm, re.S)
if m:
    spec = m.group(0)
    prefix = re.search(r'([\w./_-]*)vga\.c', spec).group(1)
    add = ''
    for f in ['i386.c', 'pc.c']:
        new = spec.replace(prefix + 'vga.c', prefix + f)
        if new not in cm:
            add += new + '\n'
    if add:
        cm += '\n# Interpreter-Optimierung (wie vga.c)\n' + add
        open(p, 'w').write(cm)
        print("OK: -O3 auch fuer i386.c/pc.c")
    else:
        print("i386.c/pc.c haben bereits O3")
else:
    print("WARN: vga.c-O3-Mechanismus nicht gefunden")
