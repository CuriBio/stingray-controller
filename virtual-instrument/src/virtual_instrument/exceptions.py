# -*- coding: utf-8 -*-


class SerialCommInvalidSamplingPeriodError(Exception):
    pass


class SerialCommTooManyMissedHandshakesError(Exception):
    pass


class UnrecognizedSerialCommPacketTypeError(Exception):
    pass
