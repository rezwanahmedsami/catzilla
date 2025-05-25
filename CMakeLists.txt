cmake_minimum_required(VERSION 3.15)
project(catzilla LANGUAGES C)

# Platform-specific compiler flags
if(MSVC)
    # MSVC compiler flags - use # Python extension module ———
add_library(_catzilla SHARED src/python/module.c)
target_include_directories(_catzilla PRIVATE
  src/python
  ${llhttp_SOURCE_DIR}/include
  deps/libuv/include
  ${Python3_INCLUDE_DIRS}
  ${yyjson_SOURCE_DIR}/src
)

# Windows-specific Python library handling for the extension
if(WIN32 AND MSVC)
    # Link directly to the release library to avoid debug library issues
    target_link_libraries(_catzilla PRIVATE
      catzilla_core
      llhttp_static
      yyjson
      "${Python3_LIBRARIES_RELEASE}"
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
endif()o reduce warning noise
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

    # Suppress common Windows warnings
    add_definitions(-D_WINSOCK_DEPRECATED_NO_WARNINGS)

    # Suppress specific warnings that are common in libuv
    add_compile_options(/wd4701)  # potentially uninitialized local variable used
    add_compile_options(/wd4702)  # unreachable code
else()
    # GCC/Clang compiler flags (Unix-like systems)
    add_compile_options(-g -O0)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC")
endif()

set(CMAKE_BUILD_TYPE Debug)
set(CMAKE_OSX_DEPLOYMENT_TARGET "10.15" CACHE STRING "")

# Python support
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

# Debug Python configuration on Windows
if(WIN32)
    message(STATUS "Python3_FOUND: ${Python3_FOUND}")
    message(STATUS "Python3_INCLUDE_DIRS: ${Python3_INCLUDE_DIRS}")
    message(STATUS "Python3_LIBRARIES: ${Python3_LIBRARIES}")
    message(STATUS "Python3_VERSION: ${Python3_VERSION}")
    message(STATUS "CMAKE_BUILD_TYPE: ${CMAKE_BUILD_TYPE}")
endif()

# Windows-specific Python linking fixes
if(WIN32 AND MSVC)
    # Critical fix for Windows debug builds:
    # Prevent CMake from automatically linking against debug Python libraries (python3XX_d.lib)
    # which are typically not available in standard Python installations

    # First, undefine Py_DEBUG to prevent automatic debug library selection
    add_definitions(-UPy_DEBUG)

    # Force release Python libraries in all build configurations
    set(Python3_USE_STATIC_LIBS FALSE)
    set(CMAKE_MAP_IMPORTED_CONFIG_DEBUG Release)
    set(CMAKE_MAP_IMPORTED_CONFIG_RELWITHDEBINFO Release)

    # Extract the actual Python library path and force its use
    string(REGEX REPLACE "python[0-9]+_d\\.lib" "python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR}.lib"
           Python3_LIBRARIES_RELEASE "${Python3_LIBRARIES}")

    # Also handle the case where the library path doesn't contain version info
    if("${Python3_LIBRARIES_RELEASE}" MATCHES "python_d\\.lib")
        string(REPLACE "python_d.lib" "python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR}.lib"
               Python3_LIBRARIES_RELEASE "${Python3_LIBRARIES_RELEASE}")
    endif()

    # Override Python3_LIBRARIES completely
    set(Python3_LIBRARIES "${Python3_LIBRARIES_RELEASE}")

    message(STATUS "Windows Python Debug Fix Applied")
    message(STATUS "Original Python3_LIBRARIES: ${Python3_LIBRARIES}")
    message(STATUS "Fixed Python3_LIBRARIES: ${Python3_LIBRARIES_RELEASE}")

    # Create a custom Python library target that always uses release libraries
    if(TARGET Python3::Python)
        # Get the release library location
        get_target_property(PYTHON_LIB_RELEASE Python3::Python IMPORTED_IMPLIB_RELEASE)
        if(NOT PYTHON_LIB_RELEASE)
            get_target_property(PYTHON_LIB_RELEASE Python3::Python IMPORTED_LOCATION_RELEASE)
        endif()
        if(NOT PYTHON_LIB_RELEASE)
            # Fallback: construct the release library path
            get_filename_component(PYTHON_LIB_DIR "${Python3_LIBRARIES}" DIRECTORY)
            set(PYTHON_LIB_RELEASE "${PYTHON_LIB_DIR}/python${Python3_VERSION_MAJOR}${Python3_VERSION_MINOR}.lib")
        endif()

        message(STATUS "Using Python release library: ${PYTHON_LIB_RELEASE}")

        # Override all configurations to use release library
        set_target_properties(Python3::Python PROPERTIES
            IMPORTED_IMPLIB_DEBUG "${PYTHON_LIB_RELEASE}"
            IMPORTED_IMPLIB_RELWITHDEBINFO "${PYTHON_LIB_RELEASE}"
            IMPORTED_LOCATION_DEBUG "${PYTHON_LIB_RELEASE}"
            IMPORTED_LOCATION_RELWITHDEBINFO "${PYTHON_LIB_RELEASE}"
        )
    endif()
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
target_link_libraries(_catzilla PRIVATE
  catzilla_core
  llhttp_static
  yyjson
  ${Python3_LIBRARIES}
)

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
if(WIN32 AND MSVC)
    target_link_libraries(test_router PRIVATE
      catzilla_core
      "${Python3_LIBRARIES_RELEASE}"
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
if(WIN32 AND MSVC)
    target_link_libraries(test_advanced_router PRIVATE
      catzilla_core
      "${Python3_LIBRARIES_RELEASE}"
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
if(WIN32 AND MSVC)
    target_link_libraries(test_server_integration PRIVATE
      catzilla_core
      "${Python3_LIBRARIES_RELEASE}"
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
if(WIN32 AND MSVC)
    target_link_libraries(catzilla-server PRIVATE
      catzilla_core
      "${Python3_LIBRARIES_RELEASE}"
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
