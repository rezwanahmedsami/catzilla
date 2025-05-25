cmake_minimum_required(VERSION 3.15)
project(catzilla LANGUAGES C)

# CRITICAL: On Windows, force Release build type BEFORE any find_package calls
# This prevents CMake from looking for debug Python libraries (python3XX_d.lib)
if(WIN32)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Force Release build type on Windows to avoid debug Python library issues" FORCE)

    # CRITICAL: Clear any cached Python debug library references
    unset(Python3_LIBRARY CACHE)
    unset(Python3_LIBRARIES CACHE)
    unset(Python3_LIBRARY_DEBUG CACHE)
    unset(Python3_LIBRARY_RELEASE CACHE)

    # Force CMake to not look for debug libraries
    set(CMAKE_FIND_DEBUG_MODE FALSE)

    message(STATUS "FORCED CMAKE_BUILD_TYPE to Release on Windows: ${CMAKE_BUILD_TYPE}")
    message(STATUS "Cleared all cached Python library references")
endif()

# Platform-specific compiler flags
if(MSVC)
    # MSVC compiler flags - use /W1 instead of /W3 to reduce warning noise
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} /W1")
    set(CMAKE_C_FLAGS_DEBUG "/Od /Zi /RTC1")
    set(CMAKE_C_FLAGS_RELEASE "/O2 /DNDEBUG")

    # Ensure warnings don't cause build failures
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} /WX-")

    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
    add_definitions(-DWIN32_LEAN_AND_MEAN)
    add_definitions(-D_WIN32_WINNT=0x0602)  # Windows 8 or later (required for GetSystemTimePreciseAsFileTime)

    # Handle potential Python debug library issues
    add_definitions(-DPy_ENABLE_SHARED)
    # Prevent CMake from automatically trying to link debug Python libraries
    add_definitions(-UPy_DEBUG)
    add_definitions(-UNDEBUG)

    # Suppress common Windows warnings
    add_definitions(-D_WINSOCK_DEPRECATED_NO_WARNINGS)

    # Suppress specific warnings that are common in libuv
    add_compile_options(/wd4701)  # potentially uninitialized local variable used
    add_compile_options(/wd4702)  # unreachable code
else()
    # GCC/Clang compiler flags (Unix-like systems)
    add_compile_options(-g -O0)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC")
    # Set Debug build type only for non-Windows platforms
    set(CMAKE_BUILD_TYPE Debug)
endif()

set(CMAKE_OSX_DEPLOYMENT_TARGET "10.15" CACHE STRING "")

