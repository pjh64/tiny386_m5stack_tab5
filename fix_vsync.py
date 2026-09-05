import re

# 1. Füge VSync-Semaphore zu esp_main.c hinzu
with open('esp/main/esp_main.c', 'r') as f:
    content = f.read()

# Füge VSync-Semaphore Deklaration hinzu
vsync_decl = '''static ppa_client_handle_t ppa_srm_handle = NULL;
static volatile bool g_no_rotate = false;   /* Benchmark: Rotation aus */
static SemaphoreHandle_t vsync_sem = NULL;  /* VSync-Synchronisation */'''

content = content.replace(
    'static ppa_client_handle_t ppa_srm_handle = NULL;\nstatic volatile bool g_no_rotate = false;',
    vsync_decl
)

# 2. Erstelle VSync-Callback-Funktion
vsync_callback = '''
/* VSync-Interrupt-Callback: Signalisiert dass Vertical Blank begonnen hat */
static bool IRAM_ATTR on_vsync_callback(esp_lcd_panel_handle_t panel, 
                                        const esp_lcd_dpi_panel_event_data_t *edata, 
                                        void *user_ctx)
{
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    xSemaphoreGiveFromISR(vsync_sem, &xHigherPriorityTaskWoken);
    return xHigherPriorityTaskWoken == pdTRUE;
}

'''

# Füge die Callback-Funktion vor display_task ein
content = content.replace('static void display_task(void *arg)', vsync_callback + 'static void display_task(void *arg)')

# 3. Initialisiere VSync-Semaphore und registriere Callback in vga_task
old_display_init = '''    xEventGroupSetBits(global_event_group, BIT1);
    xEventGroupWaitBits(global_event_group, BIT0, pdFALSE, pdFALSE, portMAX_DELAY);

    while (1) {'''

new_display_init = '''    /* Initialisiere VSync-Synchronisation */
    vsync_sem = xSemaphoreCreateBinary();
    if (vsync_sem == NULL) {
        ESP_LOGE(TAG, "Failed to create vsync semaphore");
        vTaskDelete(NULL);
    }
    
    /* Registriere VSync-Callback */
    esp_lcd_dpi_panel_event_callbacks_t cbs = {
        .on_vsync = on_vsync_callback,
    };
    esp_lcd_dpi_panel_register_event_callbacks(globals.panel, &cbs, NULL);
    ESP_LOGI(TAG, "VSync callback registered");

    xEventGroupSetBits(global_event_group, BIT1);
    xEventGroupWaitBits(global_event_group, BIT0, pdFALSE, pdFALSE, portMAX_DELAY);

    while (1) {'''

content = content.replace(old_display_init, new_display_init)

# 4. Füge VSync-Warten vor PPA-Operation hinzu
old_ppa_call = '''        int64_t t0 = esp_timer_get_time();
        int64_t t1 = t0;   /* memcpy entfaellt */

        if (ppa_srm_handle) {'''

new_ppa_call = '''        /* Warte auf VBlank bevor wir den Framebuffer aktualisieren */
        if (vsync_sem != NULL) {
            xSemaphoreTake(vsync_sem, portMAX_DELAY);
        }
        
        int64_t t0 = esp_timer_get_time();
        int64_t t1 = t0;   /* memcpy entfaellt */

        if (ppa_srm_handle) {'''

content = content.replace(old_ppa_call, new_ppa_call)

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)

print("✓ VSync-Synchronisation implementiert")
