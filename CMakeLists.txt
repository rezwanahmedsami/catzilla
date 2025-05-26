cmake_minimum_required(VERSION 3.15)
project(catzilla VERSION 0.1.0 LANGUAGES C CXX)

# Windows-specific configuration for professional Python library handling
if(WIN32)
    # Professional Windows Python library detection and configuration
    message(STATUS "Windows: Configuring Python library detection...")

    # Check if Python debug libraries are available
    find_library(PYTHON_DEBUG_LIB
        NAMES python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR}_d
        PATHS ${Python3_LIBRARY_DIRS}
        NO_DEFAULT_PATH)

    # Determine optimal build configuration
    if(NOT CMAKE_BUILD_TYPE)
        if(PYTHON_DEBUG_LIB)
            set(CMAKE_BUILD_TYPE Debug CACHE STRING "Default build type" FORCE)
            message(STATUS "Windows: Python debug libraries found - using Debug build")
        else()
            set(CMAKE_BUILD_TYPE RelWithDebInfo CACHE STRING "Default build type" FORCE)
            message(STATUS "Windows: Python debug libraries not found - using RelWithDebInfo")
        endif()
    else()
        # User specified build type - validate it works
        if(CMAKE_BUILD_TYPE STREQUAL "Debug" AND NOT PYTHON_DEBUG_LIB)
            message(WARNING
                "Debug build requested but Python debug libraries not found.\n"
                "This may cause linking errors (python3XX_d.lib not found).\n"
                "Consider using 'RelWithDebInfo' for debugging with release Python libraries,\n"
                "or install Python with debug libraries.\n"
                "Continuing with Debug build as requested...")
        endif()
    endif()

    message(STATUS "Windows: Using ${CMAKE_BUILD_TYPE} build configuration")

    # Configure Python library linking based on build type
    if(CMAKE_BUILD_TYPE STREQUAL "Debug" AND PYTHON_DEBUG_LIB)
        # Use debug Python library if available
        set(Python3_LIBRARIES ${PYTHON_DEBUG_LIB})
        message(STATUS "Windows: Using Python debug library: ${PYTHON_DEBUG_LIB}")
    else()
        # Use release Python library (safer default)
        if(Python3_LIBRARY_RELEASE)
            set(Python3_LIBRARIES ${Python3_LIBRARY_RELEASE})
            message(STATUS "Windows: Using Python release library: ${Python3_LIBRARY_RELEASE}")
        elseif(Python3_LIBRARY)
            # Ensure we're not using debug library by accident
            string(REGEX REPLACE "_d\\.lib$" ".lib" Python3_LIBRARIES "${Python3_LIBRARY}")
            message(STATUS "Windows: Modified Python library path: ${Python3_LIBRARIES}")
        endif()
    endif()
else()
    # Unix-like systems: use Debug by default
    if(NOT CMAKE_BUILD_TYPE)
        set(CMAKE_BUILD_TYPE Debug CACHE STRING "Default build type" FORCE)
    endif()
endif()

# Platform-specific compiler flags
if(MSVC)
    # MSVC compiler flags
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} /W1")
    set(CMAKE_C_FLAGS_DEBUG "/Od /Zi /RTC1")
    set(CMAKE_C_FLAGS_RELEASE "/O2 /DNDEBUG")
    set(CMAKE_C_FLAGS_RELWITHDEBINFO "/O2 /Zi /DNDEBUG")

    # Ensure warnings don't cause build failures
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} /WX-")

    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
    add_definitions(-DWIN32_LEAN_AND_MEAN)
    add_definitions(-D_WIN32_WINNT=0x0602)  # Windows 8 or later

    # Suppress common Windows warnings
    add_definitions(-D_WINSOCK_DEPRECATED_NO_WARNINGS)

    # Suppress Unity test function parameter warnings
    add_compile_options(/wd4113)  # function parameter list mismatch (Unity test warnings)
else()
    # GCC/Clang compiler flags (Unix-like systems)
    add_compile_options(-g -O0)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC")
endif()

set(CMAKE_OSX_DEPLOYMENT_TARGET "10.15" CACHE STRING "")

