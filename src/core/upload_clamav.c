#include "upload_clamav.h"
#include "logging.h"
#include "platform_compat.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <time.h>

// Platform-specific includes and compatibility
#ifdef _WIN32
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <io.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <shlwapi.h>
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "shlwapi.lib")

// Windows compatibility definitions
#define close closesocket
#define access _access
// Note: Do NOT redefine popen/pclose - use _popen/_pclose directly on Windows
typedef SSIZE_T ssize_t;
typedef struct _stat stat_t;
#define stat_func _stat
#else
#include <unistd.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <fcntl.h>

// Unix compatibility definitions
typedef struct stat stat_t;
#define stat_func stat
#endif

// Global ClamAV system info cache
static clamav_system_info_t g_clamav_info = {0};
static bool g_clamav_detected = false;
static clamav_performance_stats_t g_clamav_stats = {0};

// Static function declarations
static char* catzilla_get_clamav_version(const char* binary_path);
static bool catzilla_test_clamd_connection_internal(const char* socket_path);
static int catzilla_clamav_parse_scan_response(const char* response, clamav_scan_result_t* result);
static void catzilla_update_scan_stats(clamav_scan_result_t* result);

// Detect ClamAV system availability
int catzilla_clamav_detect_system(clamav_system_info_t* info) {
    if (!info) {
        LOG_CLAMAV_ERROR("Invalid parameter for ClamAV system detection");
        return -1;
    }

    memset(info, 0, sizeof(clamav_system_info_t));
    LOG_CLAMAV_INFO("Detecting ClamAV installation...");

    // Platform-specific detection
#ifdef __linux__
    if (catzilla_clamav_detect_linux(info) == 0) {
        info->available = true;
        g_clamav_info = *info;
        g_clamav_detected = true;
        return 0;
    }
#elif defined(__APPLE__)
    if (catzilla_clamav_detect_macos(info) == 0) {
        info->available = true;
        g_clamav_info = *info;
        g_clamav_detected = true;
        return 0;
    }
#elif defined(_WIN32)
    if (catzilla_clamav_detect_windows(info) == 0) {
        info->available = true;
        g_clamav_info = *info;
        g_clamav_detected = true;
        return 0;
    }
#endif

    LOG_CLAMAV_WARN("ClamAV not found on system");
    return -1;
}

#ifdef __linux__
// Linux-specific ClamAV detection
int catzilla_clamav_detect_linux(clamav_system_info_t* info) {
    LOG_CLAMAV_DEBUG("Detecting ClamAV on Linux...");

    // Check for clamd daemon socket (preferred method)
    const char* socket_paths[] = {
        "/var/run/clamav/clamd.ctl",     // Ubuntu/Debian
        "/var/run/clamd.scan/clamd.sock", // CentOS/RHEL
        "/tmp/clamd.socket",             // Generic
        "/run/clamav/clamd.ctl",         // Modern systemd
        NULL
    };

    for (int i = 0; socket_paths[i]; i++) {
        struct stat st;
        if (stat(socket_paths[i], &st) == 0 && S_ISSOCK(st.st_mode)) {
            info->daemon_socket = strdup(socket_paths[i]);
            info->status = CLAMAV_STATUS_FOUND_DAEMON;
            LOG_CLAMAV_INFO("Found ClamAV daemon socket: %s", socket_paths[i]);
            break;
        }
    }

    // Check for ClamAV binaries
    const char* binary_paths[] = {
        "/usr/bin/clamdscan",        // Daemon client (preferred)
        "/usr/bin/clamscan",         // Direct scanner
        "/usr/local/bin/clamdscan",  // Local install
        "/usr/local/bin/clamscan",   // Local install
        NULL
    };

    for (int i = 0; binary_paths[i]; i++) {
        if (access(binary_paths[i], X_OK) == 0) {
            info->binary_path = strdup(binary_paths[i]);
            if (info->status == CLAMAV_STATUS_NOT_FOUND) {
                info->status = CLAMAV_STATUS_FOUND_BINARY;
            }
            LOG_CLAMAV_INFO("Found ClamAV binary: %s", binary_paths[i]);
            break;
        }
    }

    // Test if daemon is actually running
    if (info->daemon_socket) {
        info->daemon_running = catzilla_test_clamd_connection_internal(info->daemon_socket);
        if (info->daemon_running) {
            info->status = CLAMAV_STATUS_DAEMON_RUNNING;
            LOG_CLAMAV_INFO("ClamAV daemon is running and accessible");
        }
    }

    // Get version information
    if (info->binary_path) {
        info->version = catzilla_get_clamav_version(info->binary_path);
        LOG_CLAMAV_INFO("ClamAV version: %s", info->version ? info->version : "unknown");
    }

    return (info->status != CLAMAV_STATUS_NOT_FOUND) ? 0 : -1;
}
#endif

