import sys

# === 1. VGA-STATE ERWEITERN: Dirty-Tracking hinzufügen ===

vga_file = 'vga.c'
with open(vga_file, 'r', encoding='utf-8') as f:
    vga_content = f.read()

# Füge dirty_lines Array zur VGAState Struktur hinzu
vga_state_insert = '''
    /* Dirty tracking for optimization */
    uint8_t *dirty_lines;
    int dirty_lines_size;
    uint32_t vram_size;
'''

# Finde das Ende der VGAState Struktur (vor dem };)
vga_struct_end = vga_content.find('};\n\nuint32_t get_uticks();')
if vga_struct_end == -1:
    print("Fehler: Konnte VGAState-Struktur-Ende nicht finden")
    sys.exit(1)

vga_content = vga_content[:vga_struct_end] + vga_state_insert + vga_content[vga_struct_end:]

# === 2. VGA_INIT ERWEITERN: Dirty-Array allokieren ===

vga_init_code = '''
VGAState *vga_init(uint8_t *vga_ram_base, int vga_ram_size,
                   uint8_t *frame_buffer, int width, int height)
{
    VGAState *s;
    int i;

    s = calloc(1, sizeof(VGAState));
    if (!s)
        return NULL;

    s->fb_dev = calloc(1, sizeof(FBDevice));
    if (!s->fb_dev) {
        free(s);
        return NULL;
    }
    
    // Dirty tracking initialization
    s->vram_size = vga_ram_size;
    s->dirty_lines_size = (vga_ram_size / 640); // Max lines
    s->dirty_lines = calloc(1, s->dirty_lines_size);
    if (!s->dirty_lines) {
        free(s->fb_dev);
        free(s);
        return NULL;
    }
    memset(s->dirty_lines, 1, s->dirty_lines_size); // Mark all as dirty initially
'''

vga_init_start = vga_content.find('VGAState *vga_init(uint8_t *vga_ram_base')
if vga_init_start == -1:
    print("Fehler: Konnte vga_init Funktion nicht finden")
    sys.exit(1)

vga_init_end = vga_content.find('}\n\n', vga_init_start)
vga_content = vga_content[:vga_init_start] + vga_init_code + vga_content[vga_init_end+3:]

# === 3. VGA_MEM_WRITE ERWEITERN: Dirty-Flag setzen ===

# Funktion um Zeile aus Adresse zu berechnen
dirty_mark_func = '''
static inline void mark_line_dirty(VGAState *s, uint32_t addr)
{
    // Calculate line number from address
    // For 800x600@32bpp: line = addr / (800 * 4)
    // For 640x480@32bpp: line = addr / (640 * 4)
    // General: line = addr / bytes_per_line
    int bpp = s->vbe_regs[VBE_DISPI_INDEX_BPP];
    int width = s->vbe_regs[VBE_DISPI_INDEX_XRES];
    if (width == 0) width = 640; // Default fallback
    if (bpp == 0) bpp = 8;
    
    int bytes_per_line = width * (bpp / 8);
    int line = addr / bytes_per_line;
    
    if (line < s->dirty_lines_size) {
        s->dirty_lines[line] = 1;
    }
}

'''

# Füge diese Funktion vor vga_mem_write ein
vga_mem_write_start = vga_content.find('void vga_mem_write(VGAState *s')
if vga_mem_write_start == -1:
    print("Fehler: Konnte vga_mem_write nicht finden")
    sys.exit(1)

vga_content = vga_content[:vga_mem_write_start] + dirty_mark_func + vga_content[vga_mem_write_start:]

# Füge mark_line_dirty Aufruf am Ende von vga_mem_write hinzu
# Finde das Ende von vga_mem_write (vor der nächsten Funktion)
vga_mem_write_end = vga_content.find('}\n\nvoid', vga_mem_write_start)
if vga_mem_write_end == -1:
    vga_mem_write_end = vga_content.find('}\n\nstatic', vga_mem_write_start)

# Füge den Aufruf vor dem schließenden } ein
mark_call = '''
    // Mark this line as dirty
    mark_line_dirty(s, addr);
}
'''
vga_content = vga_content[:vga_mem_write_end] + mark_call + vga_content[vga_mem_write_end+2:]

# === 4. VGA_GRAPHIC_REFRESH OPTIMIEREN: Nur dirty Zeilen konvertieren ===

# Finde vga_graphic_refresh
vga_refresh_start = vga_content.find('static void vga_graphic_refresh(VGAState *s')
if vga_refresh_start == -1:
    print("Fehler: Konnte vga_graphic_refresh nicht finden")
    sys.exit(1)

# Ersetze die Haupt-Schleife mit einer optimierten Version
# Suche nach der for-Schleife die über alle y iteriert
old_loop = '''    for (int y = 0; y < h; y++) {'''

new_loop = '''    // Optimized: only process dirty lines or all if full_update
    if (full_update) {
        memset(s->dirty_lines, 1, h);
    }
    
    for (int y = 0; y < h; y++) {
        // Skip non-dirty lines unless full_update
        if (!full_update && !s->dirty_lines[y]) {
            continue;
        }
'''

vga_content = vga_content.replace(old_loop, new_loop, 1)

# Füge dirty_lines Reset am Ende der Funktion hinzu (vor dem redraw_func Aufruf)
redraw_call = 'redraw_func(opaque, 0, 0, fb_dev->width, fb_dev->height);'
reset_dirty = '''        // Clear dirty flags for processed lines
        if (!full_update) {
            for (int y = 0; y < h; y++) {
                s->dirty_lines[y] = 0;
            }
        }
    
    '''
vga_content = vga_content.replace(redraw_call, reset_dirty + redraw_call)

# === 5. OFFSET-KORREKTUR: Vereinfache i0-Berechnung ===

# Finde die komplexe i0-Berechnung
old_offset = '''    int i0 = 0;
#if defined(SCALE_3_2) || defined(SCALE_2_1) || defined(SWAPXY)'''

new_offset = '''    int i0 = 0;
    
    // Simplified offset calculation
    // Center the VGA image on the LCD framebuffer
    if (fb_dev->width > w) {
        i0 += (fb_dev->width - w) / 2 * (BPP / 8);
    }
    if (fb_dev->height > h) {
        i0 += (fb_dev->height - h) / 2 * fb_dev->stride;
    }
    
#if defined(SCALE_3_2) || defined(SCALE_2_1) || defined(SWAPXY)'''

vga_content = vga_content.replace(old_offset, new_offset, 1)

# Schreibe die Datei
with open(vga_file, 'w', encoding='utf-8') as f:
    f.write(vga_content)

print("✓ vga.c optimiert: Dirty-Tracking + Offset-Korrektur")
print("✓ Erwartete Verbesserung: 42ms → ~5ms (80-90% schneller)")
print("✓ Flimmer-Problem sollte behoben sein")
