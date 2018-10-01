# packets.py

class PacketError(Exception):
    pass

class PacketCreationError(PacketError):
    """
    """
    def __init__(self, message):
        self.message = message

class PacketParseError(PacketError):
    """
    """
    def __init__(self, message):
        self.message = message

START_OF_PACKET_BYTE_1 = 0xFF

START_OF_PACKET_BYTE_2_SYNC = 0xFF
START_OF_PACKET_BYTE_2_ASYNC = 0xFE

DEVICE_ID_BYTE_CORE = 0x00
DEVICE_ID_BYTE_SPHERO = 0x02

COMMAND_ID_BYTE_PING = 0x01

ID_CODE_POWER_NOTIFICATION = 0x01
ID_CODE_LEVEL_1_DIAGNOSTICS = 0x02
# TODO: Fill the rest out if it makes sense.

def _compute_checksum(packet):
    """Computes the checksum of a packet in list of byte form

        Args:
            packet (list): List of bytes for a packet.
                packet must not contain a checksum
                as the last element

        Returns:
            The computed checksum
    """

    return ~(sum(packet[2:]) % 256)


class ClientCommandPacket:
    """Represents a command packet sent from the client to a Sphero device
    """
    def __init__(self,
        start_of_packet_byte_2,
        device_id_byte,
        command_id_byte,
        sequence_number_byte = 0x00,
        data = []):
        if start_of_packet_byte_2 < 0xF8 or start_of_packet_byte_2 > 0xFF:
            raise PacketCreationError("Start of Packet Byte 2 was outside the allowed range. SOP2 = {:X}".format(start_of_packet_byte_2))

        self._packet = [
            START_OF_PACKET_BYTE_1,
            start_of_packet_byte_2,
            device_id_byte,
            command_id_byte,
            sequence_number_byte,
            max(len(data) + 1, 0xFF),
            ].extend(data)

        self._packet.append(_compute_checksum(self._packet))

    def get_packet(self):
        return self._packet

    def get_bytes(self):
        return bytes(self._packet)

class SpheroResponsePacket:
    """Represents a response packet from a Sphero to the client

    Will parse packet provided to constructor
    """

    def __init__(self, packet):
        self._checksum = packet[-1]
        if self._checksum is not _compute_checksum(packet[:-1]):
            raise PacketParseError("Checksum is not correct")

        self._start_of_packet_byte_1 = packet[0]
        self._start_of_packet_byte_2 = packet[1]
        # TODO: tag this as a response SOP2 since it is different than command
        # TODO: we also probably want to do more with masking the SOP2 bytes for sending since there are two bytes that have different meaning
        # 0xFC is the base and then we can OR in the other bytes
        if self._start_of_packet_byte_2 is START_OF_PACKET_BYTE_2_SYNC:
            self._message_response_byte = packet[3]
            self._sequence_number_byte = packet[4]
            self._data_length = packet[5]

        else:
            self.id_code = packet[3]
            self._data_length = packet[4] << 8 | packet[5]

        self._data = packet[6:-1]
        if len(self._data) is not self._data_length - 1:
            raise PacketParseError("Length of data does not match data length byte. length = {:X} dlen = {:X}".format(len(self._data), self._data_length - 1))

    # TODO: add member methods to get useful data.