#ifdef __APPLE__
// macOS-specific ClamAV detection
int catzilla_clamav_detect_macos(clamav_system_info_t* info) {
    LOG_CLAMAV_DEBUG("Detecting ClamAV on macOS...");

    // Check for Homebrew installation
    const char* homebrew_paths[] = {
        "/opt/homebrew/bin/clamdscan",   // Apple Silicon Homebrew
        "/opt/homebrew/bin/clamscan",
        "/usr/local/bin/clamdscan",      // Intel Homebrew
        "/usr/local/bin/clamscan",
        NULL
    };

    for (int i = 0; homebrew_paths[i]; i++) {
        if (access(homebrew_paths[i], X_OK) == 0) {
            info->binary_path = strdup(homebrew_paths[i]);
            info->status = CLAMAV_STATUS_FOUND_BINARY;
            LOG_CLAMAV_INFO("Found ClamAV binary (Homebrew): %s", homebrew_paths[i]);
            break;
        }
    }

    // Check for daemon sockets (Homebrew)
    const char* macos_socket_paths[] = {
        "/opt/homebrew/var/run/clamav/clamd.socket",
        "/usr/local/var/run/clamav/clamd.socket",
        "/tmp/clamd.socket",
        NULL
    };

    for (int i = 0; macos_socket_paths[i]; i++) {
        struct stat st;
        if (stat(macos_socket_paths[i], &st) == 0 && S_ISSOCK(st.st_mode)) {
            info->daemon_socket = strdup(macos_socket_paths[i]);
            if (info->status == CLAMAV_STATUS_NOT_FOUND) {
                info->status = CLAMAV_STATUS_FOUND_DAEMON;
            }
            LOG_CLAMAV_INFO("Found ClamAV daemon socket: %s", macos_socket_paths[i]);
            break;
        }
    }

    // Test daemon connectivity
    if (info->daemon_socket) {
        info->daemon_running = catzilla_test_clamd_connection_internal(info->daemon_socket);
        if (info->daemon_running) {
            info->status = CLAMAV_STATUS_DAEMON_RUNNING;
            LOG_CLAMAV_INFO("ClamAV daemon is running and accessible");
        }
    }

    // Get version
    if (info->binary_path) {
        info->version = catzilla_get_clamav_version(info->binary_path);
        LOG_CLAMAV_INFO("ClamAV version: %s", info->version ? info->version : "unknown");
    }

    return (info->status != CLAMAV_STATUS_NOT_FOUND) ? 0 : -1;
}
#endif

#ifdef _WIN32
// Windows-specific ClamAV detection
int catzilla_clamav_detect_windows(clamav_system_info_t* info) {
    LOG_CLAMAV_DEBUG("Detecting ClamAV on Windows...");

    windows_clamav_registry_info_t registry_info;

    // Try registry detection first
    if (catzilla_detect_clamav_from_registry(&registry_info) == 0) {
        // Found in registry
        info->binary_path = strdup(registry_info.install_path);
        info->version = strdup(registry_info.version);
        info->status = CLAMAV_STATUS_FOUND_BINARY;

        if (registry_info.is_service_installed) {
            info->status = CLAMAV_STATUS_FOUND_DAEMON;
            info->daemon_running = registry_info.is_daemon_running;
        }

        LOG_CLAMAV_INFO("Found ClamAV via registry: %s", registry_info.install_path);
        return 0;
    }

    // Try PowerShell detection as fallback
    if (catzilla_detect_clamav_powershell(&registry_info) == 0) {
        info->binary_path = strdup(registry_info.install_path);
        info->status = CLAMAV_STATUS_FOUND_BINARY;
        LOG_CLAMAV_INFO("Found ClamAV via PowerShell: %s", registry_info.install_path);
        return 0;
    }

    // Check common installation paths
    const char* windows_paths[] = {
        "C:\\Program Files\\ClamAV\\clamscan.exe",
        "C:\\Program Files (x86)\\ClamAV\\clamscan.exe",
        "C:\\ClamAV\\clamscan.exe",
        NULL
    };

    for (int i = 0; windows_paths[i]; i++) {
        if (GetFileAttributesA(windows_paths[i]) != INVALID_FILE_ATTRIBUTES) {
            info->binary_path = strdup(windows_paths[i]);
            info->status = CLAMAV_STATUS_FOUND_BINARY;
            LOG_CLAMAV_INFO("Found ClamAV binary: %s", windows_paths[i]);
            break;
        }
    }

    return (info->status != CLAMAV_STATUS_NOT_FOUND) ? 0 : -1;
}
#endif