# Python support
if(WIN32)
    # NUCLEAR OPTION: On Windows, completely bypass find_package for Python
    # and manually configure Python to avoid any debug library issues

    message(STATUS "=== STARTING NUCLEAR Windows Python Detection ===")

    # Try to find Python executable first
    find_program(Python3_EXECUTABLE python3 python)
    if(NOT Python3_EXECUTABLE)
        find_program(Python3_EXECUTABLE python)
    endif()

    message(STATUS "Python3_EXECUTABLE found: ${Python3_EXECUTABLE}")

    if(Python3_EXECUTABLE)
        # Get Python version and paths manually
        execute_process(
            COMMAND ${Python3_EXECUTABLE} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            OUTPUT_VARIABLE Python3_VERSION
            OUTPUT_STRIP_TRAILING_WHITESPACE
            ERROR_VARIABLE Python3_VERSION_ERROR
            RESULT_VARIABLE Python3_VERSION_RESULT
        )

        message(STATUS "Python version detection result: ${Python3_VERSION_RESULT}")
        message(STATUS "Python version: ${Python3_VERSION}")
        if(Python3_VERSION_ERROR)
            message(STATUS "Python version error: ${Python3_VERSION_ERROR}")
        endif()

        execute_process(
            COMMAND ${Python3_EXECUTABLE} -c "import sys; print(sys.prefix)"
            OUTPUT_VARIABLE Python3_PREFIX
            OUTPUT_STRIP_TRAILING_WHITESPACE
            ERROR_VARIABLE Python3_PREFIX_ERROR
            RESULT_VARIABLE Python3_PREFIX_RESULT
        )

        message(STATUS "Python prefix detection result: ${Python3_PREFIX_RESULT}")
        message(STATUS "Python prefix: ${Python3_PREFIX}")
        if(Python3_PREFIX_ERROR)
            message(STATUS "Python prefix error: ${Python3_PREFIX_ERROR}")
        endif()

        execute_process(
            COMMAND ${Python3_EXECUTABLE} -c "import sysconfig; print(sysconfig.get_path('include'))"
            OUTPUT_VARIABLE Python3_INCLUDE_DIRS
            OUTPUT_STRIP_TRAILING_WHITESPACE
            ERROR_VARIABLE Python3_INCLUDE_ERROR
            RESULT_VARIABLE Python3_INCLUDE_RESULT
        )

        message(STATUS "Python include detection result: ${Python3_INCLUDE_RESULT}")
        message(STATUS "Python include dirs: ${Python3_INCLUDE_DIRS}")
        if(Python3_INCLUDE_ERROR)
            message(STATUS "Python include error: ${Python3_INCLUDE_ERROR}")
        endif()

        # Manually construct the Python library path (ALWAYS release version)
        string(REPLACE "." "" Python3_VERSION_NODOT "${Python3_VERSION}")
        set(Python3_LIBRARY "${Python3_PREFIX}/libs/python${Python3_VERSION_NODOT}.lib")
        set(Python3_LIBRARIES "${Python3_LIBRARY}")

        message(STATUS "Constructed Python library path: ${Python3_LIBRARY}")

        # Verify the library exists
        if(EXISTS "${Python3_LIBRARY}")
            message(STATUS "=== NUCLEAR Windows Python Override SUCCESS ===")
            message(STATUS "Python3_EXECUTABLE: ${Python3_EXECUTABLE}")
            message(STATUS "Python3_VERSION: ${Python3_VERSION}")
            message(STATUS "Python3_PREFIX: ${Python3_PREFIX}")
            message(STATUS "Python3_INCLUDE_DIRS: ${Python3_INCLUDE_DIRS}")
            message(STATUS "Python3_LIBRARY: ${Python3_LIBRARY}")
            message(STATUS "Python library exists: YES")

            set(Python3_FOUND TRUE)

            # Create our custom Python target
            add_library(PythonForCatzilla INTERFACE IMPORTED)
            set_target_properties(PythonForCatzilla PROPERTIES
                INTERFACE_LINK_LIBRARIES "${Python3_LIBRARY}"
                INTERFACE_INCLUDE_DIRECTORIES "${Python3_INCLUDE_DIRS}"
            )

            message(STATUS "PythonForCatzilla target created successfully")
        else()
            # CRITICAL FALLBACK: If our constructed path doesn't exist, try to find it manually
            message(WARNING "Constructed Python library path not found: ${Python3_LIBRARY}")

            # Try alternative paths
            set(ALTERNATIVE_PATHS
                "${Python3_PREFIX}/libs/python${Python3_VERSION_NODOT}.lib"
                "${Python3_PREFIX}/lib/python${Python3_VERSION_NODOT}.lib"
                "${Python3_PREFIX}/Python${Python3_VERSION_NODOT}.lib"
                "C:/Program Files/Python${Python3_VERSION_NODOT}/libs/python${Python3_VERSION_NODOT}.lib"
                "C:/Users/$ENV{USERNAME}/AppData/Local/Programs/Python/Python${Python3_VERSION_NODOT}/libs/python${Python3_VERSION_NODOT}.lib"
            )

            set(FOUND_PYTHON_LIB "")
            foreach(ALT_PATH ${ALTERNATIVE_PATHS})
                if(EXISTS "${ALT_PATH}")
                    set(FOUND_PYTHON_LIB "${ALT_PATH}")
                    message(STATUS "Found Python library at alternative path: ${ALT_PATH}")
                    break()
                endif()
            endforeach()

            if(FOUND_PYTHON_LIB)
                set(Python3_LIBRARY "${FOUND_PYTHON_LIB}")
                set(Python3_LIBRARIES "${FOUND_PYTHON_LIB}")
                set(Python3_FOUND TRUE)

                # Create our custom Python target with found library
                add_library(PythonForCatzilla INTERFACE IMPORTED)
                set_target_properties(PythonForCatzilla PROPERTIES
                    INTERFACE_LINK_LIBRARIES "${Python3_LIBRARY}"
                    INTERFACE_INCLUDE_DIRECTORIES "${Python3_INCLUDE_DIRS}"
                )

                message(STATUS "=== FALLBACK Windows Python Override SUCCESS ===")
                message(STATUS "Found Python library: ${Python3_LIBRARY}")
            else()
                # LAST RESORT: Use find_package but force release library
                message(WARNING "=== USING LAST RESORT: find_package with forced release ===")
                find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

                # Force override any debug library references
                string(REGEX REPLACE "_d\\.lib" ".lib" Python3_LIBRARY "${Python3_LIBRARY}")
                string(REGEX REPLACE "_d\\.lib" ".lib" Python3_LIBRARIES "${Python3_LIBRARIES}")

                # Force cache override
                set(Python3_LIBRARY "${Python3_LIBRARY}" CACHE STRING "Forced release Python library" FORCE)
                set(Python3_LIBRARIES "${Python3_LIBRARIES}" CACHE STRING "Forced release Python libraries" FORCE)

                # Create custom target
                add_library(PythonForCatzilla INTERFACE IMPORTED)
                set_target_properties(PythonForCatzilla PROPERTIES
                    INTERFACE_LINK_LIBRARIES "${Python3_LIBRARY}"
                    INTERFACE_INCLUDE_DIRECTORIES "${Python3_INCLUDE_DIRS}"
                )

                message(STATUS "Last resort Python library: ${Python3_LIBRARY}")
            endif()
        endif()
    else()
        message(FATAL_ERROR "NUCLEAR PYTHON DETECTION FAILED: Could not find Python executable on Windows")
    endif()
