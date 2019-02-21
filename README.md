# SpheroPy
An unofficial Sphero Python SDK to programmatically control Sphero robots.

# Project Status
**Now Available on PyPi!**

**Early Alpha**\
Many commands have been implemented and we now have early alpha releases.\
Be aware that releases are frequent and breaking changes can happen at this stage of development.

# Supported Platforms
SpheroPy is supported and tested on Windows and Linux.\
SpheroPy is theoretically supported on Mac, but has not been tested on Mac.

# Dependencies
SpheroPy requires Python 3.6 or greater.

SpheroPy needs a low-level bluetooth interface provider in order to talk to Sphero devices.\
You can choose to optionally install a bluetooth interface provider along with SpheroPy (see install).\
SpheroPy has optional depedencies on:
- **pybluez**
    - For bluetooth support. Useful for talking to first-gen Sphero devices that don't implement BLE.
    - [pybluez github](https://github.com/pybluez/pybluez)
- **pygatt**
    - For bluetooth LE support. Supported on linux. Also, supported on any platform with a BGAPI supported adapter.
    - Example of BGAPI adapter: https://www.silabs.com/products/wireless/bluetooth/bluetooth-low-energy-modules/bled112-bluetooth-smart-dongle
    - [pygatt github](https://github.com/peplin/pygatt)
- **winble**
    - For bluetooth LE support on Windows. Winble is a native bluetooth LE library for Windows. Requires VS2017 to build from source, but wheel distribution is available.
    - [winble github](https://github.com/irvinec/SpheroPy/tree/master/winble)

# Install
To install SpheroPy:\
```pip install spheropy```

To update SpheroPy:\
```pip install --upgrade spheropy```

To install with optional bluetooth interface dependency:\
```pip install spheropy[<dependency>]```\
Replace `<dependency>` with **pybluez**, **pygatt**, or **winble** (see Dependencies).

# Examples
See files in the [tests](https://github.com/irvinec/SpheroPy/tree/master/tests) directory for examples on how to use the APIs.

# License
This software is made available under the MIT License.
See the license file for more details.