// Scan file with ClamAV
clamav_scan_result_t* catzilla_clamav_scan_file(const char* file_path) {
    if (!file_path) {
        LOG_CLAMAV_ERROR("Invalid file path for virus scanning");
        return NULL;
    }

    // Initialize detection if not done
    if (!g_clamav_detected) {
        if (catzilla_clamav_detect_system(&g_clamav_info) != 0) {
            LOG_CLAMAV_WARN("ClamAV not available for virus scanning");
            return NULL;
        }
    }

    if (!g_clamav_info.available) {
        LOG_CLAMAV_WARN("ClamAV not available on system");
        return NULL;
    }

    clamav_scan_result_t* result = malloc(sizeof(clamav_scan_result_t));
    if (!result) {
        LOG_CLAMAV_ERROR("Failed to allocate memory for scan result");
        return NULL;
    }

    memset(result, 0, sizeof(clamav_scan_result_t));
    result->scanned_file_path = strdup(file_path);

    // Get file size for statistics
    stat_t st;
    if (stat_func(file_path, &st) == 0) {
        result->file_size = st.st_size;
    }

    char command[2048];

    // Build scan command based on available tools
    if (g_clamav_info.daemon_running && g_clamav_info.daemon_socket) {
        // Use daemon client (fastest)
#ifdef _WIN32
        snprintf(command, sizeof(command),
                "clamdscan --no-summary --infected --stdout \"%s\" 2>&1", file_path);
#else
        snprintf(command, sizeof(command),
                "clamdscan --no-summary --infected --stdout '%s' 2>&1", file_path);
#endif
    } else if (g_clamav_info.binary_path) {
        // Use direct scanner
#ifdef _WIN32
        snprintf(command, sizeof(command),
                "\"%s\" --no-summary --infected --stdout \"%s\" 2>&1",
                g_clamav_info.binary_path, file_path);
#else
        snprintf(command, sizeof(command),
                "'%s' --no-summary --infected --stdout '%s' 2>&1",
                g_clamav_info.binary_path, file_path);
#endif
    } else {
        result->is_error = true;
        result->error_message = strdup("No ClamAV scanner available");
        return result;
    }

    LOG_CLAMAV_DEBUG("ClamAV scan command: %s", command);

    // Time the scan
    uint64_t start_time = time(NULL);

    // Execute scan with timeout
#ifdef _WIN32
    FILE* fp = _popen(command, "r");
#else
    FILE* fp = popen(command, "r");
#endif
    if (!fp) {
        result->is_error = true;
        result->error_message = strdup("Failed to execute ClamAV");
        return result;
    }

    // Read scan output
    char output[1024] = {0};
    size_t output_len = fread(output, 1, sizeof(output) - 1, fp);
    output[output_len] = '\0';

#ifdef _WIN32
    int exit_code = _pclose(fp);
#else
    int exit_code = pclose(fp);
#endif

    uint64_t end_time = time(NULL);
    result->scan_time_seconds = (double)(end_time - start_time);
    result->exit_code = exit_code;

    // Parse results based on exit code and output
    if (catzilla_clamav_parse_scan_response(output, result) != 0) {
        LOG_CLAMAV_ERROR("Failed to parse ClamAV scan response");
        result->is_error = true;
        if (!result->error_message) {
            result->error_message = strdup("Failed to parse scan response");
        }
    }

    // Add version info
    if (g_clamav_info.version) {
        result->engine_version = strdup(g_clamav_info.version);
    }

    // Update statistics
    catzilla_update_scan_stats(result);

    LOG_CLAMAV_DEBUG("ClamAV scan completed: %s (%.3fs, infected: %s)",
             file_path, result->scan_time_seconds,
             result->is_infected ? "yes" : "no");

    return result;
}

