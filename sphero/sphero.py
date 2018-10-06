# sphero.py

# Should look at sphero_ros sphero_driver implementation.
# It looks pretty good but does not hide the right data.
# https://github.com/mmwise/sphero_ros

#import asyncio
import threading

import sphero.packets
import sphero.commands

__all__ = ['Sphero', 'CommandTimedOutError']

class CommandTimedOutError(Exception):
    """Exception thrown when a command times out."""

    def __init__(self):
        Exception.__init__(self)

class Sphero(object):
    """The main Sphero class that is used for interacting with a Sphero device.
    """

    def __init__(self, bluetooth_interface, response_timeout=0.5):
        self._bluetooth_interface = bluetooth_interface
        """Bluetooth interface object that implements send and receive"""
        self._response_timeout = response_timeout
        """Timeout value used when waiting for responses"""
        self._command_sequence_number = 0x00
        """The command sequence byte that needs to be passed when creating synchronous commands"""
        self._commands_waiting_for_response = {}

        # setup thread for receiving responses
        self._class_destroy_event = threading.Event()
        self._receive_thread = threading.Thread(target=self._receive_thread_run)
        self._receive_thread.daemon = True
        self._receive_thread.start()

        # declare private event listeners
        self._on_ping_response = None

    def __del__(self):
        self._class_destroy_event.set()

    def _receive_thread_run(self):
        receive_buffer = []
        while not self._class_destroy_event.is_set():
            receive_buffer.extend(self._bluetooth_interface.recv(1024))
            response_packet = None
            while len(receive_buffer) >= sphero.packets.MIN_PACKET_LENGTH:
                try:
                    response_packet = sphero.packets.SpheroResponsePacket(receive_buffer)
                    # we have a valid response to handle
                    # break out of the inner while loop to handle
                    # the response
                    break
                except sphero.packets.BufferNotLongEnoughError:
                    # break out of inner loop so we can fetch more data
                    break
                except sphero.packets.PacketParseError:
                    # this is an error in the packet format
                    # remove one byte from the buffer and try again
                    receive_buffer.pop(0)
                    continue

            # TODO: need to refactor this loop
            # to not have so many breaks and continues.
            if response_packet is None:
                continue

            if response_packet.is_async():
                pass # TODO: implement logic from here down
            else:
                # for ACK/sync responses we only need to call the registered callback.
                sequence_number = response_packet.get_sequence_number()
                if sequence_number in self._commands_waiting_for_response:
                    self._commands_waiting_for_response[sequence_number](response_packet)
                    # NOTE: it is up to the callback/waiting function to remove the handler.
            # remove the packet we just handled
            del receive_buffer[:response_packet.get_packet_length()]

    def _get_and_increment_command_sequence_number(self):
        result = self._command_sequence_number
        self._command_sequence_number += 1
        if self._command_sequence_number > 0xFF:
            self._command_sequence_number = 0x00

        return result

    # TODO: Do we need to let a timeout exist per command?
    async def ping(self, wait_for_response=True, reset_inactivity_timeout=True):
        """Sends ping command to the Sphero

        The Ping command is used to verify both a solid data link with the client
        and that Sphero is awake and dispatching commands.

        Args:
            wait_for_response (bool, True): If True, will wait for
                a response from the Sphero
            reset_inactivity_timeout (bool, True): If True, will
                reset the inactivity timer on the Sphero.
        """

        sequence_number = self._get_and_increment_command_sequence_number()
        ping_ack_response_event = threading.Event()
        if wait_for_response:
            self._commands_waiting_for_response[sequence_number] = (
                lambda response_packet: ping_ack_response_event.set()
            )

        ping_command = sphero.commands.create_ping_command(
            sequence_number,
            wait_for_response,
            reset_inactivity_timeout)

        self._bluetooth_interface.send(ping_command.get_bytes())

        if wait_for_response:
            timed_out = not ping_ack_response_event.wait(self._response_timeout)
            del self._commands_waiting_for_response[sequence_number]
            ping_ack_response_event.clear()
            if timed_out:
                raise CommandTimedOutError()
