// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files
import { SYSTEM_STATUS, ERROR_MESSAGES } from "./enums";

export default {
  setStatusUuid(state, newId) {
    if (state.statusUuid !== SYSTEM_STATUS.ERROR_STATE) {
      state.statusUuid = newId;
    }
  },
  setSimulationStatus(state, newId) {
    state.simulationMode = newId;
  },
  setSocket(state, socket) {
    state.socket = socket;
  },
  setIsConnectedToController(state, newStatus) {
    state.isConnectedToController = newStatus;
  },
  setBarcodeManualMode(state, newValue) {
    state.barcodeManualMode = newValue;
  },
  setBarcode(state, { type, newValue, isValid }) {
    state.barcodes[type].value = newValue;
    state.barcodes[type].valid = isValid;
  },
  setShutdownStatus(state, bool) {
    state.shutdownStatus = bool;
  },
  setBarcodeWarning(state, bool) {
    state.barcodeWarning = bool;
  },
  setSystemErrorCode(state, msg) {
    state.systemErrorCode = msg.error_code;

    if (msg.latest_compatible_sw_version) {
      state.systemErrorMessage = "Please download the installer for the correct version here:";
      state.installerLink = `https://downloads.curibio.com/software/StingrayController-Setup-prod-${msg.latest_compatible_sw_version}.exe`;
    } else if (state.statusUuid === SYSTEM_STATUS.UPDATE_ERROR_STATE) {
      state.systemErrorMessage = "Error during firmware update.";
    } else {
      state.systemErrorMessage =
        ERROR_MESSAGES[msg.error_code] || "Stingray Controller is about to shutdown.";
    }
  },
  setSystemErrorMessage(state, msg) {
    // used for testing
    state.systemErrorMessage = msg;
  },
  setSoftwareUpdateAvailable(state, bool) {
    state.softwareUpdateAvailable = bool;
  },
  setFirmwareUpdateAvailable(state, channelFwUpdate) {
    state.firmwareUpdateAvailable = true;
    state.firmwareUpdateDurMins = channelFwUpdate ? 5 : 1;
  },
  setallowSwUpdateInstall(state, bool) {
    state.allowSwUpdateInstall = bool;
  },
  setConfirmationRequest(state, bool) {
    state.confirmationRequest = bool;
  },
  setLoginAttemptStatus(state, bool) {
    state.loginAttemptStatus = bool;
  },
};
