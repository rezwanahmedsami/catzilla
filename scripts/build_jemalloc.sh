#!/bin/bash
set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
JEMALLOC_SOURCE_DIR="${PROJECT_ROOT}/deps/jemalloc"
JEMALLOC_LIB_FILE="${JEMALLOC_SOURCE_DIR}/lib/libjemalloc.a"

echo -e "${BLUE}🧠 jemalloc Build Script${NC}"
echo -e "${BLUE}========================${NC}"

# Skip jemalloc build on Windows
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]] || \
   [[ "$(uname -s)" == "MINGW"* ]] || [[ "$(uname -s)" == "MSYS"* ]] || \
   [[ -n "$WINDIR" ]] || [[ -n "$SYSTEMROOT" ]]; then
    echo -e "${YELLOW}⏭️  Skipping jemalloc build on Windows platform${NC}"
    echo -e "${BLUE}💡 Windows builds use standard memory allocator${NC}"
    exit 0
fi

# Check if jemalloc source directory exists
if [ ! -d "${JEMALLOC_SOURCE_DIR}" ]; then
    echo -e "${RED}❌ Error: jemalloc source directory not found: ${JEMALLOC_SOURCE_DIR}${NC}"
    echo -e "${YELLOW}💡 Tip: Initialize git submodules: git submodule update --init --recursive${NC}"
    exit 1
fi

# Check if jemalloc static library already exists
if [ -f "${JEMALLOC_LIB_FILE}" ]; then
    echo -e "${GREEN}✅ jemalloc static library already exists: ${JEMALLOC_LIB_FILE}${NC}"
    echo -e "${YELLOW}📊 Library info:${NC}"
    ls -lh "${JEMALLOC_LIB_FILE}"
    echo -e "${GREEN}🚀 Skipping jemalloc build (already built)${NC}"
    exit 0
fi

echo -e "${YELLOW}🔨 Building jemalloc static library...${NC}"
echo -e "${BLUE}Source: ${JEMALLOC_SOURCE_DIR}${NC}"
echo -e "${BLUE}Target: ${JEMALLOC_LIB_FILE}${NC}"

# Navigate to jemalloc source directory
cd "${JEMALLOC_SOURCE_DIR}"

# Clean any previous build artifacts
echo -e "\n${GREEN}🧹 Cleaning previous build artifacts...${NC}"
if [ -f "Makefile" ]; then
    make distclean || true
fi

# Configure jemalloc with optimal settings for Catzilla
echo -e "\n${GREEN}⚙️  Configuring jemalloc...${NC}"

# Platform-specific CFLAGS for proper symbol visibility
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: Build universal binary for both x86_64 and arm64
    # Set deployment target to match what cibuildwheel expects
    export MACOSX_DEPLOYMENT_TARGET=${MACOSX_DEPLOYMENT_TARGET:-"10.15"}

    echo -e "\n${YELLOW}🏗️  Building universal jemalloc binary for macOS (x86_64 + arm64)...${NC}"

    # Build for x86_64
    echo -e "${BLUE}📦 Building x86_64 binary...${NC}"
    export CFLAGS="-fPIC -O2 -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET} -arch x86_64"
    export CXXFLAGS="-fPIC -O2 -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET} -arch x86_64"
    export LDFLAGS="-arch x86_64"
    CONFIGURE_ARGS="--enable-static --disable-shared --disable-doc --disable-debug --enable-prof --enable-stats --with-pic --disable-initial-exec-tls --disable-cc-silence --host=x86_64-apple-darwin"

    ./autogen.sh ${CONFIGURE_ARGS}
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error: jemalloc x86_64 configuration failed${NC}"
        exit 1
    fi

    NPROC=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo "4")
    make -j${NPROC}
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error: jemalloc x86_64 build failed${NC}"
        exit 1
    fi

    # Save x86_64 library
    mkdir -p build_temp
    cp lib/libjemalloc.a build_temp/libjemalloc_x86_64.a
    cp lib/libjemalloc_pic.a build_temp/libjemalloc_pic_x86_64.a

    # Clean for arm64 build
    make distclean || true

    # Build for arm64
    echo -e "${BLUE}📦 Building arm64 binary...${NC}"
    export CFLAGS="-fPIC -O2 -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET} -arch arm64"
    export CXXFLAGS="-fPIC -O2 -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET} -arch arm64"
    export LDFLAGS="-arch arm64"
    CONFIGURE_ARGS="--enable-static --disable-shared --disable-doc --disable-debug --enable-prof --enable-stats --with-pic --disable-initial-exec-tls --disable-cc-silence --host=arm64-apple-darwin"

    ./autogen.sh ${CONFIGURE_ARGS}
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error: jemalloc arm64 configuration failed${NC}"
        exit 1
    fi

    make -j${NPROC}
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error: jemalloc arm64 build failed${NC}"
        exit 1
    fi

    # Save arm64 library
    cp lib/libjemalloc.a build_temp/libjemalloc_arm64.a
    cp lib/libjemalloc_pic.a build_temp/libjemalloc_pic_arm64.a

    # Create universal binaries
    echo -e "${BLUE}🔗 Creating universal binaries...${NC}"
    mkdir -p lib
    lipo -create build_temp/libjemalloc_x86_64.a build_temp/libjemalloc_arm64.a -output lib/libjemalloc.a
    lipo -create build_temp/libjemalloc_pic_x86_64.a build_temp/libjemalloc_pic_arm64.a -output lib/libjemalloc_pic.a

    # Clean up temporary files
    rm -rf build_temp

else
    # Linux: Use default visibility settings
    export SPECIFIED_CFLAGS="-fvisibility=default -fPIC -O2"
    export SPECIFIED_CXXFLAGS="-fvisibility=default -fPIC -O2"
    export CFLAGS="-fvisibility=default -fPIC -O2"
    export CXXFLAGS="-fvisibility=default -fPIC -O2"
    CONFIGURE_ARGS="--enable-static --disable-shared --disable-doc --disable-debug --enable-prof --enable-stats --with-pic --disable-initial-exec-tls --disable-cc-silence"

    ./autogen.sh ${CONFIGURE_ARGS}
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error: jemalloc configuration failed${NC}"
        exit 1
    fi

    # Build jemalloc
    echo -e "\n${GREEN}🔨 Building jemalloc (this may take a few minutes)...${NC}"
    NPROC=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo "4")
    make -j${NPROC}

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error: jemalloc build failed${NC}"
        exit 1
    fi
fi

# Verify the static library was created
if [ ! -f "${JEMALLOC_LIB_FILE}" ]; then
    echo -e "${RED}❌ Error: jemalloc static library was not created: ${JEMALLOC_LIB_FILE}${NC}"
    echo -e "${YELLOW}🔍 Available files in lib/:${NC}"
    ls -la lib/ || echo "lib/ directory not found"
    exit 1
fi

# Success!
echo -e "\n${GREEN}✅ jemalloc build complete!${NC}"
echo -e "${YELLOW}📊 Library info:${NC}"
ls -lh "${JEMALLOC_LIB_FILE}"
echo -e "${GREEN}🚀 Ready for Catzilla build!${NC}"
