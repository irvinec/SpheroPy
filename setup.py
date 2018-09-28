from distutils.core import setup

setup(
    name='TowelStuff',
    version='0.0.1',
    author='Casey Irvine',
    author_email='',
    packages=['sphero'],
    scripts=['bin/sphero.py',],
    url='http://pypi.python.org/pypi/sphero/',
    license='LICENSE.txt',
    description='',
    long_description=open('README.txt').read(),
    install_requires=[
    ],
)