#!/usr/bin/env python3
with open('esp/main/esp_main.c', 'r') as f:
    c = f.read()

def rep(old, new, n=1):
    global c
    assert c.count(old) >= n, "ANKER NICHT GEFUNDEN: " + old[:60]
    c = c.replace(old, new, n)

# 1. Semaphore + Callback + Benchmark nach g_no_rotate einfuegen
rep("static volatile bool g_no_rotate = false;",
    "static volatile bool g_no_rotate = false;\n"
    "static SemaphoreHandle_t ppa_done_sem = NULL;\n"
    "static bool ppa_trans_done_cb(ppa_client_handle_t h, ppa_event_data_t *e, void *u)\n"
    "{\n"
    "    BaseType_t w = pdFALSE;\n"
    "    xSemaphoreGiveFromISR((SemaphoreHandle_t)u, &w);\n"
    "    return w == pdTRUE;\n"
    "}\n"
    "static void ppa_benchmark(void)\n"
    "{\n"
    "    if (!ppa_srm_handle) return;\n"
    "    ppa_srm_oper_config_t o;\n"
    "    int64_t a, b;\n"
    "    for (int i = 0; i < LCD_WIDTH * LCD_HEIGHT; i++) rot_buf[i] = (uint16_t)((i * 2654435761u) >> 16);\n"
    "    esp_cache_msync(rot_buf, LCD_WIDTH * LCD_HEIGHT * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);\n"
    "    a = esp_timer_get_time();\n"
    "    memcpy(snap_buf, rot_buf, LCD_WIDTH * LCD_HEIGHT * 2);\n"
    "    esp_cache_msync(snap_buf, LCD_WIDTH * LCD_HEIGHT * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);\n"
    "    b = esp_timer_get_time();\n"
    "    ESP_LOGW(\"PPABENCH\", \"BUS cpu-memcpy 1.8MB: %lld us (~%d MB/s)\", (long long)(b - a), (int)((LCD_WIDTH * LCD_HEIGHT * 2) / (b - a)));\n"
    "    memset(&o, 0, sizeof(o));\n"
    "    o.in.buffer = rot_buf; o.in.pic_w = 720; o.in.pic_h = 480;\n"
    "    o.in.block_w = 720; o.in.block_h = 480; o.in.srm_cm = PPA_SRM_COLOR_MODE_RGB565;\n"
    "    o.out.buffer = snap_buf; o.out.srm_cm = PPA_SRM_COLOR_MODE_RGB565;\n"
    "    o.mode = PPA_TRANS_MODE_BLOCKING; o.user_data = ppa_done_sem;\n"
    "    o.scale_x = 1.0f; o.scale_y = 1.0f; o.rotation_angle = PPA_SRM_ROTATION_ANGLE_0;\n"
    "    o.out.buffer_size = (720 * 480 * 2 + 127) & ~127; o.out.pic_w = 720; o.out.pic_h = 480;\n"
    "    ppa_do_scale_rotate_mirror(ppa_srm_handle, &o);\n"
    "    a = esp_timer_get_time();\n"
    "    for (int i = 0; i < 5; i++) ppa_do_scale_rotate_mirror(ppa_srm_handle, &o);\n"
    "    b = esp_timer_get_time();\n"
    "    ESP_LOGW(\"PPABENCH\", \"BUS ppa-copy 720x480: %lld us\", (long long)((b - a) / 5));\n"
    "    o.out.buffer_size = (1280 * 720 * 2 + 127) & ~127; o.out.pic_w = 1280; o.out.pic_h = 720;\n"
    "    o.scale_x = 1280.0f / 720.0f; o.scale_y = 720.0f / 480.0f;\n"
    "    ppa_do_scale_rotate_mirror(ppa_srm_handle, &o);\n"
    "    a = esp_timer_get_time();\n"
    "    for (int i = 0; i < 5; i++) ppa_do_scale_rotate_mirror(ppa_srm_handle, &o);\n"
    "    b = esp_timer_get_time();\n"
    "    ESP_LOGW(\"PPABENCH\", \"SCALE 720x480->1280x720: %lld us\", (long long)((b - a) / 5));\n"
    "    o.out.buffer_size = (480 * 720 * 2 + 127) & ~127; o.out.pic_w = 480; o.out.pic_h = 720;\n"
    "    o.scale_x = 1.0f; o.scale_y = 1.0f; o.rotation_angle = PPA_SRM_ROTATION_ANGLE_270;\n"
    "    ppa_do_scale_rotate_mirror(ppa_srm_handle, &o);\n"
    "    a = esp_timer_get_time();\n"
    "    for (int i = 0; i < 5; i++) ppa_do_scale_rotate_mirror(ppa_srm_handle, &o);\n"
    "    b = esp_timer_get_time();\n"
    "    ESP_LOGW(\"PPABENCH\", \"ROTATE 720x480->480x720: %lld us\", (long long)((b - a) / 5));\n"
    "    o.out.buffer_size = (720 * 1280 * 2 + 127) & ~127; o.out.pic_w = 720; o.out.pic_h = 1280;\n"
    "    o.scale_x = 1280.0f / 720.0f; o.scale_y = 720.0f / 480.0f;\n"
    "    ppa_do_scale_rotate_mirror(ppa_srm_handle, &o);\n"
    "    a = esp_timer_get_time();\n"
    "    for (int i = 0; i < 5; i++) ppa_do_scale_rotate_mirror(ppa_srm_handle, &o);\n"
    "    b = esp_timer_get_time();\n"
    "    ESP_LOGW(\"PPABENCH\", \"FULL scale+rotate ->720x1280: %lld us\", (long long)((b - a) / 5));\n"
    "}\n")

