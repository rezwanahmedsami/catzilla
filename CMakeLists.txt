cmake_minimum_required(VERSION 3.15)
project(catzilla LANGUAGES C)

set(CMAKE_OSX_DEPLOYMENT_TARGET "10.15")  # Set minimum macOS version
# Add to CMakeLists.txt
add_compile_options(-g -O0)
set(CMAKE_BUILD_TYPE Debug)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC")

include(FetchContent)
find_package(Python3 REQUIRED COMPONENTS Development)

# libuv subproject
add_subdirectory(deps/libuv)

# llhttp configuration
FetchContent_Declare(llhttp
    URL "https://github.com/nodejs/llhttp/archive/refs/tags/release/v8.1.0.tar.gz"
)
set(BUILD_SHARED_LIBS OFF CACHE INTERNAL "")
set(BUILD_STATIC_LIBS ON CACHE INTERNAL "")
FetchContent_MakeAvailable(llhttp)

# Core library
add_library(catzilla_core STATIC
    src/core/server.c
)

target_include_directories(catzilla_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src/core
    ${llhttp_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/deps/libuv/include
    ${Python3_INCLUDE_DIRS}
)

target_link_libraries(catzilla_core PRIVATE
    uv_a
    llhttp_static
)

# Python extension
add_library(_catzilla SHARED
    src/python/module.c
)

# Add include directories for Python bindings
set(PYTHON_BINDINGS_INCLUDE_DIRS
    ${CMAKE_CURRENT_SOURCE_DIR}/src/python
    ${llhttp_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/deps/libuv/include
    ${Python3_INCLUDE_DIRS}
)

target_include_directories(_catzilla PRIVATE
    ${PYTHON_BINDINGS_INCLUDE_DIRS}
)

target_link_libraries(_catzilla PRIVATE
    catzilla_core
    llhttp_static
    ${Python3_LIBRARIES}
)

# Add the main.c file to the executable target
add_executable(catzilla-server src/core/main.c)

# Link the core library to the executable
target_link_libraries(catzilla-server PRIVATE catzilla_core)

# Link the Python library to the executable
target_link_libraries(catzilla-server PRIVATE ${Python3_LIBRARIES})

# Include Python headers
target_include_directories(catzilla-server PRIVATE ${Python3_INCLUDE_DIRS})

# Set the output directory for the executable
set_target_properties(catzilla-server PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
)

# Install rules
install(TARGETS _catzilla DESTINATION python/catzilla)
install(DIRECTORY python/catzilla DESTINATION .)

# Add this at the end of CMakeLists.txt
set_target_properties(_catzilla PROPERTIES
    SUFFIX ".so"
    PREFIX ""
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
)