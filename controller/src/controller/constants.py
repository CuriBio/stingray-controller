# -*- coding: utf-8 -*-
"""Constants for the Stingray Controller."""
from collections import namedtuple
import datetime
from enum import Enum
from enum import IntEnum
import uuid

from immutabledict import immutabledict
from labware_domain_models import LabwareDefinition


# General
CURRENT_SOFTWARE_VERSION = "1.0.9"  # TODO  "REPLACETHISWITHVERSIONDURINGBUILD"
COMPILED_EXE_BUILD_TIMESTAMP = "REPLACETHISWITHTIMESTAMPDURINGBUILD"
SOFTWARE_RELEASE_CHANNEL = "REPLACETHISWITHRELEASECHANNELDURINGBUILD"

DEFAULT_SERVER_PORT_NUMBER = 4567

NUM_WELLS = 24
GENERIC_24_WELL_DEFINITION = LabwareDefinition(row_count=4, column_count=6)

AuthTokens = namedtuple("AuthTokens", ["access", "refresh"])
AuthCreds = namedtuple("AuthCreds", ["customer_id", "username", "password"])
ConfigSettings = namedtuple("ConfigSettings", ["auto_upload_on_completion", "log_directory"])

VALID_CREDENTIAL_TYPES = frozenset(AuthCreds._fields)
VALID_CONFIG_SETTINGS = frozenset(ConfigSettings._fields)

# TODO try replacing all immutabledicts with enums
BARCODE_HEADERS: immutabledict[str, str] = immutabledict({"plate_barcode": "ML", "stim_barcode": "MS"})
ALL_VALID_BARCODE_HEADERS = frozenset(BARCODE_HEADERS.values())

MICROS_PER_MILLIS = int(1e3)
MICRO_TO_BASE_CONVERSION = int(1e6)

# Cloud APIs
CLOUD_ENDPOINT_USER_OPTION = "REPLACETHISWITHENDPOINTDURINGBUILD"
CLOUD_ENDPOINT_VALID_OPTIONS: immutabledict[str, str] = immutabledict(
    {"test": "curibio-test", "prod": "curibio"}
)
CLOUD_DOMAIN = CLOUD_ENDPOINT_VALID_OPTIONS.get(
    CLOUD_ENDPOINT_USER_OPTION, "curibio"
)  # TODO change this back
CLOUD_API_ENDPOINT = f"apiv2.{CLOUD_DOMAIN}.com"
CLOUD_PULSE3D_ENDPOINT = f"pulse3d.{CLOUD_DOMAIN}.com"


# System
SERVER_BOOT_UP_TIMEOUT_SECONDS = 5


class SystemStatuses(Enum):
    # boot up states
    SERVER_INITIALIZING_STATE = uuid.UUID("04471bcf-1a00-4a0d-83c8-4160622f9a25")
    SERVER_READY_STATE = uuid.UUID("8e24ef4d-2353-4e9d-aa32-4346126e73e3")
    SYSTEM_INITIALIZING_STATE = uuid.UUID("d2e3d386-b760-4c9a-8b2d-410362ff11c4")
    CHECKING_FOR_UPDATES_STATE = uuid.UUID("04fd6f6b-ee9e-4656-aae4-0b9584791f36")
    # normal operation states
    IDLE_READY_STATE = uuid.UUID("009301eb-625c-4dc4-9e92-1a4d0762465f")
    # updating states
    UPDATES_NEEDED_STATE = uuid.UUID("d6dcf2a9-b6ea-4d4e-9423-500f91a82a2f")
    DOWNLOADING_UPDATES_STATE = uuid.UUID("b623c5fa-af01-46d3-9282-748e19fe374c")
    INSTALLING_UPDATES_STATE = uuid.UUID("19c9c2d6-0de4-4334-8cb3-a4c7ab0eab00")
    UPDATES_COMPLETE_STATE = uuid.UUID("31f8fbc9-9b41-4191-8598-6462b7490789")
    UPDATE_ERROR_STATE = uuid.UUID("33742bfc-d354-4ae5-88b6-2b3cee23aff8")


# TODO redo these
class ErrorCodes(IntEnum):
    INSTRUMENT_NOT_FOUND = 1
    INSTRUMENT_CONNECTION_CREATION = 2
    INSTRUMENT_CONNECTION_LOST = 3
    INSTRUMENT_SENT_BAD_DATA = 4
    INSTRUMENT_STATUS_CODE = 5
    INSTRUMENT_FW_INCOMPATIBLE_WITH_SW = 6
    UI_SENT_BAD_DATA = 7
    # These by nature cannot be set by the controller itself, and thus are only here for documentation
    CONTROLLER_CONNECTION_CREATION = 8
    CONTROLLER_CONNECTION_LOST = 9
    CONTROLLER_SENT_BAD_DATA = 10
    # This ideally should never happen, but creating it just in case
    UNSPECIFIED = 999


# Serial Communication Values
STM_VID = 1155
CURI_VID = 1027
SERIAL_COMM_BAUD_RATE = int(5e6)