# 2. Sem + Callback-Registrierung + Benchmark-Aufruf nach SRM-Registrierung
rep('ESP_LOGI("PPA", "SRM client registered");',
    'ESP_LOGI("PPA", "SRM client registered");\n'
    '\t\tppa_done_sem = xSemaphoreCreateBinary();\n'
    '\t\txSemaphoreGive(ppa_done_sem);\n'
    '\t\tppa_event_callbacks_t cbs = { .on_trans_done = ppa_trans_done_cb };\n'
    '\t\tppa_client_register_event_callbacks(ppa_srm_handle, &cbs);\n'
    '\t\tppa_benchmark();')

# 3. wait-Messung + Semaphore-Take vor PPA-Submit
rep("\t\t\tint64_t tc0 = esp_timer_get_time();",
    "\t\t\tint64_t tw0 = esp_timer_get_time();\n"
    "\t\t\txSemaphoreTake(ppa_done_sem, portMAX_DELAY);\n"
    "\t\t\tt_wait = esp_timer_get_time() - tw0;\n"
    "\t\t\tint64_t tc0 = esp_timer_get_time();")

# 4. Non-Blocking + user_data
rep("\t\t\toper.mode = PPA_TRANS_MODE_BLOCKING;",
    "\t\t\toper.mode = PPA_TRANS_MODE_NON_BLOCKING;\n"
    "\t\t\toper.user_data = ppa_done_sem;")

# 5. Bei Fehler: Sem zurueckgeben (kein Deadlock)
rep("\t\t\tif (perr != ESP_OK) {",
    "\t\t\tif (perr != ESP_OK) {\n"
    "\t\t\t\txSemaphoreGive(ppa_done_sem);")

# 6. t_wait/accc_wait in Timing-Infrastruktur
rep("int64_t t_cfg = 0, t_ppa = 0, t_edge = 0, t_sync = 0;",
    "int64_t t_cfg = 0, t_ppa = 0, t_edge = 0, t_sync = 0, t_wait = 0;")
rep("static int64_t acc_cfg = 0, acc_ppa = 0, acc_edge = 0, acc_sync = 0;",
    "static int64_t acc_cfg = 0, acc_ppa = 0, acc_edge = 0, acc_sync = 0, acc_wait = 0;")
rep("\t\tacc_sync += t_sync;",
    "\t\tacc_sync += t_sync;\n\t\tacc_wait += t_wait;")
rep("[cfg=%ld ppa=%ld edge=%ld sync=%ld]",
    "[cfg=%ld ppa=%ld wait=%ld edge=%ld sync=%ld]")
rep("(long)(acc_cfg / fc), (long)(acc_ppa / fc),",
    "(long)(acc_cfg / fc), (long)(acc_ppa / fc), (long)(acc_wait / fc),")
rep("acc_cfg = acc_ppa = acc_edge = acc_sync = 0;",
    "acc_cfg = acc_ppa = acc_edge = acc_sync = acc_wait = 0;")

with open('esp/main/esp_main.c', 'w') as f:
    f.write(c)
print("OK: Alle 10 Ersetzungen angewendet (Non-Blocking + Benchmark + wait-Feld)")
