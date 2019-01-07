"""
"""

import bluetooth # pybluez

class BluetoothInterface(object):
    """
    """

    def __init__(self, target_name='Sphero', target_address=None, port=1):
        self._target_name = target_name
        self._port = port
        self._tries = 0
        self._target_address = target_address
        self._sock = None


    def __del__(self):
        self.close()


    def connect(self):
        """
        """

        if self._target_address is None:
            # search for a matching device
            found_device = False
            for _ in range(10):
                nearby_devices = bluetooth.discover_devices(lookup_names=True)
                if nearby_devices:
                    for target_address, name in nearby_devices:
                    # look for a device name that starts with the target name
                        if name.startswith(self._target_name):
                            found_device = True
                            self._target_address = target_address
                            break
                if found_device:
                    break
                else:
                    raise RuntimeError(
                        "Could not find device with name {}".format(self._target_name)
                    )

        self._sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self._sock.connect((self._target_address, self._port))


    def send(self, data):
        """
        """

        self._sock.send(data)


    def recv(self, num_bytes):
        """
        """

        return self._sock.recv(num_bytes)


    def close(self):
        """
        """

        if self._sock is not None:
            self._sock.close()
