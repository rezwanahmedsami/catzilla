cmake_minimum_required(VERSION 3.15)
project(catzilla LANGUAGES C)

# Libuv configuration
add_subdirectory(deps/libuv)
include_directories(deps/libuv/include)

# llhttp configuration 
add_subdirectory(deps/llhttp)
include_directories(deps/llhttp/include)

# Main server executable
add_executable(catzilla-server
    src/server.c
)

target_link_libraries(catzilla-server
    uv_a
    llhttp
)