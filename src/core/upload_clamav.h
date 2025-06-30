#ifndef CATZILLA_UPLOAD_CLAMAV_H
#define CATZILLA_UPLOAD_CLAMAV_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// ClamAV availability status
typedef enum {
    CLAMAV_STATUS_NOT_FOUND = 0,
    CLAMAV_STATUS_FOUND_DAEMON = 1,
    CLAMAV_STATUS_FOUND_BINARY = 2,
    CLAMAV_STATUS_DAEMON_RUNNING = 3
} clamav_availability_t;

// ClamAV system information
typedef struct {
    bool available;
    clamav_availability_t status;
    char* daemon_socket;        // /var/run/clamav/clamd.ctl
    char* binary_path;          // /usr/bin/clamdscan or /usr/bin/clamscan
    char* version;              // ClamAV version string
    bool daemon_running;        // Is clamd daemon running?
    uint32_t daemon_port;       // TCP port if using network
    char* config_path;          // Path to clamd.conf
} clamav_system_info_t;

// ClamAV scan result
typedef struct {
    bool is_infected;
    bool is_error;
    char* threat_name;
    double scan_time_seconds;
    char* engine_version;
    char* error_message;
    int exit_code;
    uint64_t file_size;
    char* scanned_file_path;
} clamav_scan_result_t;

// Windows-specific ClamAV information
#ifdef _WIN32
typedef struct {
    char install_path[260];     // MAX_PATH
    char version[64];
    bool is_service_installed;
    bool is_daemon_running;
    char service_executable[260];
    char config_path[260];
    char* pipe_name;            // Named pipe for communication
} windows_clamav_registry_info_t;
#endif

// Core functions
int catzilla_clamav_detect_system(clamav_system_info_t* info);
clamav_scan_result_t* catzilla_clamav_scan_file(const char* file_path);
void catzilla_clamav_cleanup_result(clamav_scan_result_t* result);
void catzilla_clamav_cleanup_system_info(clamav_system_info_t* info);

// System detection functions
bool catzilla_clamav_is_available(void);
const char* catzilla_clamav_get_version(void);
bool catzilla_clamav_daemon_running(void);

// Installation helper functions
const char* catzilla_clamav_get_install_instructions(void);
char* catzilla_clamav_get_platform_install_command(void);

// Connection testing
bool catzilla_test_clamd_connection(const char* socket_path);
bool catzilla_test_clamd_tcp_connection(const char* host, uint32_t port);

// Scanning functions
int catzilla_clamav_scan_buffer(const char* buffer, size_t buffer_size, clamav_scan_result_t* result);
int catzilla_clamav_scan_file_async(const char* file_path, void (*callback)(clamav_scan_result_t*));

// Configuration functions
int catzilla_clamav_load_config(const char* config_path);
bool catzilla_clamav_update_definitions(void);

// Platform-specific functions
#ifdef __linux__
int catzilla_clamav_detect_linux(clamav_system_info_t* info);
bool catzilla_clamav_start_daemon_systemd(void);
#endif

#ifdef __APPLE__
int catzilla_clamav_detect_macos(clamav_system_info_t* info);
bool catzilla_clamav_start_daemon_launchd(void);
#endif

#ifdef _WIN32
int catzilla_clamav_detect_windows(clamav_system_info_t* info);
int catzilla_detect_clamav_from_registry(windows_clamav_registry_info_t* info);
int catzilla_detect_clamav_powershell(windows_clamav_registry_info_t* info);
bool catzilla_clamav_start_service_windows(void);

// Windows named pipe functions
typedef struct {
    void* pipe_handle;          // HANDLE
    char pipe_name[256];
    uint32_t timeout_ms;
    bool is_connected;
} windows_clamav_pipe_t;

int catzilla_clamav_connect_named_pipe(windows_clamav_pipe_t* pipe_conn, const char* pipe_name, uint32_t timeout);
int catzilla_clamav_scan_via_pipe(windows_clamav_pipe_t* pipe_conn, const char* file_path, clamav_scan_result_t* result);
void catzilla_clamav_disconnect_pipe(windows_clamav_pipe_t* pipe_conn);
#endif

// Error codes
typedef enum {
    CLAMAV_ERROR_SUCCESS = 0,
    CLAMAV_ERROR_NOT_FOUND = -2001,
    CLAMAV_ERROR_DAEMON_NOT_RUNNING = -2002,
    CLAMAV_ERROR_CONNECTION_FAILED = -2003,
    CLAMAV_ERROR_SCAN_FAILED = -2004,
    CLAMAV_ERROR_FILE_NOT_FOUND = -2005,
    CLAMAV_ERROR_INVALID_RESPONSE = -2006,
    CLAMAV_ERROR_TIMEOUT = -2007,
    CLAMAV_ERROR_MEMORY = -2008,
    CLAMAV_ERROR_PERMISSION_DENIED = -2009
} clamav_error_t;

// Error handling
const char* catzilla_clamav_error_string(clamav_error_t error);

// Performance monitoring
typedef struct {
    uint64_t total_scans;
    uint64_t total_scan_time_ms;
    uint64_t files_scanned;
    uint64_t threats_detected;
    uint64_t scan_errors;
    double avg_scan_time_ms;
    double avg_scan_speed_mbps;
} clamav_performance_stats_t;

void catzilla_clamav_get_stats(clamav_performance_stats_t* stats);
void catzilla_clamav_reset_stats(void);

#ifdef __cplusplus
}
#endif

#endif // CATZILLA_UPLOAD_CLAMAV_H
