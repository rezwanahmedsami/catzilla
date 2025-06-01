# Windows Simulation Environment using Wine
# This provides Windows-like testing without requiring Windows containers
FROM ubuntu:22.04

# Install Wine for Windows simulation
RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    gnupg2 \
    && dpkg --add-architecture i386 \
    && wget -O - https://dl.winehq.org/wine-builds/winehq.key | apt-key add - \
    && add-apt-repository 'deb https://dl.winehq.org/wine-builds/ubuntu/ jammy main' \
    && apt-get update && apt-get install -y \
        winehq-stable \
        winetricks \
        python3 \
        python3-pip \
        build-essential \
        cmake \
        git \
        pkg-config \
        libjemalloc2 \
        libjemalloc-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up Wine
ENV WINEARCH=win64
ENV WINEPREFIX=/root/.wine
RUN wine --version && wineboot --init

# Install Python in Wine
RUN cd /tmp && \
    wget https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe && \
    wine python-3.11.9-amd64.exe /quiet InstallAllUsers=1 PrependPath=1

# Set up environment for Windows-style testing
ENV CATZILLA_PLATFORM=windows-sim
ENV PYTHONPATH=/catzilla/python

WORKDIR /catzilla

# Copy test script
COPY docker/windows-sim/test.sh /usr/local/bin/test.sh
RUN chmod +x /usr/local/bin/test.sh

CMD ["/usr/local/bin/test.sh"]