# macOS multi-architecture support
if(APPLE)
    # Handle multi-architecture builds for macOS
    # Check if we're building for specific architectures via environment variables
    if(DEFINED ENV{CMAKE_OSX_ARCHITECTURES})
        set(CMAKE_OSX_ARCHITECTURES $ENV{CMAKE_OSX_ARCHITECTURES} CACHE STRING "Build architectures for macOS")
        message(STATUS "macOS: Using architectures from environment: ${CMAKE_OSX_ARCHITECTURES}")
    elseif(DEFINED ENV{ARCHFLAGS})
        # Parse ARCHFLAGS environment variable (common in Python wheel building)
        string(REGEX MATCHALL "-arch ([a-zA-Z0-9_]+)" ARCH_MATCHES $ENV{ARCHFLAGS})
        set(PARSED_ARCHS "")
        foreach(ARCH_MATCH ${ARCH_MATCHES})
            string(REGEX REPLACE "-arch " "" ARCH ${ARCH_MATCH})
            list(APPEND PARSED_ARCHS ${ARCH})
        endforeach()
        if(PARSED_ARCHS)
            set(CMAKE_OSX_ARCHITECTURES ${PARSED_ARCHS} CACHE STRING "Build architectures for macOS")
            message(STATUS "macOS: Using architectures from ARCHFLAGS: ${CMAKE_OSX_ARCHITECTURES}")
        endif()
    else()
        # Default to current system architecture if not specified
        execute_process(
            COMMAND uname -m
            OUTPUT_VARIABLE SYSTEM_ARCH
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        if(SYSTEM_ARCH STREQUAL "arm64")
            set(CMAKE_OSX_ARCHITECTURES "arm64" CACHE STRING "Build architectures for macOS")
        else()
            set(CMAKE_OSX_ARCHITECTURES "x86_64" CACHE STRING "Build architectures for macOS")
        endif()
        message(STATUS "macOS: Auto-detected architecture: ${CMAKE_OSX_ARCHITECTURES}")
    endif()

    # Ensure compiler respects the architecture setting
    if(CMAKE_OSX_ARCHITECTURES)
        foreach(ARCH ${CMAKE_OSX_ARCHITECTURES})
            set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -arch ${ARCH}")
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -arch ${ARCH}")
        endforeach()
        message(STATUS "macOS: Architecture flags added to compiler")
    endif()

    # Additional macOS-specific optimizations
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fno-common")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fno-common")
endif()

# Python support
# Set Python-related variables to help CMake find Python in containerized environments
if(DEFINED ENV{Python3_ROOT_DIR})
    set(Python3_ROOT_DIR $ENV{Python3_ROOT_DIR})
endif()

if(DEFINED ENV{Python3_EXECUTABLE})
    set(Python3_EXECUTABLE $ENV{Python3_EXECUTABLE})
endif()

# Use the current Python executable if available
if(NOT Python3_EXECUTABLE AND DEFINED ENV{PYTHON})
    set(Python3_EXECUTABLE $ENV{PYTHON})
endif()

# For manylinux containers, try to use the active Python
if(NOT Python3_EXECUTABLE)
    find_program(Python3_EXECUTABLE NAMES python3 python)
endif()