MAX_MC_REBOOT_DURATION_SECONDS = 15
MAX_MAIN_FIRMWARE_UPDATE_DURATION_SECONDS = 60
MAX_CHANNEL_FIRMWARE_UPDATE_DURATION_SECONDS = 600

SERIAL_COMM_NUM_ALLOWED_MISSED_HANDSHAKES = 3

SERIAL_COMM_TIMESTAMP_EPOCH = datetime.datetime(year=2021, month=1, day=1, tzinfo=datetime.timezone.utc)

SERIAL_COMM_STATUS_BEACON_PERIOD_SECONDS = 5
SERIAL_COMM_HANDSHAKE_PERIOD_SECONDS = 5
SERIAL_COMM_REGISTRATION_TIMEOUT_SECONDS = 8
# Tanner (3/22/22): The following values are probably much larger than they need to be, not sure best duration of time to use now that a command might be sent right before or during a FW reboot initiated automatically by a FW error
SERIAL_COMM_STATUS_BEACON_TIMEOUT_SECONDS = SERIAL_COMM_STATUS_BEACON_PERIOD_SECONDS * 2
SERIAL_COMM_HANDSHAKE_TIMEOUT_SECONDS = SERIAL_COMM_HANDSHAKE_PERIOD_SECONDS * 2
SERIAL_COMM_RESPONSE_TIMEOUT_SECONDS = SERIAL_COMM_STATUS_BEACON_PERIOD_SECONDS * 2

# general packet components
SERIAL_COMM_MAGIC_WORD_BYTES = b"CURI BIO"
SERIAL_COMM_PACKET_REMAINDER_SIZE_LENGTH_BYTES = 2
SERIAL_COMM_TIMESTAMP_LENGTH_BYTES = 8
SERIAL_COMM_PACKET_TYPE_LENGTH_BYTES = 1
SERIAL_COMM_CHECKSUM_LENGTH_BYTES = 4


SERIAL_COMM_PACKET_HEADER_LENGTH_BYTES = (
    len(SERIAL_COMM_MAGIC_WORD_BYTES) + SERIAL_COMM_PACKET_REMAINDER_SIZE_LENGTH_BYTES
)
SERIAL_COMM_PACKET_BASE_LENGTH_BYTES = (
    SERIAL_COMM_TIMESTAMP_LENGTH_BYTES + SERIAL_COMM_PACKET_TYPE_LENGTH_BYTES
)
SERIAL_COMM_PACKET_METADATA_LENGTH_BYTES = (
    SERIAL_COMM_PACKET_HEADER_LENGTH_BYTES
    + SERIAL_COMM_PACKET_BASE_LENGTH_BYTES
    + SERIAL_COMM_CHECKSUM_LENGTH_BYTES
)

SERIAL_COMM_MAX_PAYLOAD_LENGTH_BYTES = 20000 - SERIAL_COMM_CHECKSUM_LENGTH_BYTES
SERIAL_COMM_MAX_FULL_PACKET_LENGTH_BYTES = (
    SERIAL_COMM_PACKET_METADATA_LENGTH_BYTES + SERIAL_COMM_MAX_PAYLOAD_LENGTH_BYTES
)

SERIAL_COMM_STATUS_CODE_LENGTH_BYTES = 2 + NUM_WELLS  # main micro, idx of thread with error, 24 wells
# data stream components
SERIAL_COMM_TIME_INDEX_LENGTH_BYTES = 8
SERIAL_COMM_TIME_OFFSET_LENGTH_BYTES = 2
SERIAL_COMM_DATA_SAMPLE_LENGTH_BYTES = 2

SERIAL_COMM_MAX_TIMESTAMP_VALUE = 2 ** (8 * SERIAL_COMM_TIMESTAMP_LENGTH_BYTES) - 1

SERIAL_COMM_TIMESTAMP_BYTES_INDEX = (
    len(SERIAL_COMM_MAGIC_WORD_BYTES) + SERIAL_COMM_PACKET_REMAINDER_SIZE_LENGTH_BYTES
)
SERIAL_COMM_PACKET_TYPE_INDEX = SERIAL_COMM_TIMESTAMP_BYTES_INDEX + SERIAL_COMM_TIMESTAMP_LENGTH_BYTES
SERIAL_COMM_PAYLOAD_INDEX = SERIAL_COMM_PACKET_TYPE_INDEX + 1


