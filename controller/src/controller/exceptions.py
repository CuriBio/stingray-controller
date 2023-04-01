# -*- coding: utf-8 -*-
"""Exceptions for the Stingray Controller."""


# Server


class LocalServerPortAlreadyInUseError(Exception):
    pass


class WebsocketCommandError(Exception):
    pass


# Instrument related errors


class NoInstrumentDetectedError(Exception):
    pass


class InstrumentError(Exception):
    """Generic exception for errors with instrument interaction."""


class InstrumentConnectionCreationError(InstrumentError):
    """Generic exception for errors caused by connection failures."""


class SerialCommPacketRegistrationTimeoutError(InstrumentConnectionCreationError):
    pass


class SerialCommPacketRegistrationReadEmptyError(InstrumentConnectionCreationError):
    pass


class SerialCommPacketRegistrationSearchExhaustedError(InstrumentConnectionCreationError):
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


# TODO might need to make this a subclass of a different error (Tanner: not sure why anymore)
class SerialCommCommandProcessingError(InstrumentBadDataError):
    pass


class InstrumentFirmwareError(InstrumentError):
    """Generic exception representing errors in the instrument's firmware."""


# Misc Instrument comm related errors
class SerialCommIncorrectChecksumFromPCError(Exception):
    pass


class SerialCommUntrackedCommandResponseError(Exception):
    pass


class InstrumentRebootTimeoutError(Exception):
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


# TODO add this in
class FirmwareDownloadError(Exception):
    pass


class FirmwareAndSoftwareNotCompatibleError(Exception):
    pass


class FirmwareGoingDormantError(Exception):
    pass


# Cloud
# TODO remove any of these below if they become unnecessary


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
