export const SYSTEM_STATUS = {
  SERVER_INITIALIZING_STATE: "04471bcf-1a00-4a0d-83c8-4160622f9a25",
  SERVER_READY_STATE: "8e24ef4d-2353-4e9d-aa32-4346126e73e3",
  INSTRUMENT_INITIALIZING_STATE: "d2e3d386-b760-4c9a-8b2d-410362ff11c4",
  CHECKING_FOR_UPDATES_STATE: "04fd6f6b-ee9e-4656-aae4-0b9584791f36",
  IDLE_READY_STATE: "009301eb-625c-4dc4-9e92-1a4d0762465f",
  UPDATES_NEEDED_STATE: "d6dcf2a9-b6ea-4d4e-9423-500f91a82a2f",
  DOWNLOADING_UPDATES_STATE: "b623c5fa-af01-46d3-9282-748e19fe374c",
  INSTALLING_UPDATES_STATE: "19c9c2d6-0de4-4334-8cb3-a4c7ab0eab00",
  UPDATES_COMPLETE_STATE: "31f8fbc9-9b41-4191-8598-6462b7490789",
  OFFLINE_STATE: "9cf862e0-805e-4aa5-b345-eef298c11317",
  GOING_OFFLINE_STATE: "74362035-a23f-4cba-9e82-106872cb2b13",
};

export const ERROR_CODES = {
  // 000 - Instrument related
  INSTRUMENT_NOT_FOUND: 1,
  INSTRUMENT_CONNECTION_CREATION: 2,
  INSTRUMENT_CONNECTION_LOST: 3,
  INSTRUMENT_STATUS_CODE: 4,
  INSTRUMENT_FW_INCOMPATIBLE_WITH_SW: 5,
  INCORRECT_INSTRUMENT_TYPE: 6,
  INSTRUMENT_SENT_BAD_DATA: 10,
  INVALID_INSTRUMENT_METADATA: 7,
  INSTRUMENT_INITIATED_DISCONNECTION: 11,
  INSTRUMENT_COMMAND_FAILED: 12,
  INSTRUMENT_COMMAND_ATTEMPT: 13,
  // 100 - Caught in Controller  // These by nature cannot be set by the UI itself, and thus are only here for documentation
  UI_SENT_BAD_DATA: 110,
  FIRMWARE_DOWNLOAD_ERROR: 180,
  UNSPECIFIED_CONTROLLER_ERROR: 199, // Catch all error. This ideally should never happen, but created just in case
  // 200 - Caught in UI
  CONTROLLER_CONNECTION_CREATION: 202,
  CONTROLLER_CONNECTION_LOST: 203,
  CONTROLLER_SENT_BAD_DATA: 210,
  UNSPECIFIED_UI_ERROR: 299, // Catch all error. This ideally should never happen, but created just in case
};

export const ERROR_MESSAGES = {
  [ERROR_CODES.INSTRUMENT_NOT_FOUND]:
    "No instrument was detected, please make sure it is plugged in and powered on",
  [ERROR_CODES.INSTRUMENT_CONNECTION_CREATION]: "Unable to establish a connection to the instrument",
  [ERROR_CODES.INSTRUMENT_CONNECTION_LOST]: "The instrument failed to respond to one or more commands",
  [ERROR_CODES.INSTRUMENT_STATUS_CODE]: "An error occurred on the instrument",
  [ERROR_CODES.INSTRUMENT_SENT_BAD_DATA]: "Malformed data received from the instrument",
  [ERROR_CODES.INCORRECT_INSTRUMENT_TYPE]:
    "Mantarray instrument detected. Please connect to a Stingray and restart the software",
};
