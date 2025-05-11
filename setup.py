from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import subprocess
import os
import sys

class CMakeBuild(build_ext):
    def build_extensions(self):
        # Ensure CMake is present
        subprocess.check_call(['cmake', '--version'])
        
        # Create build directory
        build_dir = os.path.abspath(self.build_temp)
        os.makedirs(build_dir, exist_ok=True)
        
        # Configure with Python executable
        python_exe = sys.executable
        subprocess.check_call([
            'cmake', '-S', '.', '-B', build_dir,
            f'-DPython3_EXECUTABLE={python_exe}',
            f'-DCMAKE_OSX_DEPLOYMENT_TARGET={os.getenv("MACOSX_DEPLOYMENT_TARGET", "10.15")}'
        ])
        
        # Build
        subprocess.check_call(['cmake', '--build', build_dir])
        
        # Copy built library
        dest_path = self.get_ext_fullpath('catzilla._catzilla')
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        self.copy_file(os.path.join(build_dir, '_catzilla.so'), dest_path)

setup(
    name="catzilla",
    version="0.1.0",
    packages=["catzilla"],
    package_dir={"catzilla": "python/catzilla"},
    ext_modules=[Extension('catzilla._catzilla', sources=[])],
    cmdclass={"build_ext": CMakeBuild},
    install_requires=["pydantic>=2.0"],
    python_requires=">=3.8",
    include_package_data=True,
    zip_safe=False,
)