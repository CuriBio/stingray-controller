# -*- coding: utf-8 -*-
"""Exceptions for the Stingray Controller."""


# Server


class LocalServerPortAlreadyInUseError(Exception):
    pass


class WebsocketCommandError(Exception):
    pass


class WebsocketCommandNoOpException(Exception):
    pass


# Instrument related errors


class NoInstrumentDetectedError(Exception):
    pass


class InstrumentError(Exception):
    """Base exception for errors with instrument interaction."""


class IncorrectInstrumentConnectedError(InstrumentError):
    pass


class InstrumentConnectionCreationError(InstrumentError):
    """Base exception for errors caused by connection failures."""


class SerialCommPacketRegistrationTimeoutError(InstrumentConnectionCreationError):
    pass


class SerialCommPacketRegistrationReadEmptyError(InstrumentConnectionCreationError):
    pass


class SerialCommPacketRegistrationSearchExhaustedError(InstrumentConnectionCreationError):
    pass


class InstrumentConnectionLostError(InstrumentError):
    """Base exception for errors caused by response timeouts."""


class SerialCommStatusBeaconTimeoutError(InstrumentConnectionLostError):
    pass


class SerialCommCommandResponseTimeoutError(InstrumentConnectionLostError):
    pass


class FirmwareGoingDormantError(InstrumentError):
    pass


# TODO change this to be an issue processing comm from instrument, rather than explicitly bad data from it
class InstrumentBadDataError(InstrumentError):
    """Base exception for errors caused by malformed data."""


class SerialCommIncorrectMagicWordFromInstrumentError(InstrumentBadDataError):
    pass


class SerialCommIncorrectChecksumFromInstrumentError(InstrumentBadDataError):
    pass


# TODO might need to make this a subclass of a different error (Tanner: not sure why anymore)
class SerialCommCommandProcessingError(InstrumentBadDataError):
    pass


class InstrumentFirmwareError(InstrumentError):
    """Generic exception representing errors in the instrument's firmware."""


class InstrumentInvalidMetadataError(InstrumentError):
    """Generic exception representing errors in the instrument's firmware."""


class InstrumentRebootTimeoutError(InstrumentFirmwareError):
    pass


class FirmwareUpdateTimeoutError(InstrumentFirmwareError):
    pass


class InstrumentCommandResponseError(InstrumentError):
    """Base exception for errors resulting from command responses from the instrument"""


class SerialCommUntrackedCommandResponseError(InstrumentCommandResponseError):
    pass


class InstrumentCommandAttemptError(InstrumentError):
    """Base exception for errors resulting from attempting to send a command to the instrument incorrectly"""


class SerialCommIncorrectChecksumFromPCError(InstrumentCommandAttemptError):
    pass


class FirmwareAndSoftwareNotCompatibleError(InstrumentError):
    pass


# Cloud


class CloudAuthFailedError(Exception):
    """Base exception for cloud auth related errors."""


class LoginFailedError(CloudAuthFailedError):
    pass


class RefreshFailedError(CloudAuthFailedError):
    pass


class RequestFailedError(Exception):
    pass


class FirmwareDownloadError(Exception):
    pass


# class CloudAnalysisJobFailedError(Exception):
#     pass
