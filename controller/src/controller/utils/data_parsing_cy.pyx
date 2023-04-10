# distutils: language = c++
# cython: language_level=3
# Tanner (9/1/20): Make sure to set `linetrace=False` except when profiling cython code or creating annotation file. All performance tests should be timed without line tracing enabled. Cython files in this package can easily be recompiled with `pip install -e .`
# cython: linetrace=False
"""Parsing data from instrument firmware."""
from ..constants import NUM_WELLS
from ..constants import SERIAL_COMM_PAYLOAD_INDEX
from ..constants import SERIAL_COMM_CHECKSUM_LENGTH_BYTES
from ..constants import SERIAL_COMM_DATA_SAMPLE_LENGTH_BYTES
from ..constants import SERIAL_COMM_MAGIC_WORD_BYTES
from ..constants import SERIAL_COMM_PACKET_METADATA_LENGTH_BYTES
from ..constants import SERIAL_COMM_PACKET_REMAINDER_SIZE_LENGTH_BYTES
from ..constants import SERIAL_COMM_TIME_OFFSET_LENGTH_BYTES
from ..constants import SerialCommPacketTypes
from ..exceptions import SerialCommIncorrectChecksumFromInstrumentError
from ..exceptions import SerialCommIncorrectMagicWordFromInstrumentError

from libc.stdint cimport int64_t
from libc.stdint cimport uint8_t
from libc.stdint cimport uint16_t
from libc.stdint cimport uint32_t
from libc.stdint cimport uint64_t
from libc.string cimport strncpy
from libc.string cimport strncmp
# import numpy correctly
import numpy as np
cimport numpy as np
np.import_array()

cdef extern from "../zlib/zlib.h":
    ctypedef unsigned char Bytef
    ctypedef unsigned long uLong
    ctypedef unsigned int uInt

    uLong crc32(uLong, Bytef*, uInt)
    Bytef* Z_NULL


# Tanner (5/26/21): Can't import these constants from python and use them in array declarations, so have to redefine them here
DEF MAGIC_WORD_LEN = 8
DEF NUM_CHANNELS_PER_SENSOR = 3

# these values exist only for importing the constants defined above into the python test suite
SERIAL_COMM_MAGIC_WORD_LENGTH_BYTES_CY = MAGIC_WORD_LEN
SERIAL_COMM_NUM_CHANNELS_PER_SENSOR_CY = NUM_CHANNELS_PER_SENSOR

# convert python constants to C types
cdef char[MAGIC_WORD_LEN + 1] MAGIC_WORD = SERIAL_COMM_MAGIC_WORD_BYTES + bytes(1)
cdef int SERIAL_COMM_PRS_LENGTH_BYTES_C_INT = SERIAL_COMM_PACKET_REMAINDER_SIZE_LENGTH_BYTES
cdef int SERIAL_COMM_CHECKSUM_LENGTH_BYTES_C_INT = SERIAL_COMM_CHECKSUM_LENGTH_BYTES

cdef int PACKET_HEADER_LEN = MAGIC_WORD_LEN + SERIAL_COMM_PRS_LENGTH_BYTES_C_INT
cdef int MIN_PACKET_SIZE = SERIAL_COMM_PACKET_METADATA_LENGTH_BYTES

cdef int SERIAL_COMM_TIME_OFFSET_LENGTH_BYTES_C_INT = SERIAL_COMM_TIME_OFFSET_LENGTH_BYTES
cdef int SERIAL_COMM_DATA_SAMPLE_LENGTH_BYTES_C_INT = SERIAL_COMM_DATA_SAMPLE_LENGTH_BYTES
cdef int SERIAL_COMM_NUM_CHANNELS_PER_SENSOR_C_INT = NUM_CHANNELS_PER_SENSOR

cdef int SERIAL_COMM_PAYLOAD_INDEX_C_INT = SERIAL_COMM_PAYLOAD_INDEX
cdef int SERIAL_COMM_STIM_STATUS_PACKET_TYPE_C_INT = SerialCommPacketTypes.STIM_STATUS


cdef int TOTAL_NUM_WELLS_C_INT = NUM_WELLS


cdef packed struct Packet:
    char magic[MAGIC_WORD_LEN]
    uint16_t packet_len
    uint64_t timestamp
    uint8_t packet_type
    uint8_t additional_bytes


cdef packed struct SensorData:
    uint16_t time_offset
    uint16_t data_points[NUM_CHANNELS_PER_SENSOR]


cdef packed struct MagnetometerData:
    uint64_t time_index
    SensorData sensor_data


cdef int TIME_INDEX_LEN = sizeof(uint64_t)


cdef int get_checksum_index(int packet_len):
    return packet_len + PACKET_HEADER_LEN - SERIAL_COMM_CHECKSUM_LENGTH_BYTES_C_INT


