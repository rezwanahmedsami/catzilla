# setup.py
import os
import sys
import subprocess
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

class CMakeBuild(build_ext):
    def run(self):
        subprocess.check_call(['cmake', '--version'])
        super().run()

    def build_extensions(self):
        build_dir = os.path.abspath(self.build_temp)
        os.makedirs(build_dir, exist_ok=True)

        # 1) Configure
        subprocess.check_call([
            'cmake', '-S', '.', '-B', build_dir,
            f'-DPython3_EXECUTABLE={sys.executable}',
            f'-DCMAKE_OSX_DEPLOYMENT_TARGET={os.getenv("MACOSX_DEPLOYMENT_TARGET","10.15")}'
        ])

        # 2) Build
        subprocess.check_call(['cmake', '--build', build_dir])

        # 3) Locate the one _catzilla.so
        so_path = os.path.join(build_dir, '_catzilla.so')
        if not os.path.isfile(so_path):
            # debugging dump
            print("=== build_dir contents ===", os.listdir(build_dir))
            raise RuntimeError(f"Expected {_catzilla.so} in {build_dir}, but not found")
        
        # 4) Copy it into your package
        dest_path = self.get_ext_fullpath('catzilla._catzilla')
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        self.copy_file(so_path, dest_path)

ext_modules = [Extension('catzilla._catzilla', sources=[])]

setup(
    name="catzilla",
    version="0.1.0",
    packages=["catzilla"],
    package_dir={"catzilla": "python/catzilla"},
    ext_modules=ext_modules,
    cmdclass={"build_ext": CMakeBuild},
    install_requires=["pydantic>=2.0"],
    python_requires=">=3.8",
    include_package_data=True,
    zip_safe=False,
)
