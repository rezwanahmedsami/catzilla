from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import subprocess

class CMakeBuild(build_ext):
    def run(self):
        subprocess.check_call(["cmake", "-S", ".", "-B", "build"])
        subprocess.check_call(["cmake", "--build", "build"])
        
setup(
    name="catzilla",
    version="0.1.0",
    packages=["catzilla"],
    package_dir={"": "python"},
    ext_modules=[Extension("catzilla._native", [])],
    cmdclass={"build_ext": CMakeBuild},
    install_requires=["pydantic>=2.0"],
)