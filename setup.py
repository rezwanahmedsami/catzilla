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

        # 1) Configure
        configure_cmd = [
            'cmake', '-S', '.', '-B', build_dir,
            f'-DPython3_EXECUTABLE={sys.executable}',
            f'-DCMAKE_OSX_DEPLOYMENT_TARGET={os.getenv("MACOSX_DEPLOYMENT_TARGET","10.15")}',
            f'-DUSE_JEMALLOC={"ON" if use_jemalloc else "OFF"}'
        ]

        if use_jemalloc:
            print(f"{platform_emoji('🚀', '>>')} Building Catzilla with jemalloc support...")
        else:
            print(f"{platform_emoji('⚠️', '!!')} Building Catzilla without jemalloc (fallback to standard malloc)")

        subprocess.check_call(configure_cmd)

        # 2) Build
        build_cmd = ['cmake', '--build', build_dir]
        # On Windows, explicitly use Release configuration to avoid python3XX_d.lib issues
        if sys.platform == 'win32':
            build_cmd.extend(['--config', 'Release'])
        subprocess.check_call(build_cmd)

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

        # 4) Copy it into your package
        dest_path = self.get_ext_fullpath('catzilla._catzilla')
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        self.copy_file(so_path, dest_path)

ext_modules = [Extension('catzilla._catzilla', sources=[])]

setup(
    name="catzilla",
    version="0.1.0",
    ext_modules=ext_modules,
    cmdclass={"build_ext": CMakeBuild},
    python_requires=">=3.8",
    include_package_data=True,
    zip_safe=False,
)
