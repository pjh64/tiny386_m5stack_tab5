#!/usr/bin/env python3
"""
I/O-Port-Profiling für tiny386
Findet heraus welche I/O-Ports am häufigsten gelesen/geschrieben werden.
Das zeigt uns, worauf Windows 95 in den Busy-Loops wartet.
"""
import sys
import os
import shutil
from datetime import datetime

def backup_file(filename):
    backup = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filename, backup)
    print(f"✓ Backup: {backup}")

def main():
    # Prüfe welche Dateien die I/O-Funktionen enthalten
    files_to_check = ['i8254.c', 'i8259.c', 'vga.c', 'ide.c', 'misc.c', 'pc.c', 'i386.c']
    
    print("=== Suche nach I/O-Dispatch-Funktionen ===")
    for f in files_to_check:
        if os.path.exists(f):
            print(f"  ✓ {f} existiert")
        else:
            print(f"  ✗ {f} nicht gefunden")
    
    print("\n=== Hinweis ===")
    print("Um I/O-Ports zu profilen, müssen wir die IN/OUT-Instruktionen finden.")
    print("Diese sind in i386.c (Opcode 0xe4-0xe7, 0xec-0xef).")
    print("\nWir suchen nach den I/O-Handler-Funktionen:")
    
    # Suche nach I/O-Handlern in i386.c
    if os.path.exists('i386.c'):
        with open('i386.c', 'r') as f:
            content = f.read()
        
        # Suche nach IN/OUT Implementierungen
        io_patterns = ['io_read', 'io_write', 'inb', 'outb', 'read_io', 'write_io', 
                       'IO_READ', 'IO_WRITE', 'cpu_io_read', 'cpu_io_write']
        
        print("\n  Gefundene I/O-bezogene Funktionen/Variablen:")
        found = set()
        for pattern in io_patterns:
            if pattern in content:
                found.add(pattern)
        
        if found:
            for f_item in sorted(found):
                print(f"    - {f_item}")
        else:
            print("    Keine direkten I/O-Funktionen in i386.c gefunden")
            print("    Die I/O-Handler sind vermutlich in einer Callback-Struktur")
        
        # Suche nach Callback-Struktur
        if 'cb.' in content:
            print("\n  Callback-Struktur gefunden (cb.)")
            # Zeige die Callback-Definition
            import re
            cb_matches = re.findall(r'cb\.(\w+)', content)
            cb_unique = sorted(set(cb_matches))
            print(f"  Verwendete Callbacks: {', '.join(cb_unique[:20])}")

if __name__ == '__main__':
    main()
