# Catzilla Linux Docker Testing Environment
# Replicates Ubuntu 22.04 CI environment with jemalloc support
FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV FORCE_COLOR=1
ENV PYTHONIOENCODING=utf-8

# Install system dependencies matching CI environment
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libjemalloc-dev \
    libjemalloc2 \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    git \
    curl \
    wget \
    ca-certificates \
    pkg-config \
    valgrind \
    gdb \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set up Python environment
RUN python3 -m pip install --upgrade pip setuptools wheel

# Set up jemalloc preloading for tests (matching CI configuration)
ENV LD_PRELOAD=/lib/x86_64-linux-gnu/libjemalloc.so.2:$LD_PRELOAD

WORKDIR /catzilla

# Copy requirements first for better Docker layer caching
COPY requirements*.txt ./
RUN pip install -r requirements-dev.txt

# Copy the entire project
COPY . .

# Make scripts executable
RUN chmod +x scripts/build.sh scripts/run_tests.sh scripts/run_example.sh \
    && chmod +x docker/linux/test.sh

# Build Catzilla with jemalloc support
RUN ./scripts/build.sh

# Set up healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import catzilla; print('OK')" || exit 1

# Default command
CMD ["bash"]
