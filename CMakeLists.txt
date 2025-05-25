cmake_minimum_required(VERSION 3.15)
project(catzilla LANGUAGES C)

# Platform-specific compiler flags
if(MSVC)
    # MSVC compiler flags
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} /W3")
    set(CMAKE_C_FLAGS_DEBUG "/Od /Zi /RTC1")
    set(CMAKE_C_FLAGS_RELEASE "/O2 /DNDEBUG")
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
    add_definitions(-DWIN32_LEAN_AND_MEAN)
    add_definitions(-D_WIN32_WINNT=0x0602)  # Windows 8 or later (required for GetSystemTimePreciseAsFileTime)

    # Handle potential Python debug library issues
    add_definitions(-DPy_ENABLE_SHARED)

    # Suppress common Windows warnings
    add_definitions(-D_WINSOCK_DEPRECATED_NO_WARNINGS)
else()
    # GCC/Clang compiler flags (Unix-like systems)
    add_compile_options(-g -O0)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC")
endif()

set(CMAKE_BUILD_TYPE Debug)
set(CMAKE_OSX_DEPLOYMENT_TARGET "10.15" CACHE STRING "")

# Python support
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

# Windows-specific Python linking fixes
if(WIN32)
    # On Windows, prefer release libraries over debug libraries
    # This avoids issues with missing python3XX_d.lib debug libraries
    set(Python3_USE_STATIC_LIBS FALSE)

    # For MSVC, we need to handle the debug library issue differently
    if(MSVC)
        # Force the use of release Python libraries even in debug builds
        # This prevents linking against debug Python libraries that may not be installed
        set(CMAKE_MAP_IMPORTED_CONFIG_DEBUG Release)
        set(CMAKE_MAP_IMPORTED_CONFIG_RELWITHDEBINFO Release)

        # Override Python library settings for debug builds
        get_target_property(PYTHON_LIBRARY_RELEASE Python3::Python IMPORTED_LOCATION_RELEASE)
        if(PYTHON_LIBRARY_RELEASE)
            set_target_properties(Python3::Python PROPERTIES
                IMPORTED_LOCATION_DEBUG "${PYTHON_LIBRARY_RELEASE}"
                IMPORTED_IMPLIB_DEBUG "${PYTHON_LIBRARY_RELEASE}"
            )
        endif()
    endif()

    # Ensure we link against the correct Python library paths
    if(CMAKE_BUILD_TYPE STREQUAL "Debug")
        # In debug builds, prefer release Python libs to avoid missing debug lib issues
        set_property(TARGET Python3::Python PROPERTY IMPORTED_CONFIGURATIONS "RELEASE;DEBUG")
    endif()
endif()

# libuv
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

target_link_libraries(test_router PRIVATE
  catzilla_core
  ${Python3_LIBRARIES}
)

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
  ${Python3_LIBRARIES}
)

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
  ${Python3_LIBRARIES}
)

# Standalone server executable
add_executable(catzilla-server src/core/main.c)
target_link_libraries(catzilla-server PRIVATE
  catzilla_core
  ${Python3_LIBRARIES}
)
target_include_directories(catzilla-server PRIVATE ${Python3_INCLUDE_DIRS})
set_target_properties(catzilla-server PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
)

# Install rules (unused by pip, but here for completeness)
install(TARGETS _catzilla DESTINATION python/catzilla)
install(DIRECTORY python/catzilla DESTINATION .)
