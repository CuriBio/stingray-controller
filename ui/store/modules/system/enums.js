export const STATUS = {
  SERVER_INITIALIZING_STATE: "04471bcf-1a00-4a0d-83c8-4160622f9a25",
  SERVER_READY_STATE: "8e24ef4d-2353-4e9d-aa32-4346126e73e3",
  INSTRUMENT_INITIALIZING_STATE: "d2e3d386-b760-4c9a-8b2d-410362ff11c4",
  CHECKING_FOR_UPDATES_STATE: "04fd6f6b-ee9e-4656-aae4-0b9584791f36",
  IDLE_READY_STATE: "009301eb-625c-4dc4-9e92-1a4d0762465f",
  UPDATES_NEEDED_STATE: "d6dcf2a9-b6ea-4d4e-9423-500f91a82a2f",
  DOWNLOADING_UPDATES_STATE: "b623c5fa-af01-46d3-9282-748e19fe374c",
  INSTALLING_UPDATES_STATE: "19c9c2d6-0de4-4334-8cb3-a4c7ab0eab00",
  UPDATES_COMPLETE_STATE: "31f8fbc9-9b41-4191-8598-6462b7490789",
  UPDATE_ERROR_STATE: "33742bfc-d354-4ae5-88b6-2b3cee23aff8",
};

export const ERRORS = {
  InstrumentCreateConnectionError: "Unable to establish a connection to the instrument",
  InstrumentConnectionLostError: "The instrument failed to respond to one or more commands",
  InstrumentBadDataError: "Malformed data received from the instrument",
  InstrumentFirmwareError: "An error occurred in the instrument's firmware",
  FirmwareAndSoftwareNotCompatibleError:
    "The instrument's firmware is not compatible with this version of the Stingray Controller",
};
