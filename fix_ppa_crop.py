import re

with open('esp/main/esp_main.c', 'r') as f:
    content = f.read()

# 1. Füge globale Variablen für VGA-Auflösung hinzu
globals_section = '''static uint16_t *volatile disp_src = NULL;
static TaskHandle_t disp_task_handle = NULL;
static uint16_t *rot_buf = NULL;
static uint16_t *snap_buf = NULL;
static ppa_client_handle_t ppa_srm_handle = NULL;
static volatile bool g_no_rotate = false;   /* Benchmark: Rotation aus */

/* Dynamische VGA-Auflösung für PPA-Crop */
static volatile int g_vga_width = 640;
static volatile int g_vga_height = 480;'''

content = re.sub(
    r'static uint16_t \*volatile disp_src = NULL;.*?static volatile bool g_no_rotate = false;.*?\n',
    globals_section + '\n',
    content,
    flags=re.DOTALL
)

# 2. Ersetze den hartcodierten PPA-Crop mit dynamischer Berechnung
old_ppa_config = '''			/* Wie alter STRETCH-Pfad:
			 * Nimm den zentralen 720x480-Ausschnitt aus dem 1280x720 VGA-Framebuffer
			 * und strecke ihn auf Vollbild. */
			oper.in.block_offset_x = 280;
			oper.in.block_offset_y = 120;
			oper.in.block_w = 720;
			oper.in.block_h = 480;'''

new_ppa_config = '''			/* Dynamischer Crop basierend auf aktueller VGA-Auflösung */
			int vga_w = g_vga_width;
			int vga_h = g_vga_height;
			
			/* Clamp auf sinnvolle Werte */
			if (vga_w < 320) vga_w = 320;
			if (vga_w > LCD_WIDTH) vga_w = LCD_WIDTH;
			if (vga_h < 200) vga_h = 200;
			if (vga_h > LCD_HEIGHT) vga_h = LCD_HEIGHT;
			
			/* Berechne zentrierte Offsets */
			int offset_x = (LCD_WIDTH - vga_w) / 2;
			int offset_y = (LCD_HEIGHT - vga_h) / 2;
			
			oper.in.block_offset_x = offset_x;
			oper.in.block_offset_y = offset_y;
			oper.in.block_w = vga_w;
			oper.in.block_h = vga_h;'''

content = content.replace(old_ppa_config, new_ppa_config)

# 3. Füge Funktion zum Aktualisieren der VGA-Auflösung hinzu
update_func = '''
/* Aktualisiert die globale VGA-Auflösung aus den VBE-Registern */
void lcd_update_vga_resolution(int width, int height)
{
	g_vga_width = width;
	g_vga_height = height;
}

'''

# Füge die Funktion vor console_init ein
content = content.replace('Console *console_init', update_func + 'Console *console_init')

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)

print("✓ esp_main.c: Dynamischer PPA-Crop implementiert")
