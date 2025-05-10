cmake_minimum_required(VERSION 3.15)
project(catzilla LANGUAGES C)

include(FetchContent)

# libuv subproject
add_subdirectory(deps/libuv)

# llhttp via FetchContent
FetchContent_Declare(llhttp
  URL "https://github.com/nodejs/llhttp/archive/refs/tags/release/v8.1.0.tar.gz"
)
# Build only static llhttp
set(BUILD_SHARED_LIBS OFF CACHE INTERNAL "")
set(BUILD_STATIC_LIBS ON CACHE INTERNAL "")
FetchContent_MakeAvailable(llhttp)

# Main server executable
add_executable(catzilla-server
  src/core/server.c
)

# Include paths for dependencies
# libuv headers
# llhttp generates its header in its binary dir (llhttp_BINARY_DIR)
target_include_directories(catzilla-server
  PRIVATE
    ${CMAKE_SOURCE_DIR}/deps/libuv/include
    ${llhttp_BINARY_DIR}
)

# Link against static libraries
# uv_a from libuv, llhttp_static from llhttp
target_link_libraries(catzilla-server
  PRIVATE
    uv_a
    llhttp_static
)
