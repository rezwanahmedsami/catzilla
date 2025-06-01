# Catzilla Windows Docker Testing Environment
# Replicates Windows Server 2022 CI environment with vcpkg jemalloc support
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Use PowerShell as the default shell
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

# Install Chocolatey package manager
RUN Set-ExecutionPolicy Bypass -Scope Process -Force; \
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; \
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Install development tools matching CI environment
RUN choco install -y cmake --installargs 'ADD_CMAKE_TO_PATH=System'; \
    choco install -y python3 --version=3.11.9; \
    choco install -y git; \
    choco install -y visualstudio2022buildtools --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64

# Refresh environment variables
RUN refreshenv

# Install vcpkg and jemalloc (matching CI configuration)
RUN git clone https://github.com/Microsoft/vcpkg.git C:\vcpkg; \
    C:\vcpkg\bootstrap-vcpkg.bat; \
    C:\vcpkg\vcpkg.exe install jemalloc:x64-windows

# Set up environment variables matching CI
ENV CMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake
ENV CATZILLA_JEMALLOC_PATH=C:/vcpkg/installed/x64-windows/bin/jemalloc.dll
ENV PATH="C:\vcpkg\installed\x64-windows\bin;C:\Python311;C:\Python311\Scripts;${PATH}"

WORKDIR C:/catzilla

# Copy requirements and install Python dependencies
COPY requirements*.txt ./
RUN python -m pip install --upgrade pip setuptools wheel; \
    pip install -r requirements-dev.txt

# Copy the entire project
COPY . .

# Make batch scripts executable (Windows doesn't need chmod)
# Build Catzilla with jemalloc support
RUN scripts\build.bat

# Set up healthcheck
HEALTHCHECK --interval=30s --timeout=15s --start-period=10s --retries=3 \
    CMD python -c "import catzilla; print('OK')" || exit 1

# Default command
CMD ["cmd"]