class SerialCommPacketTypes(IntEnum):
    # General
    STATUS_BEACON = 0
    MAGNETOMETER_DATA = 1
    REBOOT = 2
    HANDSHAKE = 4
    PLATE_EVENT = 6
    GOING_DORMANT = 10
    # Stimulation
    SET_STIM_PROTOCOL = 20
    START_STIM = 21
    STOP_STIM = 22
    STIM_STATUS = 23
    STIM_IMPEDANCE_CHECK = 27
    # Magnetometer
    SET_SAMPLING_PERIOD = 50
    START_DATA_STREAMING = 52
    STOP_DATA_STREAMING = 53
    # Metadata
    GET_METADATA = 60
    SET_NICKNAME = 62
    # Firmware Updating
    BEGIN_FIRMWARE_UPDATE = 70
    FIRMWARE_UPDATE = 71
    END_FIRMWARE_UPDATE = 72
    CF_UPDATE_COMPLETE = 73
    MF_UPDATE_COMPLETE = 74
    # Barcode
    BARCODE_FOUND = 90
    # Misc?
    TRIGGER_ERROR = 103
    # Errors
    ERROR_ACK = 254
    CHECKSUM_FAILURE = 255


# Instrument Status Codes
SERIAL_COMM_OKAY_CODE = 0
# Command Response Info
SERIAL_COMM_COMMAND_SUCCESS_BYTE = 0
SERIAL_COMM_COMMAND_FAILURE_BYTE = 1
# Going Dormant Codes
GOING_DORMANT_HANDSHAKE_TIMEOUT_CODE = 0


# Stimulation
STIM_MAX_ABSOLUTE_CURRENT_MICROAMPS = int(100e3)
STIM_MAX_ABSOLUTE_VOLTAGE_MILLIVOLTS = int(1.2e3)

STIM_MAX_DUTY_CYCLE_PERCENTAGE = 0.8
STIM_MAX_DUTY_CYCLE_DURATION_MICROSECONDS = int(50e3)

STIM_MAX_PULSE_DURATION_MICROSECONDS = int(50e3)
STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS = int(100e3)
STIM_MAX_SUBPROTOCOL_DURATION_MICROSECONDS = 24 * 60 * 60 * MICRO_TO_BASE_CONVERSION  # 24hrs

# Protocol Chunking
STIM_MAX_CHUNKED_SUBPROTOCOL_DUR_MINS = 1
STIM_MAX_CHUNKED_SUBPROTOCOL_DUR_MICROSECONDS = (
    STIM_MAX_CHUNKED_SUBPROTOCOL_DUR_MINS * 60 * MICRO_TO_BASE_CONVERSION
)

STIM_MAX_NUM_SUBPROTOCOLS_PER_PROTOCOL = 50

STIM_COMPLETE_SUBPROTOCOL_IDX = 255

STIM_NO_PROTOCOL_ASSIGNED = 255

# Stimulator Impedance Thresholds
STIM_OPEN_CIRCUIT_THRESHOLD_OHMS = 20000
STIM_SHORT_CIRCUIT_THRESHOLD_OHMS = 10

# Stim Subprotocols
VALID_STIMULATION_TYPES = frozenset(["C", "V"])
VALID_SUBPROTOCOL_TYPES = frozenset(["delay", "monophasic", "biphasic"])

# does not include subprotocol idx
STIM_PULSE_BYTES_LEN = 29


# Stim Checks
class StimulatorCircuitStatuses(IntEnum):
    CALCULATING = -1
    MEDIA = 0
    OPEN = 1
    SHORT = 2
    ERROR = 3


class StimProtocolStatuses(IntEnum):
    ACTIVE = 0
    NULL = 1
    FINISHED = 2
    ERROR = 3


# Metadata
SERIAL_COMM_METADATA_BYTES_LENGTH = 96
SERIAL_COMM_NICKNAME_BYTES_LENGTH = 13
SERIAL_COMM_SERIAL_NUMBER_BYTES_LENGTH = 12


# Mappings

# fmt: off
SERIAL_COMM_WELL_IDX_TO_MODULE_ID: immutabledict[int, int] = immutabledict(
    {
        well_idx: module_id
        for well_idx, module_id in enumerate(
            [
                3, 2, 1, 0,  # A1 - D1
                7, 6, 5, 4,  # A2 - D2
                11, 10, 9, 8,  # A3 - D3
                15, 14, 13, 12,  # A4 - D4
                19, 18, 17, 16,  # A5 - D5
                23, 22, 21, 20   # A6 - D6
            ]
        )
    }
)
# fmt: on
SERIAL_COMM_MODULE_ID_TO_WELL_IDX: immutabledict[int, int] = immutabledict(
    {module_id: well_idx for well_idx, module_id in SERIAL_COMM_WELL_IDX_TO_MODULE_ID.items()}
)

# fmt: off
STIM_MODULE_ID_TO_WELL_IDX: immutabledict[int, int] = immutabledict(
    {
        module_id: well_idx
        for module_id, well_idx in enumerate(
            [
                3, 7, 11, 15, 19, 23,  # D wells
                2, 6, 10, 14, 18, 22,  # C wells
                1, 5, 9, 13, 17, 21,   # B wells
                0, 4, 8, 12, 16, 20    # A wells
            ],
        )
    }
)
# fmt: on
STIM_WELL_IDX_TO_MODULE_ID: immutabledict[int, int] = immutabledict(
    {well_idx: module_id for module_id, well_idx in STIM_MODULE_ID_TO_WELL_IDX.items()}
)