cpdef dict sort_serial_packets(unsigned char [:] read_bytes):
    """Sort all complete packets from the given buffer by packet type.

    Args:
        read_bytes: an array of all bytes to be parsed are sorted by packet type

    Returns:
        A dict whose values consist of a dict containing a bytearray and the number of packets found for both
        magnetometer data and stim data, a list of bytearrays of all other data packets, and a bytearray of
        all remaining bytes that were not sorted (usually part of an incomplete packet)
    """
    read_bytes = read_bytes.copy()  # make sure data is C contiguous
    cdef int num_bytes = len(read_bytes)

    # generic data parsing values
    cdef int num_packets_sorted = 0
    cdef unsigned char [:] packet_payload
    cdef int payload_len
    cdef int relative_checksum_idx

    # magnetometer data parsing values
    cdef unsigned char [:] mag_data_packet_bytes = bytearray(num_bytes)
    cdef int mag_data_packet_byte_idx = 0
    cdef int num_mag_data_packets = 0

    # stim data parsing values
    cdef unsigned char [:] stim_packet_bytes = bytearray(num_bytes)
    cdef int stim_packet_byte_idx = 0
    cdef int num_stim_packets = 0

    # list for storing non-data packets
    other_packet_info = list()

    # packet integrity values
    cdef unsigned int crc, original_crc
    cdef char[MAGIC_WORD_LEN + 1] magic_word
    magic_word[MAGIC_WORD_LEN] = 0

    cdef Packet *p
    cdef int bytes_idx = 0
    cdef int payload_start_idx, checksum_start_idx

    while bytes_idx <= num_bytes - MIN_PACKET_SIZE:
        p = <Packet *> &read_bytes[bytes_idx]

        # make sure data packet is complete before attempting to parse
        if num_bytes - (bytes_idx + PACKET_HEADER_LEN) < p.packet_len:
            break

        # check that magic word is correct
        strncpy(magic_word, p.magic, MAGIC_WORD_LEN)
        if strncmp(magic_word, MAGIC_WORD, MAGIC_WORD_LEN) != 0:
            raise SerialCommIncorrectMagicWordFromInstrumentError(
                f"At byte idx: {bytes_idx} of {num_bytes}: {list(bytes(read_bytes[bytes_idx : bytes_idx + MAGIC_WORD_LEN]))}"
            )

        relative_checksum_idx = get_checksum_index(p.packet_len)

        # get actual CRC value from packet
        original_crc = (<uint32_t *> ((<uint8_t *> &p.magic) + relative_checksum_idx))[0]
        # calculate expected CRC value
        crc = crc32(0, Z_NULL, 0)
        crc = crc32(crc, <uint8_t *> &p.magic, relative_checksum_idx)
        # check that actual CRC is the expected value. Do this before checking if it is a data packet
        if crc != original_crc:
            # raising error here, so ok to incur python overhead
            packet_end_idx = bytes_idx + PACKET_HEADER_LEN + p.packet_len
            full_data_packet = bytearray(read_bytes[bytes_idx : packet_end_idx])
            raise SerialCommIncorrectChecksumFromInstrumentError(
                f"Checksum Received: {original_crc}, Checksum Calculated: {crc}, Full Data Packet (bytes {bytes_idx} to {packet_end_idx}): {list(full_data_packet)}"
            )

        payload_start_idx = bytes_idx + SERIAL_COMM_PAYLOAD_INDEX_C_INT
        checksum_start_idx = bytes_idx + relative_checksum_idx

        packet_payload = read_bytes[payload_start_idx : checksum_start_idx]
        payload_len = checksum_start_idx - payload_start_idx

        if p.packet_type == SERIAL_COMM_STIM_STATUS_PACKET_TYPE_C_INT:
            stim_packet_bytes[
                stim_packet_byte_idx : stim_packet_byte_idx + payload_len
            ] = packet_payload
            stim_packet_byte_idx += payload_len
            num_stim_packets += 1
        else:
            # exceptional case, so ok to incur reasonable amount of python overhead here
            other_packet_info.append((p.timestamp, p.packet_type, bytearray(packet_payload)))

        bytes_idx += PACKET_HEADER_LEN + p.packet_len
        num_packets_sorted += 1

    return {
        "num_packets_sorted": num_packets_sorted,
        "magnetometer_stream_info": {
            "raw_bytes": mag_data_packet_bytes[:mag_data_packet_byte_idx],
            "num_packets": num_mag_data_packets,
        },
        "stim_stream_info": {
            "raw_bytes": stim_packet_bytes[:stim_packet_byte_idx],
            "num_packets": num_stim_packets,
        },
        "other_packet_info": other_packet_info,
        "unread_bytes": bytearray(read_bytes[bytes_idx:]),
    }


cpdef dict parse_stim_data(unsigned char [:] stim_packet_bytes, int num_stim_packets):
    cdef dict stim_data_dict = {}  # dict for storing stim statuses

    # Tanner (10/15/21): No need to heavily optimize this function until stim waveforms are streamed
    cdef int64_t time_index
    cdef int num_status_updates
    cdef int stim_packet_idx
    cdef int bytes_idx = 0

    for stim_packet_idx in range(num_stim_packets):
        num_status_updates = stim_packet_bytes[bytes_idx]
        bytes_idx += 1
        for _ in range(num_status_updates):
            protocol_idx = stim_packet_bytes[bytes_idx]
            time_index = (<uint64_t *> &stim_packet_bytes[bytes_idx + 1])[0]
            stim_status = stim_packet_bytes[bytes_idx + 2]
            subprotocol_idx = stim_packet_bytes[bytes_idx + 2 + TIME_INDEX_LEN]
            bytes_idx += 2 + TIME_INDEX_LEN + 1

            if protocol_idx not in stim_data_dict:
                stim_data_dict[protocol_idx] = [[time_index], [subprotocol_idx]]
            else:
                stim_data_dict[protocol_idx][0].append(time_index)
                stim_data_dict[protocol_idx][1].append(subprotocol_idx)

    # convert stim status lists to arrays
    for protocol_idx, stim_statuses in stim_data_dict.items():
        stim_data_dict[protocol_idx] = np.array(stim_statuses, dtype=np.int64)  # Tanner (10/18/21): using int64 here since top bit will never be used and these values can be negative

    return stim_data_dict
