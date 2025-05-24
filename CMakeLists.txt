cmake_minimum_required(VERSION 3.15)
project(catzilla LANGUAGES C)

# Debug flags + PIC
add_compile_options(-g -O0)
set(CMAKE_BUILD_TYPE Debug)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC")
set(CMAKE_OSX_DEPLOYMENT_TARGET "10.15" CACHE STRING "")

# Python support
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

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

# Force a ".so" suffix so Python's importer will find it
set_target_properties(_catzilla PROPERTIES
  PREFIX ""            # no "lib" prefix
  OUTPUT_NAME "_catzilla"
  SUFFIX ".so"
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
)

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
