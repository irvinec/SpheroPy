"""
"""

import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--ble', dest='use_ble', action='store_true',
        help='Specify that the test should use Bluetooth Low Energy (BLE).'
    )
    return parser.parse_args()