// Parse ClamAV scan response
static int catzilla_clamav_parse_scan_response(const char* response, clamav_scan_result_t* result) {
    if (!response || !result) {
        return -1;
    }

    if (result->exit_code == 0) {
        // Clean file
        result->is_infected = false;
        result->is_error = false;
        return 0;
    } else if (result->exit_code == 1) {
        // Infected file
        result->is_infected = true;
        result->is_error = false;

        // Extract threat name from output
        char* threat_start = strstr(response, ": ");
        if (threat_start) {
            threat_start += 2;
            char* threat_end = strstr(threat_start, " FOUND");
            if (threat_end) {
                size_t threat_len = threat_end - threat_start;
                result->threat_name = malloc(threat_len + 1);
                if (result->threat_name) {
                    strncpy(result->threat_name, threat_start, threat_len);
                    result->threat_name[threat_len] = '\0';
                }
            }
        }

        if (!result->threat_name) {
            result->threat_name = strdup("Unknown threat");
        }

        return 0;
    } else {
        // Scan error
        result->is_infected = false;
        result->is_error = true;
        result->error_message = strdup(response);
        return -1;
    }
}

// Test daemon connection
static bool catzilla_test_clamd_connection_internal(const char* socket_path) {
#ifdef _WIN32
    // On Windows, ClamAV typically runs as a service with TCP interface
    // For now, return false to disable daemon connection on Windows
    CATZILLA_LOG_DEBUG("ClamAV daemon connection not supported on Windows");
    return false;
#else
    int sock = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sock < 0) {
        return false;
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, socket_path, sizeof(addr.sun_path) - 1);

    bool connected = (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) == 0);

    if (connected) {
        // Send PING command to test
        const char* ping_cmd = "zPING\0";
        if (send(sock, ping_cmd, 6, 0) > 0) {
            char response[32];
            ssize_t received = recv(sock, response, sizeof(response) - 1, 0);
            if (received > 0) {
                response[received] = '\0';
                connected = (strstr(response, "PONG") != NULL);
            }
        }
    }

    close(sock);
    return connected;
#endif
}

// Get ClamAV version
static char* catzilla_get_clamav_version(const char* binary_path) {
    char command[512];
#ifdef _WIN32
    snprintf(command, sizeof(command), "\"%s\" --version 2>nul", binary_path);
#else
    snprintf(command, sizeof(command), "'%s' --version 2>/dev/null", binary_path);
#endif

#ifdef _WIN32
    FILE* fp = _popen(command, "r");
#else
    FILE* fp = popen(command, "r");
#endif
    if (!fp) {
        return NULL;
    }

    char version_line[256];
    if (fgets(version_line, sizeof(version_line), fp)) {
#ifdef _WIN32
        _pclose(fp);
#else
        pclose(fp);
#endif

        // Parse version from output like "ClamAV 0.103.8/..."
        char* version_start = strstr(version_line, "ClamAV ");
        if (version_start) {
            version_start += 7; // Skip "ClamAV "
            char* version_end = strchr(version_start, '/');
            if (!version_end) {
                version_end = strchr(version_start, '\n');
            }
            if (!version_end) {
                version_end = strchr(version_start, ' ');
            }
            if (version_end) {
                *version_end = '\0';
            }

            return strdup(version_start);
        }
    }

#ifdef _WIN32
    _pclose(fp);
#else
    pclose(fp);
#endif
    return NULL;
}

// Update scan statistics
static void catzilla_update_scan_stats(clamav_scan_result_t* result) {
    if (!result) {
        return;
    }

    g_clamav_stats.total_scans++;
    g_clamav_stats.total_scan_time_ms += (uint64_t)(result->scan_time_seconds * 1000);

    if (result->is_error) {
        g_clamav_stats.scan_errors++;
    } else {
        g_clamav_stats.files_scanned++;
        if (result->is_infected) {
            g_clamav_stats.threats_detected++;
        }
    }

    // Update averages
    if (g_clamav_stats.files_scanned > 0) {
        g_clamav_stats.avg_scan_time_ms =
            (double)g_clamav_stats.total_scan_time_ms / g_clamav_stats.files_scanned;

        if (result->file_size > 0 && result->scan_time_seconds > 0) {
            double mb_scanned = result->file_size / (1024.0 * 1024.0);
            double scan_speed = mb_scanned / result->scan_time_seconds;

            // Running average of scan speed
            if (g_clamav_stats.avg_scan_speed_mbps == 0) {
                g_clamav_stats.avg_scan_speed_mbps = scan_speed;
            } else {
                g_clamav_stats.avg_scan_speed_mbps =
                    (g_clamav_stats.avg_scan_speed_mbps + scan_speed) / 2.0;
            }
        }
    }
}

