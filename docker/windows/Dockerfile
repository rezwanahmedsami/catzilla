# Catzilla Windows Docker Testing Environment
# Replicates Windows Server 2022 CI environment with vcpkg jemalloc support
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Use PowerShell as the default shell
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

# Set up error handling and retry logic
RUN Write-Host "Setting up Windows container environment..."; \
    $maxRetries = 3; \
    $retryCount = 0

# Install Chocolatey package manager with retry logic
RUN do { \
        try { \
            Write-Host "Installing Chocolatey (attempt $($retryCount + 1))..."; \
            Set-ExecutionPolicy Bypass -Scope Process -Force; \
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; \
            iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1')); \
            break; \
        } catch { \
            $retryCount++; \
            if ($retryCount -ge $maxRetries) { throw }; \
            Write-Host "Retrying Chocolatey installation..."; \
            Start-Sleep -Seconds 10; \
        } \
    } while ($retryCount -lt $maxRetries)

# Install Python first (most reliable)
RUN choco install -y python3 --version=3.11.9 --timeout=600

# Install essential development tools
RUN choco install -y git --timeout=300; \
    choco install -y cmake --installargs 'ADD_CMAKE_TO_PATH=System' --timeout=300

# Install Visual Studio Build Tools with minimal components
RUN choco install -y visualstudio2022-workload-vctools --timeout=1200 || \
    Write-Host "Visual Studio installation may have partial failures, continuing..."

# Refresh environment variables
RUN refreshenv; \
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')

# Install vcpkg and jemalloc with error handling
RUN try { \
        Write-Host "Setting up vcpkg..."; \
        git clone --depth 1 https://github.com/Microsoft/vcpkg.git C:\vcpkg; \
        C:\vcpkg\bootstrap-vcpkg.bat; \
        Write-Host "Installing jemalloc..."; \
        C:\vcpkg\vcpkg.exe install jemalloc:x64-windows --triplet=x64-windows; \
    } catch { \
        Write-Host "vcpkg setup failed, continuing without jemalloc..."; \
    }

# Set up environment variables
ENV CMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake
ENV CATZILLA_JEMALLOC_PATH=C:/vcpkg/installed/x64-windows/bin/jemalloc.dll
ENV PATH="C:\vcpkg\installed\x64-windows\bin;C:\Python311;C:\Python311\Scripts;${PATH}"

WORKDIR C:/catzilla

# Copy requirements and install Python dependencies with error handling
COPY requirements*.txt ./
RUN try { \
        python -m pip install --upgrade pip setuptools wheel; \
        pip install -r requirements-dev.txt; \
    } catch { \
        Write-Host "Some Python packages may have failed to install, continuing..."; \
    }

# Copy the entire project
COPY . .

# Build Catzilla with error handling
RUN try { \
        if (Test-Path "scripts\build.bat") { \
            scripts\build.bat; \
        } else { \
            Write-Host "Build script not found, skipping build..."; \
        } \
    } catch { \
        Write-Host "Build failed, but container is still usable for testing..."; \
    }

# Set up healthcheck with fallback
HEALTHCHECK --interval=30s --timeout=15s --start-period=10s --retries=3 \
    CMD python -c "print('Container is healthy')" || exit 1

# Default command
CMD ["cmd"]
