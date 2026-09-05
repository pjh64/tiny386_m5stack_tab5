import re

with open('esp/main/esp_main.c', 'r') as f:
    content = f.read()

# 1. Semaphore und Callback als globale Variablen
old_globals = """static uint16_t *disp_src = NULL;
static uint16_t *rot_buf = NULL;
static uint16_t *snap_buf = NULL;
static ppa_client_handle_t ppa_srm_handle = NULL;"""

new_globals = """static uint16_t *disp_src = NULL;
static uint16_t *rot_buf = NULL;
static uint16_t *snap_buf = NULL;
static ppa_client_handle_t ppa_srm_handle = NULL;
static SemaphoreHandle_t ppa_done_sem = NULL;

static bool ppa_trans_done_cb(ppa_client_handle_t ppa_client, ppa_event_data_t *event_data, void *user_data)
{
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    SemaphoreHandle_t sem = (SemaphoreHandle_t)user_data;
    xSemaphoreGiveFromISR(sem, &xHigherPriorityTaskWoken);
    return (xHigherPriorityTaskWoken == pdTRUE);
}"""

content = content.replace(old_globals, new_globals)

# 2. Callback registrieren
old_register = """        ppa_client_config_t ppa_config = {
            .oper_type = PPA_OPERATION_SRM,
        };
        ppa_register_client(&ppa_config, &ppa_srm_handle);"""

new_register = """        ppa_client_config_t ppa_config = {
            .oper_type = PPA_OPERATION_SRM,
        };
        ppa_register_client(&ppa_config, &ppa_srm_handle);
        
        ppa_done_sem = xSemaphoreCreateBinary();
        xSemaphoreGive(ppa_done_sem);
        
        ppa_event_callbacks_t cbs = {
            .on_trans_done = ppa_trans_done_cb,
        };
        ppa_client_register_event_callbacks(ppa_srm_handle, &cbs);"""

content = content.replace(old_register, new_register)

# 3. display_task: Non-Blocking Modus
old_blocking = """            .rotation_angle = PPA_SRM_ROTATION_ANGLE_90,
            .mirror_x = false,
            .mirror_y = false,
            .mode = PPA_TRANS_MODE_BLOCKING,
        };
        
        esp_err_t err = ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper);"""

new_nonblocking = """            .rotation_angle = PPA_SRM_ROTATION_ANGLE_90,
            .mirror_x = false,
            .mirror_y = false,
            .mode = PPA_TRANS_MODE_NON_BLOCKING,
            .user_data = ppa_done_sem,
        };
        
        xSemaphoreTake(ppa_done_sem, portMAX_DELAY);
        esp_err_t err = ppa_do_scale_rotate_mirror(ppa_srm_handle, &oper);
        if (err != ESP_OK) {
            xSemaphoreGive(ppa_done_sem);
        }"""

content = content.replace(old_blocking, new_nonblocking)

with open('esp/main/esp_main.c', 'w') as f:
    f.write(content)

print("OK: Non-Blocking PPA aktiviert")
