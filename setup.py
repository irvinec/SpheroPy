import setuptools
from setuptools import setup
import sys

__version__ = '0.0.3'

ext_modules = []

extras_require = {
    'winble': ['winble'],
    'pygatt': ['pygatt'],
    'pybluez': ['pybluez']
}

install_requires = []

if sys.version_info < (3,6):
    sys.exit('Sorry, Python >= 3.6 is required')

setup(
    name='SpheroPy',
    version=__version__,
    author='Casey Irvine',
    author_email='caseyi@outlook.com',
    packages=['spheropy'],
    url='https://github.com/irvinec/SpheroPy',
    license='LICENSE',
    description='Control Sphero devices.',
    long_description=open('README.md').read(),
    install_requires=install_requires,
    extras_require=extras_require,
    zip_safe = False
)