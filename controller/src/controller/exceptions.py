# -*- coding: utf-8 -*-
"""Exceptions for the Stingray Controller."""
from typing import Union


# TODO clean up this file


class MultiprocessingNotSetToSpawnError(Exception):
    def __init__(self, start_method: Union[str, None]):
        super().__init__(
            f"The multiprocessing start type has not been set to spawn, which is the only option on Windows. It is current set as '{start_method}'"
        )


class InvalidCommandFromMainError(Exception):
    pass


class UnrecognizedDebugConsoleCommandError(Exception):
    pass


class UnableToUploadLogFilesToS3(Exception):
    pass


class UnrecognizedCommandFromServerToMainError(Exception):
    pass


class UnrecognizedCommandFromMainToFileWriterError(Exception):
    pass


class UnrecognizedCommandFromMainToMcCommError(Exception):
    pass


class UnrecognizedCommandFromMainToDataAnalyzerError(Exception):
    pass


class LocalServerPortAlreadyInUseError(Exception):
    pass


class SystemStartUpError(Exception):
    pass


class InvalidBeta2FlagOptionError(Exception):
    pass


class UnrecognizedNamingCommandError(Exception):
    pass


class UnrecognizedRecordingCommandError(Exception):
    pass


class UnrecognizedSimulatorTestCommandError(Exception):
    pass


class RecordingFolderDoesNotExistError(Exception):
    pass


class InvalidStopRecordingTimepointError(Exception):
    pass


class CalibrationFilesMissingError(Exception):
    pass


class RecordingUploadMissingPulse3dVersionError(Exception):
    pass


class StartManagedAcquisitionWithoutBarcodeError(Exception):
    pass


# Instrument related errors
class InstrumentError(Exception):
    """Generic exception for errors with instrument interaction."""


class InstrumentCreateConnectionError(InstrumentError):
    """Generic exception for errors caused by connection failures."""


class SerialCommPacketRegistrationTimeoutError(InstrumentCreateConnectionError):
    pass


class SerialCommPacketRegistrationReadEmptyError(InstrumentCreateConnectionError):
    pass


class SerialCommPacketRegistrationSearchExhaustedError(InstrumentCreateConnectionError):
    pass


class InstrumentConnectionLostError(InstrumentError):
    """Generic exception for errors caused by response timeouts."""


class SerialCommStatusBeaconTimeoutError(InstrumentConnectionLostError):
    pass


class SerialCommCommandResponseTimeoutError(InstrumentConnectionLostError):
    pass


class InstrumentBadDataError(InstrumentError):
    """Generic exception for errors caused by malformed data."""


class SerialCommIncorrectMagicWordFromInstrumentError(InstrumentBadDataError):
    pass


class SerialCommIncorrectChecksumFromInstrumentError(InstrumentBadDataError):
    pass


# TODO might need to make this a subclass of a different error
class SerialCommCommandProcessingError(InstrumentBadDataError):
    pass


class InstrumentFirmwareError(InstrumentError):
    """Generic exception representing errors in the instrument's firmware."""


# Misc Instrument comm related errors
class UnrecognizedSerialCommPacketTypeError(Exception):
    pass


class SerialCommIncorrectChecksumFromPCError(Exception):
    pass


class SerialCommMetadataValueTooLargeError(Exception):
    pass


class SerialCommTooManyMissedHandshakesError(Exception):
    pass


class SerialCommUntrackedCommandResponseError(Exception):
    pass


class SerialCommInvalidSamplingPeriodError(Exception):
    pass


class SamplingPeriodUpdateWhileDataStreamingError(Exception):
    pass


class InstrumentRebootTimeoutError(Exception):
    pass


class InstrumentDataStreamingAlreadyStartedError(Exception):
    pass


class InstrumentDataStreamingAlreadyStoppedError(Exception):
    pass


class StimulationProtocolUpdateWhileStimulatingError(Exception):
    pass


class StimulationProtocolUpdateFailedError(Exception):
    pass


class StimulationStatusUpdateFailedError(Exception):
    pass


class FirmwareUpdateCommandFailedError(Exception):
    pass


class FirmwareUpdateTimeoutError(Exception):
    pass


class FirmwareDownloadError(Exception):
    pass


class FirmwareAndSoftwareNotCompatibleError(Exception):
    pass


class FirmwareGoingDormantError(Exception):
    pass


# Cloud
class PresignedUploadFailedError(Exception):
    pass


class CloudAnalysisJobFailedError(Exception):
    pass


class CloudAuthFailedError(Exception):
    """Base class for cloud auth related errors."""

    def __init__(self, status_code: int):
        super().__init__(f"Status Code: {status_code}")


class LoginFailedError(CloudAuthFailedError):
    pass


class RefreshFailedError(CloudAuthFailedError):
    pass
