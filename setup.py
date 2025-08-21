# setup.py
import os
import sys
import subprocess
import platform
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext

# Helper for platform-specific output
def is_windows():
    return platform.system() == "Windows"

def platform_emoji(emoji, alt_text):
    return alt_text if is_windows() else emoji

class CMakeBuild(build_ext):
    def run(self):
        subprocess.check_call(['cmake', '--version'])
        super().run()

    def build_extensions(self):
        build_dir = os.path.abspath(self.build_temp)
        os.makedirs(build_dir, exist_ok=True)

        # Check for jemalloc environment variable
        use_jemalloc = os.getenv('CATZILLA_USE_JEMALLOC', '1') == '1'

        # Python version compatibility checks
        python_version = sys.version_info
        print(f"Building for Python {python_version.major}.{python_version.minor}.{python_version.micro} on {platform.system()}")

        # Disable jemalloc for problematic Python versions in CI
        if python_version.minor == 11 and os.getenv('CI'):
            print("Warning: Disabling jemalloc for Python 3.11 in CI environment for compatibility")
            use_jemalloc = False

        # 1) Configure with robust compiler detection
        configure_cmd = [
            'cmake', '-S', '.', '-B', build_dir,
            f'-DPython3_EXECUTABLE={sys.executable}',
            f'-DUSE_JEMALLOC={"ON" if use_jemalloc else "OFF"}'
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
                # Force architecture detection for M1/Intel compatibility
                f'-DCMAKE_OSX_ARCHITECTURES={platform.machine()}'
            ])
        elif sys.platform.startswith('linux'):
            # Linux: Set compilers for Ubuntu CI compatibility
            configure_cmd.extend([
                '-DCMAKE_C_COMPILER=/usr/bin/gcc',
                '-DCMAKE_CXX_COMPILER=/usr/bin/g++'
            ])
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
            env['CC'] = env.get('CC', 'gcc')
            env['CXX'] = env.get('CXX', 'g++')
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
        try:
            # Change to source directory for CMake
            source_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(source_dir)

            subprocess.check_call(configure_cmd, env=env, cwd=source_dir)
        except subprocess.CalledProcessError as e:
            print(f"CMake configure failed with return code {e.returncode}")
            print("Attempting fallback configuration...")

            # Fallback: minimal configuration without extra flags
            fallback_cmd = [
                'cmake', '-S', '.', '-B', build_dir,
                f'-DPython3_EXECUTABLE={sys.executable}',
                f'-DUSE_JEMALLOC={"ON" if use_jemalloc else "OFF"}'
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

        # 2) Build with environment preservation
        build_cmd = ['cmake', '--build', build_dir]
        # On Windows, explicitly use Release configuration to avoid python3XX_d.lib issues
        if sys.platform == 'win32':
            build_cmd.extend(['--config', 'Release'])

        # Add parallel build support for faster compilation
        if sys.platform != 'win32':
            import multiprocessing
            build_cmd.extend(['--parallel', str(min(multiprocessing.cpu_count(), 8))])

        # Ensure we build from the right directory
        source_dir = os.path.dirname(os.path.abspath(__file__))
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

        # Use shutil.copy2 to preserve metadata and handle file operations better
        import shutil
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
    version="0.2.0",
    ext_modules=ext_modules,
    cmdclass={"build_ext": CMakeBuild},
    python_requires=">=3.9",
    include_package_data=True,
    zip_safe=False,
)