# Platform-specific Python finding strategy for better manylinux compatibility
if(UNIX AND NOT APPLE)
    # Linux: Be more flexible for manylinux compatibility
    # First try with just Interpreter (always works)
    find_package(Python3 REQUIRED COMPONENTS Interpreter)

    # Try to find Development.Module (preferred for extensions)
    find_package(Python3 QUIET COMPONENTS Development.Module)
    if(NOT Python3_Development.Module_FOUND)
        # Fallback to basic Development (without .Embed which needs libpython)
        find_package(Python3 QUIET COMPONENTS Development)
    endif()

    # Get Python info manually if CMake detection fails
    if(NOT Python3_INCLUDE_DIRS)
        execute_process(
            COMMAND ${Python3_EXECUTABLE} -c "import sysconfig; print(sysconfig.get_path('include'))"
            OUTPUT_VARIABLE Python3_INCLUDE_DIRS
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        message(STATUS "Python include dirs from sysconfig: ${Python3_INCLUDE_DIRS}")
    endif()
else()
    # Windows and macOS: use the full approach (libraries are usually available)
    find_package(Python3 REQUIRED COMPONENTS Interpreter Development Development.Embed)
endif()

# Debug Python detection for troubleshooting
message(STATUS "Python detection results:")
message(STATUS "  Python3_FOUND: ${Python3_FOUND}")
message(STATUS "  Python3_VERSION: ${Python3_VERSION}")
message(STATUS "  Python3_EXECUTABLE: ${Python3_EXECUTABLE}")
message(STATUS "  Python3_INCLUDE_DIRS: ${Python3_INCLUDE_DIRS}")
message(STATUS "  Python3_LIBRARIES: ${Python3_LIBRARIES}")
message(STATUS "  Python3_LIBRARY_DIRS: ${Python3_LIBRARY_DIRS}")

# Additional fallback for manylinux containers if libraries are not found
if(UNIX AND NOT APPLE AND NOT Python3_LIBRARIES)
    message(STATUS "Python3_LIBRARIES not found, attempting comprehensive fallback detection...")

    # Get Python version info
    execute_process(
        COMMAND ${Python3_EXECUTABLE} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        OUTPUT_VARIABLE PYTHON_VERSION_SHORT
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    # Try to find Python library directory
    execute_process(
        COMMAND ${Python3_EXECUTABLE} -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))"
        OUTPUT_VARIABLE PYTHON_LIB_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    # Also try the lib directory relative to the Python executable
    get_filename_component(PYTHON_PREFIX ${Python3_EXECUTABLE} DIRECTORY)
    get_filename_component(PYTHON_PREFIX ${PYTHON_PREFIX} DIRECTORY)

    # Multiple potential library names and locations
    set(PYTHON_LIB_NAMES
        "python${PYTHON_VERSION_SHORT}"
        "python${PYTHON_VERSION_SHORT}m"
        "python${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}"
        "python${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}m"
    )

    set(PYTHON_LIB_PATHS
        "${PYTHON_LIB_DIR}"
        "${PYTHON_PREFIX}/lib"
        "${PYTHON_PREFIX}/lib64"
        "/usr/lib64"
        "/usr/lib"
        "/lib64"
        "/lib"
    )

    # Try to find the Python library
    foreach(LIB_NAME ${PYTHON_LIB_NAMES})
        foreach(LIB_PATH ${PYTHON_LIB_PATHS})
            # Look for shared library first
            find_library(PYTHON_FALLBACK_LIB_${LIB_NAME}
                NAMES ${LIB_NAME}
                PATHS ${LIB_PATH}
                NO_DEFAULT_PATH
            )

            if(PYTHON_FALLBACK_LIB_${LIB_NAME})
                set(Python3_LIBRARIES ${PYTHON_FALLBACK_LIB_${LIB_NAME}})
                message(STATUS "Fallback: Found Python library: ${Python3_LIBRARIES}")
                break()
            endif()

            # If shared library not found, look for static library
            find_library(PYTHON_FALLBACK_STATIC_${LIB_NAME}
                NAMES "lib${LIB_NAME}.a"
                PATHS ${LIB_PATH}
                NO_DEFAULT_PATH
            )

            if(PYTHON_FALLBACK_STATIC_${LIB_NAME})
                set(Python3_LIBRARIES ${PYTHON_FALLBACK_STATIC_${LIB_NAME}})
                message(STATUS "Fallback: Found Python static library: ${Python3_LIBRARIES}")
                break()
            endif()
        endforeach()

        if(Python3_LIBRARIES)
            break()
        endif()
    endforeach()

    # If still not found, try creating a minimal library setup
    if(NOT Python3_LIBRARIES)
        message(STATUS "Creating minimal Python library configuration...")

        # For manylinux containers, we may need to work without explicit libraries
        # Python extensions don't actually need to link against libpython in most cases
        set(Python3_LIBRARIES "")

        # Try to extract library information from Python itself
        execute_process(
            COMMAND ${Python3_EXECUTABLE} -c "
import sysconfig
import os
libdir = sysconfig.get_config_var('LIBDIR')
libname = sysconfig.get_config_var('LDLIBRARY')
if libdir and libname:
    full_path = os.path.join(libdir, libname)
    if os.path.exists(full_path):
        print(full_path)
    else:
        # Try alternative naming
        version = sysconfig.get_config_var('py_version_short')
        alt_name = f'libpython{version}.so'
        alt_path = os.path.join(libdir, alt_name)
        if os.path.exists(alt_path):
            print(alt_path)
"
            OUTPUT_VARIABLE PYTHON_DETECTED_LIB
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )

        if(PYTHON_DETECTED_LIB AND EXISTS ${PYTHON_DETECTED_LIB})
            set(Python3_LIBRARIES ${PYTHON_DETECTED_LIB})
            message(STATUS "Python-detected library: ${Python3_LIBRARIES}")
        endif()
    endif()
endif()

# Windows-specific Python library override to prevent debug library linking
if(WIN32)
    # Override Python library to ensure we use release version
    if(Python3_LIBRARY_RELEASE)
        set(Python3_LIBRARIES ${Python3_LIBRARY_RELEASE})
        message(STATUS "Windows: Using Python release library: ${Python3_LIBRARY_RELEASE}")
    elseif(Python3_LIBRARY)
        # Ensure we're not using debug library
        string(REGEX REPLACE "_d\\.lib$" ".lib" Python3_LIBRARIES "${Python3_LIBRARY}")
        message(STATUS "Windows: Modified Python library path: ${Python3_LIBRARIES}")
    endif()

    # Additional protection: Set explicit Python library for all configurations
    # This ensures MSBuild doesn't override our Python library choice
    if(Python3_LIBRARY_RELEASE)
        set(PYTHON_LIBRARY_FOR_ALL_CONFIGS ${Python3_LIBRARY_RELEASE})
    else()
        string(REGEX REPLACE "_d\\.lib$" ".lib" PYTHON_LIBRARY_FOR_ALL_CONFIGS "${Python3_LIBRARY}")
    endif()

    message(STATUS "Windows Python configuration:")
    message(STATUS "  Python3_VERSION: ${Python3_VERSION}")
    message(STATUS "  Python3_EXECUTABLE: ${Python3_EXECUTABLE}")
    message(STATUS "  Python3_INCLUDE_DIRS: ${Python3_INCLUDE_DIRS}")
    message(STATUS "  Python3_LIBRARIES: ${Python3_LIBRARIES}")
    message(STATUS "  PYTHON_LIBRARY_FOR_ALL_CONFIGS: ${PYTHON_LIBRARY_FOR_ALL_CONFIGS}")
    message(STATUS "  CMAKE_BUILD_TYPE: ${CMAKE_BUILD_TYPE}")
endif()

# libuv
# Configure libuv to be less noisy on Windows
if(WIN32)
    set(LIBUV_BUILD_SHARED OFF CACHE BOOL "Build shared library")
    set(LIBUV_BUILD_BENCH OFF CACHE BOOL "Build benchmarks")
    set(LIBUV_BUILD_TESTS OFF CACHE BOOL "Build tests")
endif()

add_subdirectory(deps/libuv)

# Windows helper function to set Python library for all configurations
if(WIN32)
    function(set_windows_python_library target_name)
        # Use generator expressions to ensure the release Python library is used for all configurations
        if(PYTHON_LIBRARY_FOR_ALL_CONFIGS)
            target_link_libraries(${target_name} PRIVATE
                "$<$<CONFIG:Debug>:${PYTHON_LIBRARY_FOR_ALL_CONFIGS}>"
                "$<$<CONFIG:Release>:${PYTHON_LIBRARY_FOR_ALL_CONFIGS}>"
                "$<$<CONFIG:RelWithDebInfo>:${PYTHON_LIBRARY_FOR_ALL_CONFIGS}>"
                "$<$<CONFIG:MinSizeRel>:${PYTHON_LIBRARY_FOR_ALL_CONFIGS}>"
            )
            message(STATUS "Windows: Set explicit Python library for target ${target_name}: ${PYTHON_LIBRARY_FOR_ALL_CONFIGS}")
        endif()
    endfunction()
endif()

# llhttp
include(FetchContent)
FetchContent_Declare(llhttp
  URL "https://github.com/nodejs/llhttp/archive/refs/tags/release/v8.1.0.tar.gz"
)
set(BUILD_SHARED_LIBS  OFF CACHE INTERNAL "")
set(BUILD_STATIC_LIBS  ON  CACHE INTERNAL "")
FetchContent_MakeAvailable(llhttp)

# yyjson for fast JSON parsing
FetchContent_Declare(yyjson
  URL "https://github.com/ibireme/yyjson/archive/refs/tags/0.8.0.tar.gz"
)
FetchContent_MakeAvailable(yyjson)

# Core static library
add_library(catzilla_core STATIC src/core/server.c src/core/router.c)
target_include_directories(catzilla_core PUBLIC
  src/core
  ${llhttp_SOURCE_DIR}/include
  deps/libuv/include
  ${Python3_INCLUDE_DIRS}
  ${yyjson_SOURCE_DIR}/src
)
target_link_libraries(catzilla_core PRIVATE uv_a llhttp_static yyjson)

# Windows-specific linking
if(WIN32)
    target_link_libraries(catzilla_core PRIVATE ws2_32 iphlpapi userenv)
endif()

# ——— Python extension module ———
add_library(_catzilla SHARED src/python/module.c)
target_include_directories(_catzilla PRIVATE
  src/python
  ${llhttp_SOURCE_DIR}/include
  deps/libuv/include
  ${Python3_INCLUDE_DIRS}
  ${yyjson_SOURCE_DIR}/src
)

target_link_libraries(_catzilla PRIVATE
  catzilla_core
  llhttp_static
  yyjson
)

# Only link to Python libraries if they exist and are needed (not for manylinux)
if(Python3_LIBRARIES AND NOT (UNIX AND NOT APPLE))
    target_link_libraries(_catzilla PRIVATE ${Python3_LIBRARIES})
endif()

# Windows-specific linking for Python extension
if(WIN32)
    target_link_libraries(_catzilla PRIVATE ws2_32 iphlpapi userenv)
    # Ensure Python extensions use shared Python libraries
    target_compile_definitions(_catzilla PRIVATE Py_ENABLE_SHARED)
    # Set explicit Python library for all configurations
    set_windows_python_library(_catzilla)
endif()

# Force appropriate suffix for Python module based on platform
if(WIN32)
    set_target_properties(_catzilla PROPERTIES
      PREFIX ""            # no "lib" prefix
      OUTPUT_NAME "_catzilla"
      SUFFIX ".pyd"        # Windows Python extension
      LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
    )
else()
    set_target_properties(_catzilla PROPERTIES
      PREFIX ""            # no "lib" prefix
      OUTPUT_NAME "_catzilla"
      SUFFIX ".so"         # Unix Python extension
      LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
    )
endif()

# ——— Tests ———
# Only build tests when not in wheel building mode (skip for manylinux containers)
# Check if we're in a wheel building environment by looking for common indicators
set(WHEEL_BUILD_MODE OFF)
if(DEFINED ENV{AUDITWHEEL_PLAT} OR DEFINED ENV{CIBW_BUILD} OR
   (UNIX AND NOT APPLE AND EXISTS "/opt/_internal"))
    set(WHEEL_BUILD_MODE ON)
    message(STATUS "Detected wheel building environment - skipping test executables")
endif()

if(NOT WHEEL_BUILD_MODE)
    message(STATUS "Building test executables")

    # Test framework
    # Add test_router executable
    add_executable(test_router
      tests/c/test_router.c
      deps/unity/src/unity.c
    )

    target_include_directories(test_router PRIVATE
      src/core
      deps/unity/src
      ${Python3_INCLUDE_DIRS}
    )

    target_link_libraries(test_router PRIVATE
      catzilla_core
    )

    # Link Python libraries for tests (needed for symbols in catzilla_core)
    if(Python3_LIBRARIES)
        target_link_libraries(test_router PRIVATE ${Python3_LIBRARIES})
    endif()

    # Windows-specific linking for tests
    if(WIN32)
        target_link_libraries(test_router PRIVATE ws2_32 iphlpapi userenv)
        set_windows_python_library(test_router)
    endif()

    # Add test_advanced_router executable
    add_executable(test_advanced_router
      tests/c/test_advanced_router.c
      deps/unity/src/unity.c
    )

    target_include_directories(test_advanced_router PRIVATE
      src/core
      deps/unity/src
      ${Python3_INCLUDE_DIRS}
    )

    target_link_libraries(test_advanced_router PRIVATE
      catzilla_core
    )

    # Link Python libraries for tests (needed for symbols in catzilla_core)
    if(Python3_LIBRARIES)
        target_link_libraries(test_advanced_router PRIVATE ${Python3_LIBRARIES})
    endif()

    # Windows-specific linking
    if(WIN32)
        target_link_libraries(test_advanced_router PRIVATE ws2_32 iphlpapi userenv)
        set_windows_python_library(test_advanced_router)
    endif()

    # Add test_server_integration executable
    add_executable(test_server_integration
      tests/c/test_server_integration.c
      deps/unity/src/unity.c
    )

    target_include_directories(test_server_integration PRIVATE
      src/core
      deps/unity/src
      ${Python3_INCLUDE_DIRS}
    )

    target_link_libraries(test_server_integration PRIVATE
      catzilla_core
    )

    # Link Python libraries for tests (needed for symbols in catzilla_core)
    if(Python3_LIBRARIES)
        target_link_libraries(test_server_integration PRIVATE ${Python3_LIBRARIES})
    endif()

    # Windows-specific linking
    if(WIN32)
        target_link_libraries(test_server_integration PRIVATE ws2_32 iphlpapi userenv)
        set_windows_python_library(test_server_integration)
    endif()
endif()

# Install rules (unused by pip, but here for completeness)
install(TARGETS _catzilla DESTINATION python/catzilla)
install(DIRECTORY python/catzilla DESTINATION .)
