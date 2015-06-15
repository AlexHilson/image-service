from distutils.core import setup

setup(
    name='MOImageService',
    version='0.1dev',
    packages=['imageservice'],
    license='GPL3',
    long_description=open('README.txt').read(),
    packages=["tests",
              "Argparse",
              "Watchdog",
              "Logging",
              "Numpy",
              "PyOpenGL",
              "PyPng",
              "PySide",
              "Requests",
              "Scipy",
              "Vispy"]
)