# ping_test.py

import sphero

from bluetooth_interface import BluetoothInterface

def main():
    socket = BluetoothInterface()
    socket.connect()
    my_sphero = sphero.Sphero(socket)
    await my_sphero.ping()

if __name__ == "__main__": main()
