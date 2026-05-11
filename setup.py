# setup.py
import os
import sys
import subprocess
import platform
import shutil
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# Helper for platform-specific output
def is_windows():
    return platform.system() == "Windows"

def platform_emoji(emoji, alt_text):
    return alt_text if is_windows() else emoji

class CMakeBuild(build_ext):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure Windows console can handle Unicode output
        if is_windows():
            try:
                import locale
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            except:
                pass  # Fallback to cp1252, platform_emoji will handle it

    @property
    def is_ci_environment(self):
        """Check if we're running in a CI environment"""
        return bool(os.getenv('CI') or os.getenv('CIBUILDWHEEL') or os.getenv('GITHUB_ACTIONS'))

    def run(self):
        subprocess.check_call(['cmake', '--version'])
        super().run()

    def build_extension(self, ext):
        """Build the C extension module using CMake"""
        # Define source directory first (needed for jemalloc path checks)
        source_dir = os.path.dirname(os.path.abspath(__file__))

        # Ensure build directory is clean for CI builds
        build_dir = os.path.abspath(self.build_temp)

        # For CI environments, clean build directory to avoid corruption
        if os.getenv('CI') or os.getenv('CIBUILDWHEEL'):
            if os.path.exists(build_dir):
                shutil.rmtree(build_dir)

        os.makedirs(build_dir, exist_ok=True)

        # Check for jemalloc environment variable
        # Determine if we should use jemalloc (disable for CI builds with issues)
        use_jemalloc = os.getenv('USE_JEMALLOC', 'ON').upper() == 'ON'
        catzilla_use_jemalloc = os.getenv('CATZILLA_USE_JEMALLOC', '').upper() == '1'

        # For CI builds, be more conservative with jemalloc unless explicitly enabled
        if os.getenv('CI') or os.getenv('CIBUILDWHEEL') or os.getenv('GITHUB_ACTIONS'):
            if catzilla_use_jemalloc:
                # Explicitly requested jemalloc in CI
                use_jemalloc = True
                print("CI environment: jemalloc explicitly enabled via CATZILLA_USE_JEMALLOC=1")
            else:
                # Disable jemalloc for CI builds by default to avoid complex prefix detection issues
                use_jemalloc = False
                print("CI environment detected: Disabling jemalloc for reliable builds (use CATZILLA_USE_JEMALLOC=1 to force enable)")

        jemalloc_include_candidates = []
        if sys.platform == 'win32':
            jemalloc_lib_candidates = [
                os.path.join(source_dir, '.catzilla-cache', 'jemalloc-windows', 'lib', 'jemalloc.lib'),
                os.path.join(source_dir, 'deps', 'jemalloc', 'lib', 'jemalloc.lib'),
            ]
            jemalloc_include_candidates = [
                os.path.join(source_dir, '.catzilla-cache', 'jemalloc-windows', 'include', 'jemalloc', 'jemalloc.h'),
                os.path.join(source_dir, 'deps', 'jemalloc', 'include', 'jemalloc', 'jemalloc.h'),
            ]
        else:
            jemalloc_lib_candidates = [
                os.path.join(source_dir, 'deps', 'jemalloc', 'lib', 'libjemalloc.a'),
            ]
            jemalloc_include_candidates = [
                os.path.join(source_dir, 'deps', 'jemalloc', 'include', 'jemalloc', 'jemalloc.h'),
            ]

        jemalloc_lib_path = next((path for path in jemalloc_lib_candidates if os.path.exists(path)), None)
        jemalloc_include_path = next((path for path in jemalloc_include_candidates if os.path.exists(path)), None)

        if use_jemalloc and (jemalloc_lib_path is None or jemalloc_include_path is None):
            if sys.platform == 'win32':
                jemalloc_build_script = os.path.join(source_dir, 'scripts', 'build_jemalloc.bat')
                jemalloc_build_cwd = os.path.join(source_dir, 'deps', 'jemalloc')
                jemalloc_build_cmd = ['cmd', '/c', jemalloc_build_script]
            else:
                jemalloc_build_script = os.path.join(source_dir, 'scripts', 'build_jemalloc.sh')
                jemalloc_build_cwd = source_dir
                jemalloc_build_cmd = ['bash', jemalloc_build_script]

            if os.path.exists(jemalloc_build_script):
                try:
                    print("Ensuring jemalloc artifacts are available for the current build platform...")
                    subprocess.check_call(jemalloc_build_cmd, cwd=jemalloc_build_cwd)
                except subprocess.CalledProcessError as e:
                    print(f"Warning: jemalloc build script failed ({e}); disabling jemalloc for this build")
                    use_jemalloc = False

                jemalloc_lib_path = next((path for path in jemalloc_lib_candidates if os.path.exists(path)), None)
                jemalloc_include_path = next((path for path in jemalloc_include_candidates if os.path.exists(path)), None)

        # Additional check: disable jemalloc only when no staged/prebuilt library exists.
        if use_jemalloc and (jemalloc_lib_path is None or jemalloc_include_path is None):
            use_jemalloc = False
            print(
                "jemalloc staged artifacts not found in any known location, disabling jemalloc"
            )

        # Python version compatibility checks
        python_version = sys.version_info
        print(f"Building for Python {python_version.major}.{python_version.minor}.{python_version.micro} on {platform.system()}")

        # Disable jemalloc for problematic Python versions in CI
        if python_version.minor == 11 and os.getenv('CI') and not catzilla_use_jemalloc:
            print("Warning: Disabling jemalloc for Python 3.11 in CI environment for compatibility")
            use_jemalloc = False
        elif python_version.minor == 11 and os.getenv('CI') and catzilla_use_jemalloc:
            print("CI Python 3.11 build: preserving explicit CATZILLA_USE_JEMALLOC=1 override")

                # Ensure build directory exists and is clean
        if os.path.exists(build_dir):
            print(f"Cleaning existing build directory: {build_dir}")
            try:
                shutil.rmtree(build_dir)
            except Exception as e:
                print(f"Warning: Could not clean build directory: {e}")

        print(f"Creating build directory: {build_dir}")
        os.makedirs(build_dir, exist_ok=True)

        # Ensure source directory exists
        if not os.path.exists(source_dir):
            raise RuntimeError(f"Source directory not found: {source_dir}")

        # 1) Configure with environment preservation and improved error handling
        configure_cmd = [
            'cmake', '-S', '.', '-B', build_dir,
            f'-DPython3_EXECUTABLE={sys.executable}',
            f'-DCATZILLA_USE_JEMALLOC={"ON" if use_jemalloc else "OFF"}'
        ]

        # Add macOS deployment target only on macOS
        if sys.platform == 'darwin':
            configure_cmd.append(f'-DCMAKE_OSX_DEPLOYMENT_TARGET={os.getenv("MACOSX_DEPLOYMENT_TARGET","10.15")}')

        # Add platform-specific compiler fixes for isolated environments
        if sys.platform == 'darwin':
            # macOS: Explicitly set compilers to avoid isolated env issues
            configure_cmd.extend([
                '-DCMAKE_C_COMPILER=/usr/bin/clang',
                '-DCMAKE_CXX_COMPILER=/usr/bin/clang++',
            ])

            # Handle architecture based on environment (cibuildwheel vs local build)
            if self.is_ci_environment:
                # CI: Use single architecture to avoid complex universal2 build issues
                arch = platform.machine()  # Use runner's native arch (arm64 or x86_64)
                configure_cmd.append(f'-DCMAKE_OSX_ARCHITECTURES={arch}')
                print(f"CI macOS build: Using single architecture {arch}")
            elif os.getenv('CIBW_ARCHS_MACOS') or os.getenv('CMAKE_OSX_ARCHITECTURES'):
                # Local cibuildwheel: Use environment-specified architecture
                arch = os.getenv('CMAKE_OSX_ARCHITECTURES', os.getenv('CIBW_ARCHS_MACOS', platform.machine()))
                if arch == 'universal2':
                    # For universal2, let CMake handle it automatically
                    configure_cmd.append('-DCMAKE_OSX_ARCHITECTURES=arm64;x86_64')
                    print("Local build: Using universal2 architecture")
                else:
                    configure_cmd.append(f'-DCMAKE_OSX_ARCHITECTURES={arch}')
                    print(f"Local build: Using specified architecture {arch}")
            else:
                # Local development: Use current machine architecture
                arch = platform.machine()
                configure_cmd.append(f'-DCMAKE_OSX_ARCHITECTURES={arch}')
                print(f"Local development: Using machine architecture {arch}")
        elif sys.platform.startswith('linux'):
            # Linux: Prefer the active toolchain from the environment or PATH.
            # manylinux images expose GCC via devtoolset paths, not /usr/bin/gcc.
            linux_cc = os.getenv('CC') or shutil.which('gcc') or shutil.which('cc')
            linux_cxx = os.getenv('CXX') or shutil.which('g++') or shutil.which('c++')

            if linux_cc:
                configure_cmd.append(f'-DCMAKE_C_COMPILER={linux_cc}')
            if linux_cxx:
                configure_cmd.append(f'-DCMAKE_CXX_COMPILER={linux_cxx}')
        elif sys.platform == 'win32':
            # Windows: Let CMake detect compilers, but set platform
            configure_cmd.extend([
                '-DCMAKE_GENERATOR_PLATFORM=x64' if platform.machine().endswith('64') else '-DCMAKE_GENERATOR_PLATFORM=Win32'
            ])

        # Set generator for better compatibility with automatic detection
        if sys.platform == 'win32':
            # Windows: Try to detect the best available generator
            try:
                # Check for VS 2022 first (newest)
                result = subprocess.run(['cmake', '-G', 'Visual Studio 17 2022', '--help'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    configure_cmd.extend(['-G', 'Visual Studio 17 2022'])
                else:
                    # Fallback to VS 2019
                    result = subprocess.run(['cmake', '-G', 'Visual Studio 16 2019', '--help'],
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        configure_cmd.extend(['-G', 'Visual Studio 16 2019'])
                    else:
                        # Fallback to Ninja or MinGW
                        result = subprocess.run(['cmake', '-G', 'Ninja', '--help'],
                                              capture_output=True, text=True)
                        if result.returncode == 0:
                            configure_cmd.extend(['-G', 'Ninja'])
                        else:
                            # Final fallback - let CMake choose
                            print("Warning: Using default CMake generator on Windows")
            except Exception as e:
                print(f"Warning: Could not detect Windows generator: {e}")
                # Don't add any generator, let CMake choose
        else:
            configure_cmd.extend(['-G', 'Unix Makefiles'])

        if use_jemalloc:
            print(f"{platform_emoji('🚀', '>>')} Building Catzilla with jemalloc support...")
        else:
            print(f"{platform_emoji('⚠️', '!!')} Building Catzilla without jemalloc (fallback to standard malloc)")

        # Preserve environment for CMake
        env = os.environ.copy()

        # Set environment variables for isolated build environments
        if sys.platform == 'darwin':
            # macOS: Set SDK path and deployment target
            env['MACOSX_DEPLOYMENT_TARGET'] = os.getenv("MACOSX_DEPLOYMENT_TARGET", "10.15")
            # Ensure we can find system tools
            env['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin:' + env.get('PATH', '')
            # Fix for shell directory access issues in CI
            env['PWD'] = os.getcwd()
        elif sys.platform.startswith('linux'):
            # Linux: Ensure compiler tools are available
            env['CC'] = env.get('CC', shutil.which('gcc') or shutil.which('cc') or 'gcc')
            env['CXX'] = env.get('CXX', shutil.which('g++') or shutil.which('c++') or 'g++')
            env['PWD'] = os.getcwd()
        elif sys.platform == 'win32':
            # Windows: Set up build environment
            # Ensure we can find build tools
            if 'VS160COMNTOOLS' in env or 'VS170COMNTOOLS' in env:
                print("Visual Studio environment detected")
            # Set minimal Windows environment for CMake
            env['CMAKE_GENERATOR_INSTANCE'] = env.get('CMAKE_GENERATOR_INSTANCE', '')

        # Ensure we're in the right working directory
        original_cwd = os.getcwd()
        configure_succeeded = False
        try:
            # Change to source directory for CMake (source_dir already defined above)
            os.chdir(source_dir)

            print(f"Running CMake configure: {' '.join(configure_cmd)}")
            subprocess.check_call(configure_cmd, env=env, cwd=source_dir)
            print(f"{platform_emoji('✅', '[SUCCESS]')} CMake configuration successful")
            configure_succeeded = True
        except subprocess.CalledProcessError as e:
            print(f"{platform_emoji('❌', '[ERROR]')} CMake configuration failed with return code {e.returncode}")

            # For CI environments, try comprehensive fallback
            if os.getenv('CI') or os.getenv('CIBUILDWHEEL') or os.getenv('GITHUB_ACTIONS'):
                print(f"{platform_emoji('🔄', '[RETRY]')} Attempting CI-optimized fallback configuration...")

                # Simplified fallback configuration for CI
                fallback_cmd = [
                    'cmake', '-S', '.', '-B', build_dir,
                    f'-DPython3_EXECUTABLE={sys.executable}',
                    '-DCATZILLA_USE_JEMALLOC=OFF',
                    '-DCATZILLA_BUILD_TESTS=OFF',  # Skip tests in wheel builds
                    '-DCMAKE_BUILD_TYPE=Release'
                ]

                # Add platform-specific fallbacks
                if sys.platform == 'darwin':
                    # macOS CI fallback - minimal configuration
                    fallback_cmd.extend([
                        '-DCMAKE_OSX_DEPLOYMENT_TARGET=10.15',
                        '-DCMAKE_C_COMPILER=/usr/bin/clang',
                        '-DCMAKE_CXX_COMPILER=/usr/bin/clang++'
                    ])
                elif sys.platform.startswith('linux'):
                    # Linux CI fallback
                    fallback_cc = env.get('CC') or shutil.which('gcc') or shutil.which('cc') or 'gcc'
                    fallback_cxx = env.get('CXX') or shutil.which('g++') or shutil.which('c++') or 'g++'
                    fallback_cmd.extend([
                        f'-DCMAKE_C_COMPILER={fallback_cc}',
                        f'-DCMAKE_CXX_COMPILER={fallback_cxx}'
                    ])

                try:
                    print(f"Running fallback CMake: {' '.join(fallback_cmd)}")
                    subprocess.check_call(fallback_cmd, env=env, cwd=source_dir)
                    print(f"{platform_emoji('✅', '[SUCCESS]')} Fallback CMake configuration successful")
                    configure_succeeded = True
                    use_jemalloc = False
                except subprocess.CalledProcessError as fallback_e:
                    print(f"{platform_emoji('❌', '[ERROR]')} Fallback also failed: {fallback_e}")
                    # Continue with existing fallback logic below
                    print("Attempting minimal configuration...")
            else:
                print("Attempting fallback configuration...")

            if not configure_succeeded:
                # Fallback: minimal configuration without extra flags
                fallback_cmd = [
                    'cmake', '-S', '.', '-B', build_dir,
                    f'-DPython3_EXECUTABLE={sys.executable}',
                    f'-DCATZILLA_USE_JEMALLOC={"ON" if use_jemalloc else "OFF"}'
                ]

                # For Windows, try different generators in fallback
                if sys.platform == 'win32':
                    # Try minimal Windows generators
                    for generator in ['Ninja', 'MinGW Makefiles', 'NMake Makefiles']:
                        try:
                            test_cmd = fallback_cmd + ['-G', generator]
                            subprocess.check_call(test_cmd, env=env, cwd=source_dir)
                            print(f"Success with {generator} generator")
                            break
                        except subprocess.CalledProcessError:
                            print(f"Failed with {generator} generator, trying next...")
                            continue
                    else:
                        # Final fallback - no generator specified
                        print("Trying default generator...")
                        subprocess.check_call(fallback_cmd, env=env, cwd=source_dir)
                else:
                    subprocess.check_call(fallback_cmd, env=env, cwd=source_dir)
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

        # 2) Build with environment preservation and conservative parallelism
        build_cmd = ['cmake', '--build', build_dir]
        # On Windows, explicitly use Release configuration to avoid python3XX_d.lib issues
        if sys.platform == 'win32':
            build_cmd.extend(['--config', 'Release'])

        # Add parallel build support for faster compilation, but conservative for CI
        if sys.platform != 'win32':
            import multiprocessing
            if self.is_ci_environment:
                # CI: Use fewer parallel jobs to avoid resource conflicts
                parallel_jobs = min(2, multiprocessing.cpu_count())
                print(f"CI build: Using {parallel_jobs} parallel jobs")
            else:
                # Local: Use more aggressive parallelism
                parallel_jobs = min(multiprocessing.cpu_count(), 8)
                print(f"Local build: Using {parallel_jobs} parallel jobs")

            build_cmd.extend(['--parallel', str(parallel_jobs)])

        # Ensure we build from the right directory (source_dir already defined above)
        print(f"Running CMake build: {' '.join(build_cmd)}")
        subprocess.check_call(build_cmd, env=env, cwd=source_dir)

        # 3) Locate the built extension file
        if sys.platform == 'win32':
            # On Windows with Release config, files are in Release subdirectory
            ext_name = '_catzilla.pyd'
            so_path = os.path.join(build_dir, 'Release', ext_name)
            if not os.path.isfile(so_path):
                # Fallback: try build_dir root
                so_path = os.path.join(build_dir, ext_name)
        else:
            # Unix-like systems use .so extension
            ext_name = '_catzilla.so'
            so_path = os.path.join(build_dir, ext_name)

        if not os.path.isfile(so_path):
            # debugging dump
            print("=== build_dir contents ===", os.listdir(build_dir))
            if sys.platform == 'win32' and os.path.isdir(os.path.join(build_dir, 'Release')):
                print("=== Release subdirectory contents ===", os.listdir(os.path.join(build_dir, 'Release')))
            raise RuntimeError(f"Expected {ext_name} in {so_path}, but not found")

        # 4) Copy it into your package with proper cleanup handling
        dest_path = self.get_ext_fullpath('catzilla._catzilla')
        dest_dir = os.path.dirname(dest_path)
        os.makedirs(dest_dir, exist_ok=True)

        # Remove stale platform-specific extension artifacts that may have been
        # copied into build_lib from a developer's local source tree.
        for existing_name in os.listdir(dest_dir):
            if not existing_name.startswith('_catzilla'):
                continue
            if not existing_name.endswith(('.so', '.pyd', '.dylib')):
                continue

            existing_path = os.path.join(dest_dir, existing_name)
            if os.path.abspath(existing_path) == os.path.abspath(dest_path):
                continue

            try:
                os.remove(existing_path)
                print(f"Removed stale extension artifact: {existing_path}")
            except OSError as e:
                print(f"Warning: Could not remove stale extension artifact {existing_path}: {e}")

        # Use shutil.copy2 to preserve metadata and handle file operations better
        try:
            shutil.copy2(so_path, dest_path)
            print(f"Successfully copied {so_path} to {dest_path}")
        except Exception as e:
            print(f"Error copying extension: {e}")
            print(f"Source exists: {os.path.exists(so_path)}")
            print(f"Dest dir exists: {os.path.exists(dest_dir)}")
            raise

ext_modules = [Extension('catzilla._catzilla', sources=[])]

setup(
    name="catzilla",
    version="0.2.3rc4",
    ext_modules=ext_modules,
    cmdclass={"build_ext": CMakeBuild},
    python_requires=">=3.9",
    include_package_data=True,
    zip_safe=False,
)