// Cleanup scan result
void catzilla_clamav_cleanup_result(clamav_scan_result_t* result) {
    if (!result) {
        return;
    }

    free(result->threat_name);
    free(result->engine_version);
    free(result->error_message);
    free(result->scanned_file_path);
    free(result);
}

// Cleanup system info
void catzilla_clamav_cleanup_system_info(clamav_system_info_t* info) {
    if (!info) {
        return;
    }

    free(info->daemon_socket);
    free(info->binary_path);
    free(info->version);
    free(info->config_path);
    memset(info, 0, sizeof(clamav_system_info_t));
}

// Public API functions
bool catzilla_clamav_is_available(void) {
    if (!g_clamav_detected) {
        return (catzilla_clamav_detect_system(&g_clamav_info) == 0);
    }
    return g_clamav_info.available;
}

const char* catzilla_clamav_get_version(void) {
    if (!g_clamav_detected) {
        catzilla_clamav_detect_system(&g_clamav_info);
    }
    return g_clamav_info.version;
}

bool catzilla_clamav_daemon_running(void) {
    if (!g_clamav_detected) {
        catzilla_clamav_detect_system(&g_clamav_info);
    }
    return g_clamav_info.daemon_running;
}

// Get installation instructions
const char* catzilla_clamav_get_install_instructions(void) {
    static const char* instructions =
        "ClamAV Installation Instructions:\n\n"
        "Ubuntu/Debian:\n"
        "  sudo apt-get update\n"
        "  sudo apt-get install clamav clamav-daemon\n"
        "  sudo systemctl start clamav-daemon\n\n"
        "CentOS/RHEL/Fedora:\n"
        "  sudo yum install clamav clamav-update\n"
        "  sudo systemctl start clamd@scan\n\n"
        "macOS (Homebrew):\n"
        "  brew install clamav\n"
        "  brew services start clamav\n\n"
        "Windows:\n"
        "  Download from: https://www.clamav.net/downloads\n"
        "  Or use: choco install clamav\n\n"
        "For more information: https://docs.clamav.net/manual/Installing.html";

    return instructions;
}

// Get platform-specific install command
char* catzilla_clamav_get_platform_install_command(void) {
#ifdef __linux__
    // Try to detect Linux distribution
    if (access("/etc/debian_version", F_OK) == 0) {
        return strdup("sudo apt-get install clamav clamav-daemon");
    } else if (access("/etc/redhat-release", F_OK) == 0) {
        return strdup("sudo yum install clamav clamav-update");
    } else {
        return strdup("sudo apt-get install clamav clamav-daemon  # or use your distribution's package manager");
    }
#elif defined(__APPLE__)
    return strdup("brew install clamav");
#elif defined(_WIN32)
    return strdup("choco install clamav  # or download from https://www.clamav.net/downloads");
#else
    return strdup("Please install ClamAV using your system's package manager");
#endif
}

// Test connection (public wrapper)
bool catzilla_test_clamd_connection(const char* socket_path) {
    return catzilla_test_clamd_connection_internal(socket_path);
}

// Performance statistics
void catzilla_clamav_get_stats(clamav_performance_stats_t* stats) {
    if (stats) {
        *stats = g_clamav_stats;
    }
}

void catzilla_clamav_reset_stats(void) {
    memset(&g_clamav_stats, 0, sizeof(clamav_performance_stats_t));
}

// Error handling
const char* catzilla_clamav_error_string(clamav_error_t error) {
    switch (error) {
        case CLAMAV_ERROR_SUCCESS: return "Success";
        case CLAMAV_ERROR_NOT_FOUND: return "ClamAV not found";
        case CLAMAV_ERROR_DAEMON_NOT_RUNNING: return "ClamAV daemon not running";
        case CLAMAV_ERROR_CONNECTION_FAILED: return "Connection to ClamAV failed";
        case CLAMAV_ERROR_SCAN_FAILED: return "Virus scan failed";
        case CLAMAV_ERROR_FILE_NOT_FOUND: return "File not found";
        case CLAMAV_ERROR_INVALID_RESPONSE: return "Invalid response from ClamAV";
        case CLAMAV_ERROR_TIMEOUT: return "Scan timeout";
        case CLAMAV_ERROR_MEMORY: return "Memory allocation error";
        case CLAMAV_ERROR_PERMISSION_DENIED: return "Permission denied";
        default: return "Unknown error";
    }
}