else()
    # Use normal find_package for non-Windows platforms
    find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
endif()

# Debug Python configuration on Windows
if(WIN32)
    message(STATUS "=== Windows Python Configuration (Manual) ===")
    message(STATUS "Python3_FOUND: ${Python3_FOUND}")
    message(STATUS "Python3_INCLUDE_DIRS: ${Python3_INCLUDE_DIRS}")
    message(STATUS "Python3_LIBRARIES: ${Python3_LIBRARIES}")
    message(STATUS "Python3_LIBRARY: ${Python3_LIBRARY}")
    message(STATUS "Python3_VERSION: ${Python3_VERSION}")
    message(STATUS "CMAKE_BUILD_TYPE: ${CMAKE_BUILD_TYPE}")
    message(STATUS "PythonForCatzilla target created: YES")
endif()

# libuv
# Configure libuv to be less noisy on Windows
if(WIN32)
    set(LIBUV_BUILD_SHARED OFF CACHE BOOL "Build shared library")
    set(LIBUV_BUILD_BENCH OFF CACHE BOOL "Build benchmarks")
    set(LIBUV_BUILD_TESTS OFF CACHE BOOL "Build tests")
endif()

add_subdirectory(deps/libuv)

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

# Windows-specific Python library handling for the extension
if(WIN32)
    # Use our custom Python target to ensure correct linking
    target_link_libraries(_catzilla PRIVATE
      catzilla_core
      llhttp_static
      yyjson
      PythonForCatzilla
    )
    # Also add Python compile definitions to prevent debug mode issues
    target_compile_definitions(_catzilla PRIVATE Py_ENABLE_SHARED)
else()
    target_link_libraries(_catzilla PRIVATE
      catzilla_core
      llhttp_static
      yyjson
      ${Python3_LIBRARIES}
    )
endif()

# Windows-specific linking for Python extension
if(WIN32)
    target_link_libraries(_catzilla PRIVATE ws2_32 iphlpapi userenv)
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

# Windows-specific Python library handling for tests
if(WIN32)
    target_link_libraries(test_router PRIVATE
      catzilla_core
      PythonForCatzilla
    )
else()
    target_link_libraries(test_router PRIVATE
      catzilla_core
      ${Python3_LIBRARIES}
    )
endif()

# Windows-specific linking for tests
if(WIN32)
    target_link_libraries(test_router PRIVATE ws2_32 iphlpapi userenv)
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

# Windows-specific Python library handling for advanced router tests
if(WIN32)
    target_link_libraries(test_advanced_router PRIVATE
      catzilla_core
      PythonForCatzilla
    )
else()
    target_link_libraries(test_advanced_router PRIVATE
      catzilla_core
      ${Python3_LIBRARIES}
    )
endif()

# Windows-specific linking
if(WIN32)
    target_link_libraries(test_advanced_router PRIVATE ws2_32 iphlpapi userenv)
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

# Windows-specific Python library handling for server integration tests
if(WIN32)
    target_link_libraries(test_server_integration PRIVATE
      catzilla_core
      PythonForCatzilla
    )
else()
    target_link_libraries(test_server_integration PRIVATE
      catzilla_core
      ${Python3_LIBRARIES}
    )
endif()

# Windows-specific linking
if(WIN32)
    target_link_libraries(test_server_integration PRIVATE ws2_32 iphlpapi userenv)
endif()

# Standalone server executable
add_executable(catzilla-server src/core/main.c)

# Windows-specific Python library handling for standalone server
if(WIN32)
    target_link_libraries(catzilla-server PRIVATE
      catzilla_core
      PythonForCatzilla
    )
else()
    target_link_libraries(catzilla-server PRIVATE
      catzilla_core
      ${Python3_LIBRARIES}
    )
endif()

# Windows-specific linking for standalone server
if(WIN32)
    target_link_libraries(catzilla-server PRIVATE ws2_32 iphlpapi userenv)
endif()

target_include_directories(catzilla-server PRIVATE ${Python3_INCLUDE_DIRS})
set_target_properties(catzilla-server PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
)

# Install rules (unused by pip, but here for completeness)
install(TARGETS _catzilla DESTINATION python/catzilla)
install(DIRECTORY python/catzilla DESTINATION .)
