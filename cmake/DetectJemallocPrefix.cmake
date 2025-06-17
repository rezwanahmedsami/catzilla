# DetectJemallocPrefix.cmake
# Cross-platform jemalloc prefix detection for Catzilla
# Handles different naming conventions across Linux distributions and package managers

function(detect_jemalloc_prefix JEMALLOC_INCLUDE_DIRS JEMALLOC_LIBRARIES)
    set(JEMALLOC_PREFIX_DETECTED "" PARENT_SCOPE)
    set(JEMALLOC_USES_PREFIX FALSE PARENT_SCOPE)

    if(NOT JEMALLOC_INCLUDE_DIRS OR NOT JEMALLOC_LIBRARIES)
        message(STATUS "jemalloc not found, skipping prefix detection")
        return()
    endif()

    # Create a temporary directory for testing
    set(TEST_DIR "${CMAKE_BINARY_DIR}/jemalloc_prefix_test")
    file(MAKE_DIRECTORY "${TEST_DIR}")

    # Create test source file to check function naming conventions
    set(TEST_SOURCE "${TEST_DIR}/test_jemalloc_prefix.c")
    file(WRITE "${TEST_SOURCE}" "
#include <jemalloc/jemalloc.h>
#include <stdio.h>

int main() {
    // Test if direct function names work (Homebrew/some Linux builds)
    void* ptr1 = mallocx(64, 0);
    if (ptr1) {
        dallocx(ptr1, 0);
        printf(\"DIRECT_FUNCTIONS_WORK\\n\");
        return 0;
    }
    return 1;
}
")

    # Create test source file to check prefixed function names
    set(TEST_SOURCE_PREFIXED "${TEST_DIR}/test_jemalloc_prefix_je.c")
    file(WRITE "${TEST_SOURCE_PREFIXED}" "
#include <jemalloc/jemalloc.h>
#include <stdio.h>

int main() {
    // Test if je_ prefixed function names work (RPM-based Linux)
    void* ptr1 = je_mallocx(64, 0);
    if (ptr1) {
        je_dallocx(ptr1, 0);
        printf(\"JE_PREFIX_FUNCTIONS_WORK\\n\");
        return 0;
    }
    return 1;
}
")

    message(STATUS "🔍 Detecting jemalloc function naming convention...")

    # Find math library if on Unix-like systems
    set(JEMALLOC_TEST_LIBRARIES "${JEMALLOC_LIBRARIES}")
    if(UNIX)
        find_library(MATH_LIBRARY m)
        if(MATH_LIBRARY)
            set(JEMALLOC_TEST_LIBRARIES "${JEMALLOC_LIBRARIES};${MATH_LIBRARY}")
        endif()
    endif()

    # First, try to compile and link with direct function names
    try_compile(DIRECT_FUNCTIONS_COMPILE
        "${TEST_DIR}"
        "${TEST_SOURCE}"
        CMAKE_FLAGS
            "-DINCLUDE_DIRECTORIES=${JEMALLOC_INCLUDE_DIRS}"
            "-DLINK_LIBRARIES=${JEMALLOC_TEST_LIBRARIES}"
        OUTPUT_VARIABLE DIRECT_OUTPUT
    )

    # Try to compile and link with je_ prefixed function names
    try_compile(JE_PREFIX_FUNCTIONS_COMPILE
        "${TEST_DIR}"
        "${TEST_SOURCE_PREFIXED}"
        CMAKE_FLAGS
            "-DINCLUDE_DIRECTORIES=${JEMALLOC_INCLUDE_DIRS}"
            "-DLINK_LIBRARIES=${JEMALLOC_TEST_LIBRARIES}"
        OUTPUT_VARIABLE JE_PREFIX_OUTPUT
    )

    # Determine which naming convention works
    if(DIRECT_FUNCTIONS_COMPILE AND NOT JE_PREFIX_FUNCTIONS_COMPILE)
        message(STATUS "✅ jemalloc uses direct function names (mallocx, dallocx, etc.)")
        message(STATUS "   This is typical for Homebrew on macOS and some Linux builds")
        set(JEMALLOC_USES_PREFIX FALSE PARENT_SCOPE)
        set(JEMALLOC_PREFIX_DETECTED "" PARENT_SCOPE)
    elseif(JE_PREFIX_FUNCTIONS_COMPILE AND NOT DIRECT_FUNCTIONS_COMPILE)
        message(STATUS "✅ jemalloc uses je_ prefixed function names (je_mallocx, je_dallocx, etc.)")
        message(STATUS "   This is typical for RPM-based Linux distributions (RHEL, CentOS, AlmaLinux, Fedora)")
        set(JEMALLOC_USES_PREFIX TRUE PARENT_SCOPE)
        set(JEMALLOC_PREFIX_DETECTED "je_" PARENT_SCOPE)
    elseif(DIRECT_FUNCTIONS_COMPILE AND JE_PREFIX_FUNCTIONS_COMPILE)
        message(STATUS "✅ jemalloc supports both direct and je_ prefixed function names")
        message(STATUS "   Using direct function names for compatibility")
        set(JEMALLOC_USES_PREFIX FALSE PARENT_SCOPE)
        set(JEMALLOC_PREFIX_DETECTED "" PARENT_SCOPE)
    else()
        message(WARNING "⚠️  Could not determine jemalloc function naming convention")
        message(STATUS "Direct functions compile: ${DIRECT_FUNCTIONS_COMPILE}")
        message(STATUS "Direct output: ${DIRECT_OUTPUT}")
        message(STATUS "JE prefix functions compile: ${JE_PREFIX_FUNCTIONS_COMPILE}")
        message(STATUS "JE prefix output: ${JE_PREFIX_OUTPUT}")
        # Default to no prefix for safety
        set(JEMALLOC_USES_PREFIX FALSE PARENT_SCOPE)
        set(JEMALLOC_PREFIX_DETECTED "" PARENT_SCOPE)
    endif()

    # Clean up test files
    file(REMOVE_RECURSE "${TEST_DIR}")
endfunction()

# Additional platform-specific detection for edge cases
function(detect_platform_specific_jemalloc_config)
    # Check for specific Linux distributions that are known to use je_ prefix
    if(EXISTS "/etc/redhat-release" OR EXISTS "/etc/centos-release" OR EXISTS "/etc/almalinux-release")
        message(STATUS "🐧 Detected RHEL-based Linux distribution")
        message(STATUS "   These typically use je_ prefixed jemalloc functions")
        set(SUGGESTED_PREFIX "je_" PARENT_SCOPE)
    elseif(EXISTS "/etc/fedora-release")
        message(STATUS "🐧 Detected Fedora Linux")
        message(STATUS "   This typically uses je_ prefixed jemalloc functions")
        set(SUGGESTED_PREFIX "je_" PARENT_SCOPE)
    elseif(APPLE)
        message(STATUS "🍎 Detected macOS")
        message(STATUS "   Homebrew jemalloc typically uses direct function names")
        set(SUGGESTED_PREFIX "" PARENT_SCOPE)
    elseif(WIN32)
        message(STATUS "🪟 Detected Windows")
        message(STATUS "   jemalloc naming convention may vary based on build method")
        set(SUGGESTED_PREFIX "" PARENT_SCOPE)
    else()
        message(STATUS "🐧 Detected Linux (distribution unknown)")
        message(STATUS "   Will auto-detect jemalloc function naming convention")
        set(SUGGESTED_PREFIX "" PARENT_SCOPE)
    endif()
endfunction()
