cmake_minimum_required(VERSION 3.15)
project(catzilla LANGUAGES C)

# Windows-specific configuration to avoid debug Python library issues
if(WIN32)
    # Use Release instead of Debug to avoid python3XX_d.lib issues
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Force Release build type on Windows to avoid debug Python library issues" FORCE)
    message(STATUS "Windows: Using ${CMAKE_BUILD_TYPE} build type to avoid Python debug library issues")
else()
    # Set Debug build type only for non-Windows platforms
    set(CMAKE_BUILD_TYPE Debug)
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

# Python support
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

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
  ${Python3_LIBRARIES}
)

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
  ${Python3_LIBRARIES}
)

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
  ${Python3_LIBRARIES}
)

# Windows-specific linking
if(WIN32)
    target_link_libraries(test_server_integration PRIVATE ws2_32 iphlpapi userenv)
    set_windows_python_library(test_server_integration)
endif()

# Standalone server executable
add_executable(catzilla-server src/core/main.c)

target_link_libraries(catzilla-server PRIVATE
  catzilla_core
  ${Python3_LIBRARIES}
)

# Windows-specific linking for standalone server
if(WIN32)
    target_link_libraries(catzilla-server PRIVATE ws2_32 iphlpapi userenv)
    set_windows_python_library(catzilla-server)
endif()

target_include_directories(catzilla-server PRIVATE ${Python3_INCLUDE_DIRS})
set_target_properties(catzilla-server PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
)

# Install rules (unused by pip, but here for completeness)
install(TARGETS _catzilla DESTINATION python/catzilla)
install(DIRECTORY python/catzilla DESTINATION .)
