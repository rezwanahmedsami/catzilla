cmake_minimum_required(VERSION 3.15)
project(catzilla LANGUAGES C)

# Dependencies
add_subdirectory(deps/libuv)
add_subdirectory(deps/llhttp)

# Core library
add_library(catzilla_core STATIC
    src/core/server.c
    src/http/router.c
    src/python/module.c
)

target_include_directories(catzilla_core PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/deps
)

target_link_libraries(catzilla_core
    uv_a
    llhttp
)

# Python extension
python_add_module(_catzilla src/python/module.c)
target_link_libraries(_catzilla PRIVATE catzilla_core)