# SpheroPy
Python wrapper/implementation of the Orbotix Sphero APIs.

**Under Construction**, but many commands have been implemented.

# Supported Platforms
SpheroPy is supported and tested on Windows and Linux.\
SpheroPy is theoretically supported on Mac, but has not been tested on Mac.

# Dependencies
SpheroPy depends on
- pybluez - for bluetooth support
- pygatt - for ble support.

# Install
Right now only install from source is supported.\
Run\
```pip install git+https://github.com/irvinec/SpheroPy```\
or\
after cloning this repository locally, cd into the root directory (the directory containing the setup.py file).\
Then run\
```pip install -e .```\
or\
```python setup.py install```

If you are using miniconda or anaconda, you can run\
```conda create --name <env name>```\
```conda activate <env name>```\
```python setup_spheropy_env.py```\
or for a SpheroPy development environment run\
```python setup_spheropy_dev_env.py```\
then install SpheroPy with\
```pip install -e .```

# Examples
See files in the tests directory for examples on how to use the APIs.

# License
This software is made available under the MIT License.
See the license file for more details.
