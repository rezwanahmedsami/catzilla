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

# Core static library
add_library(catzilla_core STATIC src/core/server.c)
target_include_directories(catzilla_core PUBLIC
  src/core
  ${llhttp_SOURCE_DIR}/include
  deps/libuv/include
  ${Python3_INCLUDE_DIRS}
)
target_link_libraries(catzilla_core PRIVATE uv_a llhttp_static)

# ——— Python extension module ———
add_library(_catzilla SHARED src/python/module.c)
target_include_directories(_catzilla PRIVATE
  src/python
  ${llhttp_SOURCE_DIR}/include
  deps/libuv/include
  ${Python3_INCLUDE_DIRS}
)
target_link_libraries(_catzilla PRIVATE
  catzilla_core
  llhttp_static
  ${Python3_LIBRARIES}
)

# Force a “.so” suffix so Python’s importer will find it
set_target_properties(_catzilla PROPERTIES
  PREFIX ""            # no “lib” prefix
  OUTPUT_NAME "_catzilla"
  SUFFIX ".so"
  LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
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
