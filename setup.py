import setuptools
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys

# See https://github.com/pybind/python_example/blob/master/setup.py

__version__ = '0.0.1'

class get_pybind_include(object):
    """Helper class to determine the pybind11 include path
    The purpose of this class is to postpone importing pybind11
    until it is actually installed, so that the ``get_include()``
    method can be invoked. """

    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    c_opts = {
        'msvc': ['/EHsc', '/std:c++17', '/await', '/permissive-'],
        'unix': [],
    }

    if sys.platform == 'darwin':
        c_opts['unix'] += ['-stdlib=libc++', '-mmacosx-version-min=10.7']

    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        if ct == 'unix':
            opts.append(f'-DVERSION_INFO="{self.distribution.get_version()}"')
            opts.append('-std=c++17')
            if self.compiler.has_flag('-fvisibility=hidden'):
                opts.append('-fvisibility=hidden')
        elif ct == 'msvc':
            opts.append(f'/DVERSION_INFO=\\"{self.distribution.get_version()}\\"')
        for ext in self.extensions:
            # TODO: we should probably append opts to existing extra_compile_args
            ext.extra_compile_args = opts
        build_ext.build_extensions(self)

winble_module = Extension(
    'winble',
    sources=['winble/winble.cpp'],
    include_dirs=[
        # Path to pybind11 headers
        get_pybind_include(),
        get_pybind_include(user=True)
    ],
    language='c++',
)

ext_modules = [winble_module]

setup(
    name='SpheroPy',
    version=__version__,
    author='Casey Irvine',
    author_email='',
    packages=['spheropy'],
    ext_modules=ext_modules,
    url='https://github.com/irvinec/SpheroPy',
    license='LICENSE',
    description='',
    long_description=open('README.md').read(),
    install_requires=[
        'pybind11>=2.2'
    ],
    cmdclass={'build_ext': BuildExt},
    zip_safe = False
)