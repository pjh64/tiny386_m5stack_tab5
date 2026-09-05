#!/usr/bin/env python3
with open('esp/main/esp_main.c', 'r') as f:
    content = f.read()

bench_fn = '''
/* Startup-Benchmark: isoliert BUS / SCALE / ROTATE ohne Guest-Contention.
 * Vergleich mit Runtime-ppa-Zeit zeigt die Bus-Contention. */
static void ppa_benchmark(void)
{
    if (!ppa_srm_handle) return;

    for (int i = 0; i < LCD_WIDTH * LCD_HEIGHT; i++)
        rot_buf[i] = (uint16_t)((i * 2654435761u) >> 16);
    esp_cache_msync(rot_buf, LCD_WIDTH * LCD_HEIGHT * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);

    /* 1) BUS-Baseline: CPU memcpy 1.8MB PSRAM->PSRAM */
    int64_t t0 = esp_timer_get_time();
    memcpy(snap_buf, rot_buf, LCD_WIDTH * LCD_HEIGHT * 2);
    esp_cache_msync(snap_buf, LCD_WIDTH * LCD_HEIGHT * 2, ESP_CACHE_MSYNC_FLAG_TYPE_DATA);
    int64_t t1 = esp_timer_get_time();
    ESP_LOGW("PPABENCH", "BUS cpu-memcpy 1.8MB: %lld us (~%d MB/s)",
             (long long)(t1 - t0), (int)((LCD_WIDTH * LCD_HEIGHT * 2) / (t1 - t0)));

    ppa_srm_oper_config_t oper;
    memset(&oper, 0, sizeof(oper));
    oper.in.buffer = rot_buf;
    oper.in.pic_w = 720; oper.in.pic_h = 480;
    oper.in.block_w = 720; oper.in.block_h = 480;
    oper.in.srm_cm = PPA_SRM_COLOR_MODE_RGB565;
    oper.out.buffer = snap_buf;
    oper.out.srm_cm = PPA_SRM_COLOR_MODE_RGB565;
    oper.mode = PPA_TRANS_MODE_BLOCKING;
    oper.user_data = ppa_done_sem;

    /* 2) BUS: PPA pure Copy (DMA ohne scale/rot) */
    oper.out.buffer_size = (720 * 480 * 2 + 127) & ~127;
    oper.out.pic_w = 720; oper.out.pic_h = 480;
    oper.scale_x = 1.0f; oper.scale_y = 1.0f;
    oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_0;
    ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper); /* warmup */
    t0 = esp_timer_get_time();
    for (int i = 0; i < 5; i++) ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper);
    t1 = esp_timer_get_time();
    ESP_LOGW("PPABENCH", "BUS ppa-copy 720x480: %lld us", (long long)((t1 - t0) / 5));

    /* 3) SCALE: nur Skalierung 720x480 -> 1280x720 */
    oper.out.buffer_size = (1280 * 720 * 2 + 127) & ~127;
    oper.out.pic_w = 1280; oper.out.pic_h = 720;
    oper.scale_x = 1280.0f / 720.0f; oper.scale_y = 720.0f / 480.0f;
    ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper);
    t0 = esp_timer_get_time();
    for (int i = 0; i < 5; i++) ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper);
    t1 = esp_timer_get_time();
    ESP_LOGW("PPABENCH", "SCALE 720x480->1280x720: %lld us", (long long)((t1 - t0) / 5));

    /* 4) ROTATE: nur Rotation 270 */
    oper.out.buffer_size = (480 * 720 * 2 + 127) & ~127;
    oper.out.pic_w = 480; oper.out.pic_h = 720;
    oper.scale_x = 1.0f; oper.scale_y = 1.0f;
    oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_270;
    ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper);
    t0 = esp_timer_get_time();
    for (int i = 0; i < 5; i++) ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper);
    t1 = esp_timer_get_time();
    ESP_LOGW("PPABENCH", "ROTATE 720x480->480x720: %lld us", (long long)((t1 - t0) / 5));

    /* 5) FULL: wie echter Pfad (scale+rotate -> 720x1280) */
    oper.out.buffer_size = (720 * 1280 * 2 + 127) & ~127;
    oper.out.pic_w = 720; oper.out.pic_h = 1280;
    oper.scale_x = 1280.0f / 720.0f; oper.scale_y = 720.0f / 480.0f;
    oper.rotation_angle = PPA_SRM_ROTATION_ANGLE_270;
    ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper);
    t0 = esp_timer_get_time();
    for (int i = 0; i < 5; i++) ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper);
    t1 = esp_timer_get_time();
    ESP_LOGW("PPABENCH", "FULL scale+rotate ->720x1280: %lld us", (long long)((t1 - t0) / 5));
}
'''

# Funktion nach dem Callback einfuegen
anchor_cb = '''    xSemaphoreGiveFromISR(sem, &xHigherPriorityTaskWoken);
    return (xHigherPriorityTaskWoken == pdTRUE);
}'''
assert anchor_cb in content
content = content.replace(anchor_cb, anchor_cb + bench_fn)

# Aufruf nach Callback-Registrierung
anchor_call = '        ppa_client_register_event_callbacks(ppa_srm_handle, &cbs);'
assert anchor_call in content
content = content.replace(anchor_call, anchor_call + '\n        ppa_benchmark();')

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)
print("OK: ppa_benchmark() eingefuegt")
